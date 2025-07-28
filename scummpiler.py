import os, sys, re, json, time, math
from timestamp_manager import *
import script_codec, box_codec, scale_codec, palette_codec

tools_path = os.path.join(sys.argv[0].replace("scummpiler.py", ""), "Tools", "JestarJokin")
scummpacker_py2_path = os.path.join(tools_path, "scummpacker_py2", "src", "scummpacker.py")

supported_games = ["MI1EGA", "MI1VGA", "MI1CD", "MI2"]
version_table = {
    "MI1EGA": "4",
    "MI1VGA": "4",
    "MI1CD": "5",
    "MI2": "5"
}

def identify_file_status(file_name):
    if file_name.endswith(".dmp"):
        return "binary"
    elif file_name.endswith(".xml"):
        return "xml"
    elif file_name.endswith(".txt") or file_name.endswith(".json") or file_name.endswith(".png"):
        return "decoded"
    else:
        return "other"

def identify_file_type_v4(file_name):
    if "SC" in file_name or "LS" in file_name or "EN" in file_name or "EX" in file_name or "OC" in file_name:
        return "script"
    elif "BX" in file_name:
        return "box"
    elif "SA" in file_name:
        return "scale"
    elif "PA" in file_name:
        return "palette"
    else:
        return "other"

def identify_file_type_v5(file_name):
    if "SCRP" in file_name or "LSCR" in file_name or "ENCD" in file_name or "EXCD" in file_name or "VERB" in file_name:
        return "script"
    elif "BOXD" in file_name or "BOXM" in file_name:
        return "box"
    elif "SCAL" in file_name:
        return "scale"
    elif "CLUT" in file_name:
        return "palette"
    else:
        return "other"

class FileCrawler:
    version = 5
    file_types_to_decode = []
    timestamp_manager = {}

    def __init__(self, version, file_types_to_decode, timestamp_manager):
        self.version = version
        self.file_types_to_decode = file_types_to_decode
        self.timestamp_manager = timestamp_manager

    def process_file(self, file_path, file_name):
        file_status = identify_file_status(file_name)

        if file_status == "xml":
            self.timestamp_manager.add_timestamp(file_path)
        
        if file_status != "binary":
            return
        
        file_type = ""
        if self.version == '4':
            file_type = identify_file_type_v4(file_name)
        elif self.version == '5':
            file_type = identify_file_type_v5(file_name)

        if file_type in self.file_types_to_decode:
            if file_type == "script":
                script_codec.decode(file_path, self.version, self.timestamp_manager)
            elif file_type == "box":
                box_codec.decode(file_path, self.version, self.timestamp_manager)
            elif file_type == "scale":
                scale_codec.decode(file_path, self.version, self.timestamp_manager)
            elif file_type == "palette":
                palette_codec.decode(file_path, self.version, self.timestamp_manager)
    
    def crawl_folder(self, folder_path):
        folder_contents = os.scandir(folder_path)

        for entry in folder_contents:
            if entry.is_dir():
                self.crawl_folder(entry.path)
            elif entry.is_file():
                self.process_file(entry.path, entry.name)


def add_room_names(decomp_path, game_id):
    room_root_paths = []

    if game_id == "MI1CD":
        room_root_paths = [os.path.join("MONKEY1", "LECF")]
    elif game_id == "MI2":
        room_root_paths = [os.path.join("MONKEY2", "LECF")]
    elif game_id == "MI1EGA" or game_id == "MI1VGA":
        room_root_paths = [
            os.path.join("DISK01", "LE"),
            os.path.join("DISK02", "LE"),
            os.path.join("DISK03", "LE"),
            os.path.join("DISK04", "LE")
        ]
    
    room_names_file_path = os.path.join(decomp_path, "roomnames.xml")
    room_names_file = open(room_names_file_path, "r")
    room_names_xml = room_names_file.read()
    room_names_file.close()

    room_names = re.findall("<name>(.*)</name>", room_names_xml.replace("-", "_"))
    room_ids = re.findall("<id>(.*)</id>", room_names_xml)

    room_name_table = {}

    for i in range(0, len(room_ids)):
        room_name_table[int(room_ids[i])] = room_names[i].replace("-", "_")

    for local_room_root_path in room_root_paths:
        room_root_path = os.path.join(decomp_path, local_room_root_path)

        if not os.path.isdir(room_root_path):
            continue
        
        room_paths = [f.path for f in os.scandir(room_root_path) if f.is_dir()]
        for room_path in room_paths:
            room_num = int(room_path[-3:])
            new_room_path = room_path + "_" + room_name_table[room_num]
            
            os.rename(room_path, new_room_path)


def decompile(game_path, decomp_path, game_id, flags):
    game_id = game_id.upper()

    assert game_id in supported_games

    version = version_table[game_id]

    start_time = time.time()

    if not "skip_unpack" in flags:
        os.system(f'python2 {scummpacker_py2_path} -g {game_id} -i "{game_path}" -o {decomp_path} -u')
        add_room_names(decomp_path, game_id)

    file_types_to_decode = ["script", "box", "scale", "palette"]
    #file_types_to_decode = ["scale"]

    timestamp_manager = TimestampManager(decomp_path)

    file_crawler = FileCrawler(version, file_types_to_decode, timestamp_manager)
    file_crawler.crawl_folder(decomp_path)

    timestamp_manager.save_to_timestamp_file()

    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"{game_id} successfully decompiled in {math.floor(total_time)} seconds")


def build(decomp_path, game_path, game_id, flags):
    game_id = game_id.upper()
    assert game_id in supported_games

    version = version_table[game_id]

    start_time = time.time()

    timestamp_manager = TimestampManager(decomp_path)



if __name__ == "__main__":
    decompile(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])


