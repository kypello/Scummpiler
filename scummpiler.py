import os, sys, re, json, time, math
from timestamp_manager import *
from pathlib import Path
import script_codec, box_codec, scale_codec, palette_codec, image_codec, costume_codec

python_scripts_path = Path(__file__).resolve().parent
tools_path = Path(python_scripts_path, "Tools", "JestarJokin")

scummpacker_py2_path = Path(tools_path, "scummpacker_py2", "src", "scummpacker.py")
scummpacker_exe_path = Path(tools_path, "scummpacker_exe", "scummpacker.exe")

supported_games = ['MI1EGA', 'MI1VGA', 'MI1CD', 'MI2']
version_table = {
    'MI1EGA': '4',
    'MI1VGA': '4',
    'MI1CD': '5',
    'MI2': '5'
}

video_table = {
    'MI1EGA': 'ega',
    'MI1VGA': 'vga',
    'MI1CD': 'vga',
    'MI2': 'vga'
}

def identify_file_status(file_name):
    if file_name == "timestamps.json":
        return "meta"
    elif file_name.endswith(".dmp"):
        return "binary"
    elif file_name.endswith(".xml"):
        return "xml"
    elif file_name.endswith(".txt") or file_name.endswith(".json") or file_name.endswith(".png"):
        return "decoded"
    else:
        return "other"

def identify_file_type_v4(file_name):
    if "SC_" in file_name or "LS_" in file_name or "EN" in file_name or "EX" in file_name or "OC" in file_name:
        return "script"
    elif "BX." in file_name:
        return "box"
    elif "SA." in file_name:
        return "scale"
    elif "PA." in file_name:
        return "palette"
    elif "_zplane." in file_name:
        return "zplane"
    elif "BM." in file_name or "OI." in file_name or "_image." in file_name:
        return "image"
    elif "CO_" in file_name:
        return "costume"
    else:
        return "other"

def identify_file_type_v5(file_name):
    if "SCRP_" in file_name or "LSCR_" in file_name or "ENCD" in file_name or "EXCD" in file_name or "VERB" in file_name:
        return "script"
    elif "BOXD." in file_name or "BOXM." in file_name:
        return "box"
    elif "SCAL." in file_name:
        return "scale"
    elif "CLUT." in file_name:
        return "palette"
    elif "SMAP." in file_name:
        return "image"
    elif "ZP" in file_name:
        return "zplane"
    elif "COST_" in file_name:
        return "costume"
    else:
        return "other"

def identify_folder_type_v4(folder_name):
    if "LF_" in folder_name:
        return "lfl"
    elif "CO_" in folder_name:
        return "costume"
    else:
        return "other"

def identify_folder_type_v5(folder_name):
    if "LFLF_" in folder_name:
        return "lfl"
    elif "COST_" in folder_name:
        return "costume"
    else:
        return "other"

class FileCrawler:
    version = 5
    video_type = 'vga'
    file_types_to_target = []
    timestamp_manager = {}

    room_palette = []
    room_palette_found = False
    palette_dependent_queue = []

    def __init__(self, version, video_type, file_types_to_target, timestamp_manager):
        self.version = version
        self.video_type = video_type
        self.file_types_to_target = file_types_to_target
        self.timestamp_manager = timestamp_manager
    
    def crawl_folder(self, folder_path):
        folder_type = ""
        if self.version == '4':
            folder_type = identify_folder_type_v4(folder_path.name)
        elif self.version == '5':
            folder_type = identify_folder_type_v5(folder_path.name)

        if folder_type == "costume":
            self.process_folder(folder_path, folder_type)
            return

        for entry in folder_path.iterdir():
            if entry.is_dir():
                self.crawl_folder(entry)
            elif entry.is_file():
                self.process_file(entry)
        
        if folder_type == "lfl":
            for queued_file in self.palette_dependent_queue:
                self.process_file(queued_file)
            
            self.palette_dependent_queue = []
            self.room_palette_found = False

    
