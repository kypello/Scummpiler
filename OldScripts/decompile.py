import os, sys, re, descumm
from PIL import Image

tools_path = os.path.join(sys.argv[0].replace("decompile.py", ""), "Tools", "JestarJokin")
scummpacker_py2_path = os.path.join(tools_path, "scummpacker_py2", "src", "scummpacker.py")
scummpacker_exe_path = os.path.join(tools_path, "scummpacker_exe", "scummpacker.exe")

def decompile(game_path, decompiled_path, game_id):
    game_id = game_id.upper()
    print("Decompiling " + game_path)

    windows_mode = os.name == "nt"
    
    if windows_mode:
        os.system(scummpacker_exe_path + ' -g ' + game_id + ' -i "' + game_path + '" -o ' + decompiled_path + ' -u')
    else:
        os.system('python2 ' + scummpacker_py2_path + ' -g ' + game_id + ' -i "' + game_path + '" -o ' + decompiled_path + ' -u')

    room_root_paths = []

    if game_id == "MI1CD":
        room_root_paths.append(os.path.join("MONKEY1", "LECF"))
    elif game_id == "MI2":
        room_root_paths.append(os.path.join("MONKEY2", "LECF"))
    elif game_id == "MI1EGA" or game_id == "MI1VGA":
        room_root_paths.append(os.path.join("DISK01", "LE"))
        room_root_paths.append(os.path.join("DISK02", "LE"))
        room_root_paths.append(os.path.join("DISK03", "LE"))
        room_root_paths.append(os.path.join("DISK04", "LE"))
    else:
        print("Error: game ID " + game_id + " not recognised")
        exit()

    room_names_file = open(os.path.join(decompiled_path, "roomnames.xml"), "r")
    room_names_text = room_names_file.read()
    room_names_file.close()

    room_names = re.findall("<name>(.*)</name>", room_names_text.replace("-", "_"))
    room_ids = re.findall("<id>(.*)</id>", room_names_text)

    for room_root_path in room_root_paths:
        rooms = [f.path for f in os.scandir(os.path.join(decompiled_path, room_root_path)) if f.is_dir()]
        for room in rooms:
            new_room_name = ""
            room_num = int(room[-3:])
            
            for i in range(0, len(room_ids)):
                if int(room_ids[i]) == room_num:
                    new_room_name = room + "_" + room_names[i]
                    break
            
            os.rename(room, new_room_name)
    
    for room_root_path in room_root_paths:
        rooms = [f.path for f in os.scandir(os.path.join(decompiled_path, room_root_path)) if f.is_dir()]
        for room in rooms:
            if game_id == "MI1CD" or game_id == "MI2":
                descumm.descumm(room, "5", sys.argv)
            elif game_id == "MI1EGA" or game_id == "MI1VGA":
                descumm.descumm(room, "4", sys.argv)
    
    print(game_id + " successfully decompiled!!")

            

if __name__ == "__main__":
    decompile(sys.argv[1], sys.argv[2], sys.argv[3])