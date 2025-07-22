import os, sys, rescumm

tools_path = tools_path = os.path.join(sys.argv[0].replace("recompile.py", "").replace("insert_speech.py", ""), "Tools", "JestarJokin")
scummpacker_py2_path = os.path.join(tools_path, "scummpacker_py2", "src", "scummpacker.py")
scummpacker_exe_path = os.path.join(tools_path, "scummpacker_exe", "scummpacker.exe")

def recompile(decompiled_path, recompiled_path, game_id, force_recompile):
    game_id = game_id.upper()
    print("Recompiling " + game_id)

    windows_mode = os.name == "nt"
    
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
    
    recompile_needed = False

    for room_root_path in room_root_paths:
        rooms = [f.path for f in os.scandir(os.path.join(decompiled_path, room_root_path)) if f.is_dir()]
        for room in rooms:
            room_rescummed = False
            if game_id == "MI1CD" or game_id == "MI2":
                room_rescummed = rescumm.rescumm(room, "5")
            elif game_id == "MI1EGA" or game_id == "MI1VGA":
                room_rescummed = rescumm.rescumm(room, "4")
            
            if room_rescummed:
                recompile_needed = True

    if recompile_needed or not os.path.exists(recompiled_path) or force_recompile:
        if windows_mode:
            os.system(scummpacker_exe_path + " -g " + game_id + " -i " + decompiled_path + " -o " + recompiled_path +" -p")
        else:
            os.system("python2 " + scummpacker_py2_path + " -g " + game_id + " -i " + decompiled_path + " -o " + recompiled_path +" -p")
    else:
        print("Nothing to recompile")


if __name__ == "__main__":
    recompile(sys.argv[1], sys.argv[2], sys.argv[3], (len(sys.argv) == 5 and sys.argv[4] == "force"))