class FileCrawlerDecomp(FileCrawler):
    def __init__(self, version, video_type, file_types_to_target, timestamp_manager):
        super().__init__(version, video_type, file_types_to_target, timestamp_manager)

    def process_file(self, file_path):
        file_status = identify_file_status(file_path.name)

        if file_status == "xml":
            self.timestamp_manager.add_timestamp(file_path)
        
        if file_status != "binary":
            return
        
        file_type = ""
        if self.version == '4':
            file_type = identify_file_type_v4(file_path.name)
        elif self.version == '5':
            file_type = identify_file_type_v5(file_path.name)

        if file_type == "palette":
            targeting_palette_files = "palette" in self.file_types_to_target

            self.room_palette = palette_codec.decode(file_path, self.version, self.timestamp_manager, targeting_palette_files)
            self.room_palette_found = True
            return

        if file_type in self.file_types_to_target:
            if file_type == "script":
                script_codec.decode(file_path, self.version, self.timestamp_manager)
            elif file_type == "box":
                box_codec.decode(file_path, self.version, self.timestamp_manager)
            elif file_type == "scale":
                scale_codec.decode(file_path, self.version, self.timestamp_manager)
            elif file_type == "image":
                if self.video_type == 'vga' and not self.room_palette_found:
                    self.palette_dependent_queue.append(file_path)
                else:
                    image_codec.decode(file_path, self.version, self.timestamp_manager, self.video_type, self.room_palette)
            elif file_type == "costume":
                if self.video_type == 'vga' and not self.room_palette_found:
                    self.palette_dependent_queue.append(file_path)
                else:
                    costume_codec.decode(file_path, self.version, self.timestamp_manager, self.video_type, self.room_palette)
            elif file_type == "zplane":
                image_codec.decode(file_path, self.version, self.timestamp_manager, 'zplane')

    def process_folder(self, folder_path, folder_type):
        return

    


class FileCrawlerBuild(FileCrawler):
    def __init__(self, version, video_type, file_types_to_target, timestamp_manager):
        super().__init__(version, video_type, file_types_to_target, timestamp_manager)
    
    def process_file(self, file_path):
        file_status = identify_file_status(file_path.name)

        if file_status == "xml":
            self.timestamp_manager.touch_timestamp(file_path)
        

        file_type = ""
        if self.version == '4':
            file_type = identify_file_type_v4(file_path.name)
        elif self.version == '5':
            file_type = identify_file_type_v5(file_path.name)
        
        if file_type == "palette":
            if file_status == "decoded":
                targeting_palette_files = "palette" in self.file_types_to_target
                should_save_to_file = targeting_palette_files and self.timestamp_manager.check_timestamp(file_path)

                self.room_palette = palette_codec.encode(file_path, self.version, self.timestamp_manager, should_save_to_file)
                self.room_palette_found = True
            
            elif file_status == "binary":
                decoded_palette_path = Path(file_path.parent, file_path.name.replace(".dmp", ".png"))

                if (not self.room_palette_found) and (not decoded_palette_path.is_file()):
                    self.room_palette = palette_codec.decode(file_path, self.version, self.timestamp_manager, False)
                    self.room_palette_found = True
            
            return

        if file_status != "decoded":
            return

        if file_type in self.file_types_to_target and self.timestamp_manager.check_timestamp(file_path):
            if file_type == "script":
                script_codec.encode(file_path, self.version, self.timestamp_manager)
            elif file_type == "box":
                box_codec.encode(file_path, self.version, self.timestamp_manager)
            elif file_type == "scale":
                scale_codec.encode(file_path, self.version, self.timestamp_manager)
            elif file_type == "image":
                if self.video_type == 'vga' and not self.room_palette_found:
                    self.palette_dependent_queue.append(file_path)
                else:
                    image_codec.encode(file_path, self.version, self.timestamp_manager, self.video_type, self.room_palette)
            elif file_type == 'zplane':
                if self.version == '4' and self.video_type == 'vga' and not self.room_palette_found:
                    self.palette_dependent_queue.append(file_path)
                else:
                    image_codec.encode(file_path, self.version, self.timestamp_manager, 'zplane', self.room_palette)
            elif file_type == 'costume':
                if self.video_type == 'vga' and not self.room_palette_found:
                    self.palette_dependent_queue.append(file_path)
                else:
                    costume_codec.encode(file_path, self.version, self.timestamp_manager, self.video_type, self.room_palette)



    def process_folder(self, folder_path, folder_type):
        return

