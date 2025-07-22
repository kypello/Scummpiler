import os, sys, json, shutil, re, recompile

projects_path = os.path.expanduser("~/Games/ScummDecompiled/MI1TokiPona/")
extract_folder = projects_path + "LineExtracts"
timestamp_table_path = projects_path + "extract_modify_timestamps.json"
games_path = os.path.expanduser("~/Games/Scumm/")

def generate_timestamps(): 
    timestamp_table = {}

    for file_name in os.listdir(extract_folder):
        timestamp = os.path.getmtime(extract_folder + "/" + file_name)

        version_timestamp_table = {}
        version_timestamp_table["VGA"] = 0
        version_timestamp_table["EGA"] = 0

        timestamp_table[file_name] = version_timestamp_table
    
    timestamp_table_file = open(timestamp_table_path, "w")
    timestamp_table_file.write(json.dumps(timestamp_table, indent = 4))
    timestamp_table_file.close()

def clone_to_working_directory(room_name):
    #os.rmdir(working_path + room_name)
    shutil.rmtree(working_path + room_name)
    shutil.copytree(descumm_path + room_name, working_path + room_name)

    #for subdir, dirs, files in os.walk(descumm_path + room_name): #for every file basically
    #    for file_name in files:
    #        file_path = subdir + os.sep + file_name

    #        shutil.copyfile(file_path, file_path.replace("Descummed", "Working"))

def convert_to_scumm_format(json_line):
    json_line = json_line.replace("\\<", "[OPENING ANGLE BRACKET]").replace("\\>", "[CLOSING ANGLE BRACKET]")
    segments = re.split(r'<|>', json_line)

    while "" in segments:
        segments.remove("")

    formatted_line = ""

    last_segment_index = 0

    for i in range(len(segments)):
        if i != 0:
            formatted_line += " + "
        
        segment_index = json_line[last_segment_index:].index(segments[i]) + last_segment_index
        last_segment_index = segment_index

        if segments[i] == " " or segment_index == 0 or json_line[segment_index-1] == '>':
            formatted_line += '"' + segments[i] + '"'
        else:
            formatted_line += segments[i]
    
    formatted_line = formatted_line.replace("[OPENING ANGLE BRACKET]", "<").replace("[CLOSING ANGLE BRACKET]", ">")
    return formatted_line

def check_style(text_table):
    for key in text_table:
        if text_table[key] == key:
            continue
        
        if re.search("[.?!] [^ ]", text_table[key]):
            print("Spacing style violated: " + text_table[key])

def replace_text(room_path, text_table):
    for subdir, dirs, files in os.walk(room_path): #for every file basically
        for file_name in files:
            if (file_name.endswith(".txt") and not file_name[:3] == "EN_") or file_name == "OBHD.xml":
                file_path = subdir + os.sep + file_name
                english_file_path = subdir + os.sep + "EN_" + file_name

                english_version_exists = os.path.exists(english_file_path)

                file = 0
                if english_version_exists:
                    file = open(english_file_path, "r")
                else:
                    file = open(file_path, "r")

                script_text = file.read()
                english_script_text = script_text
                file.close()

                if file_name == "OC.txt":
                    object_name = re.search('name "(.*)"', script_text).group(1)

                    if object_name != "" and object_name != text_table[object_name]:
                        script_text = script_text.replace('name "' + object_name + '"', 'name "' + text_table[object_name] + '"')

                if file_name.endswith(".txt"):
                    for key in text_table:
                        if text_table[key] == key:
                            continue
                        
                        og_line = convert_to_scumm_format(key)
                        trans_line = convert_to_scumm_format(text_table[key])
                        
                        script_instances = re.findall("((Text\(|Name\(|PutCodeInString\(.+, |setObjectName\(.+,)" + re.escape(og_line) + "\))", script_text)

                        for instance in script_instances:
                            script_text = script_text.replace(instance[0], instance[0].replace(og_line, trans_line))

                elif file_name == "OBHD.xml":
                    if "<name>" in script_text:
                        object_name = re.search("<name>(.*)</name>", script_text).group(1)

                        if text_table[object_name] == object_name:
                            continue
                        
                        script_text = script_text.replace(object_name, text_table[object_name])

                file = open(file_path, "r+")
                current_file_text = file.read()
                file.close()

                if script_text != current_file_text:
                    if not english_version_exists:
                        english_file = open(english_file_path, "w+")
                        english_file.write(english_script_text)
                        english_file.close()
                    file = open(file_path, "w+")
                    file.write(script_text)
                    file.close()


def check_extracts(version):
    print("Replacing text in " + version)

    text_replaced = False

    timestamp_table_file = open(timestamp_table_path, "r")
    timestamp_table = json.loads(timestamp_table_file.read())
    timestamp_table_file.close()

    for file_name in timestamp_table:
        last_text_replace_timestamp = timestamp_table[file_name][version]

        extract_file_path = extract_folder + "/" + file_name
        last_edited_timestamp = os.path.getmtime(extract_file_path)

        if last_edited_timestamp != last_text_replace_timestamp:
            room_name = file_name[:-5]
            print("Replacing text in room " + room_name)

            extract_file = open(extract_file_path, "r")
            text_table = json.loads(extract_file.read())
            extract_file.close()

            check_style(text_table)

            room_path = ""

            if version == "CD":
                room_path = projects_path + "CD/MONKEY1/LECF/LFLF_" + room_name
            elif version == "VGA" or version == "EGA":
                for disk in range(1, 5):
                    room_path = projects_path + version + "/DISK0" + str(disk) + "/LE/LF_" + room_name
                    if os.path.isdir(room_path):
                        break
            
            replace_text(room_path, text_table)

            timestamp_table[file_name][version] = last_edited_timestamp
            text_replaced = True


    if text_replaced:
        timestamp_table_file = open(timestamp_table_path, "w")
        timestamp_table_file.write(json.dumps(timestamp_table, indent = 4))
        timestamp_table_file.close()
    else:
        print("No text to update in " + version)

for version in sys.argv[1:]:
    version = version.upper()

    check_extracts(version)

    recompile.recompile(projects_path + version, games_path + "MI1_TokiPona_" + version, "MI1" + version, False)