def add_room_names(decomp_path, game_id):
    room_root_paths = []

    if game_id == "MI1CD":
        room_root_paths = [Path("MONKEY1", "LECF")]
    elif game_id == "MI2":
        room_root_paths = [Path("MONKEY2", "LECF")]
    elif game_id == "MI1EGA" or game_id == "MI1VGA":
        room_root_paths = [
            Path("DISK01", "LE"),
            Path("DISK02", "LE"),
            Path("DISK03", "LE"),
            Path("DISK04", "LE")
        ]
    
    room_names_file_path = Path(decomp_path, "roomnames.xml")
    room_names_file = open(room_names_file_path, "r")
    room_names_xml = room_names_file.read()
    room_names_file.close()

    room_names = re.findall("<name>(.*)</name>", room_names_xml)
    room_ids = re.findall("<id>(.*)</id>", room_names_xml)

    room_name_table = {}

    for i in range(0, len(room_ids)):
        room_name_table[int(room_ids[i])] = room_names[i].replace("-", "_")

    for local_room_root_path in room_root_paths:
        room_root_path = Path(decomp_path, local_room_root_path)

        if not room_root_path.is_dir():
            continue
        
        for room_path in room_root_path.iterdir():
            if not room_path.is_dir():
                continue
            
            room_num = int(room_path.name[-3:])
            new_room_path = Path(room_path.parent, room_path.name + "_" + room_name_table[room_num])

            os.rename(room_path, new_room_path)


def decompile(game_path, decomp_path, game_id, flags):
    game_id = game_id.upper()

    assert game_id in supported_games

    version = version_table[game_id]
    video_type = video_table[game_id]

    start_time = time.time()

    game_path = Path(game_path).resolve()
    decomp_path = Path(decomp_path).resolve()

    if not "skip_unpack" in flags:
        if os.name == 'posix':
            os.system(f'python2 {scummpacker_py2_path} -g {game_id} -i "{game_path}" -o {decomp_path} -u')
        elif os.name == 'nt':
            os.system(f'{scummpacker_exe_path} -g {game_id} -i "{game_path}" -o {decomp_path} -u')

        add_room_names(decomp_path, game_id)

    #file_types_to_decode = ["costume", "script", "image", "scale", "box", "palette", "zplane"]
    file_types_to_decode = ["box"]

    timestamp_manager = TimestampManager(decomp_path)

    timestamp_manager.check_for_existing_timestamps()

    file_crawler = FileCrawlerDecomp(version, video_type, file_types_to_decode, timestamp_manager)
    file_crawler.crawl_folder(decomp_path)

    timestamp_manager.save_to_timestamp_file()

    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"{game_id} successfully decompiled in {math.floor(total_time)} seconds")


def build(decomp_path, game_path, game_id, flags):
    game_id = game_id.upper()
    assert game_id in supported_games

    version = version_table[game_id]
    video_type = video_table[game_id]

    start_time = time.time()

    decomp_path = Path(decomp_path).resolve()
    game_path = Path(game_path).resolve()
    
    file_types_to_encode = ["costume", "script", "image", "scale", "box", "palette", "zplane"]

    timestamp_manager = TimestampManager(decomp_path)
    timestamp_manager.check_for_existing_timestamps()

    file_crawler = FileCrawlerBuild(version, video_type, file_types_to_encode, timestamp_manager)
    file_crawler.crawl_folder(decomp_path)

    if not timestamp_manager.changes_found:
        print("Nothing to rebuild")
        return
    
    if os.name == 'posix':
        os.system(f'python2 {scummpacker_py2_path} -g {game_id} -i "{decomp_path}" -o {game_path} -p')
    elif os.name == 'nt':
        os.system(f'{scummpacker_exe_path} -g {game_id} -i "{decomp_path}" -o {game_path} -p')

    timestamp_manager.save_to_timestamp_file()

    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"{game_id} successfully built in {math.floor(total_time)} seconds")


if __name__ == "__main__":
    if sys.argv[1] == "decompile":
        decompile(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])

    elif sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])


