import sys, os, json, recompile

tools_path = os.path.join(sys.argv[0].replace("insert_speech.py", ""), "Tools")
resources_path = os.path.join(sys.argv[0].replace("insert_speech.py", ""), "Resources")
scummtr_path = os.path.join(tools_path, "JestarJokin", "scummspeaks_exe", "scummtr.exe")
scummspeaks_path = os.path.join(tools_path, "JestarJokin", "scummspeaks_exe", "scummspeaks.exe")
decompiled_game_path = os.path.join(resources_path, "..", "..", "MI1_Return")

speech_map_path = os.path.join(resources_path, "speech_map.json")
orphaned_clips_path = os.path.join(resources_path, "orphaned_clips.json")

speech_map_start = "<SpeechMap>\n  <TextPath>Z:\\home\\ella\\Games\\Scumm\\MI1_Modded\\dialogue.txt</TextPath>\n  <ResourceType>MONSTER</ResourceType>\n  <CompressionType>OGG</CompressionType>\n  <Sounds>"
speech_map_sound_entry_template = "\n    <SoundEntry>\n      <ID>_ID_</ID>\n      <Source>\n        <Path>Z:\\home\\ella\\ScummProjects\\PythonScripts\\Resources\\ReturnVoice\\_PATH_.ogg</Path>\n        <Offset>0</Offset>\n        <Size>_SIZE_</Size>\n      </Source>\n      <Metadata>\n        <LipSynch>4095</LipSynch>\n      </Metadata>\n      <LinesUsed>_LINES_</LinesUsed>\n    </SoundEntry>"
speech_map_end = "\n  </Sounds>\n  <TextComments />\n  <SoundComments />\n</SpeechMap>"

def fix_fuckup(game_path):
    speech_map_file = open(speech_map_path, 'r')
    speech_map = json.loads(speech_map_file.read())
    speech_map_file.close()

    orphaned_clips_file = open(orphaned_clips_path, 'r')
    orphaned_clips = json.loads(orphaned_clips_file.read())
    orphaned_clips_file.close()

    for line in orphaned_clips:
        if line.replace("\\x07", "\\x0E") in speech_map:
            speech_map[line.replace("\\x07", "\\x0E")] = orphaned_clips[line]
    
    speech_map_file = open(speech_map_path, 'w')
    speech_map_file.write(json.dumps(speech_map, indent=4))
    speech_map_file.close()

def generate_speech_map(game_path):
    recompile.recompile(decompiled_game_path, game_path, "MI1CD", True)
    
    scummtr_output_path = os.path.join(game_path, "dialogue.txt")
    os.system("wine " + scummtr_path + " -H -g monkeycdalt -o -p " + game_path + " -f " + scummtr_output_path)

    scummtr_output_file = open(scummtr_output_path, 'r')
    text_dump = scummtr_output_file.read()
    scummtr_output_file.close()

    text_dump = text_dump.splitlines()

    speech_map_file = open(speech_map_path, 'r')
    speech_map = json.loads(speech_map_file.read())
    speech_map_file.close()

    speech_map_xml = speech_map_start
    id = 0

    for map_line in speech_map:
        if speech_map[map_line] == "":
            continue
        
        voice_clip_name = speech_map[map_line].replace("/", "\\")
        line_instances = []

        i = 0
        while i < len(text_dump):
            dump_line = text_dump[i]

            if dump_line == map_line:
                line_instances.append(i)
            
            i += 1
        
        sound_entry = speech_map_sound_entry_template
        sound_entry = sound_entry.replace("_ID_", str(id))
        id += 100

        sound_entry = sound_entry.replace("_PATH_", voice_clip_name)

        lines_string = ""
        i = 0
        while i < len(line_instances):
            if i > 0:
                lines_string += ", "
            lines_string += str(line_instances[i])
            i += 1
        sound_entry = sound_entry.replace("_LINES_", lines_string)

        voice_clip_path = os.path.join(resources_path, "ReturnVoice", speech_map[map_line] + ".ogg")
        voice_clip_size = os.path.getsize(voice_clip_path)
        sound_entry = sound_entry.replace("_SIZE_", str(voice_clip_size))

        speech_map_xml += sound_entry
    
    speech_map_xml += speech_map_end

    speech_map_xml_path = os.path.join(game_path, "speech_map.xml")
    speech_map_xml_file = open(speech_map_xml_path, 'w')
    speech_map_xml_file.write(speech_map_xml)
    speech_map_xml_file.close()

    os.system("wine " + scummspeaks_path)

    input("Press enter to insert text with voice")
    
    os.system("wine " + scummtr_path + " -H -w -g monkeycdalt -i -p " + game_path + " -f " + scummtr_output_path)

def update_json(game_path):
    recompile.recompile(decompiled_game_path, game_path, "MI1CD", True)

    scummtr_output_path = os.path.join(game_path, "dialogue.txt")
    os.system("wine " + scummtr_path + " -H -g monkeycdalt -o -p " + game_path + " -f " + scummtr_output_path)

    scummtr_output_file = open(scummtr_output_path, 'r')
    text_dump = scummtr_output_file.read()
    scummtr_output_file.close()

    old_speech_map = {}
    speech_map = {}

    if os.path.exists(speech_map_path):
        speech_map_file = open(speech_map_path, 'r')
        old_speech_map = json.loads(speech_map_file.read())
        speech_map_file.close()
    
    for line in text_dump.splitlines():
        if line in old_speech_map:
            speech_map[line] = old_speech_map[line]
        else:
            speech_map[line] = ""
    
    orphaned_clips = {}
    if os.path.exists(orphaned_clips_path):
        orphaned_clips_file = open(orphaned_clips_path, 'r')
        orphaned_clips = json.loads(orphaned_clips_file.read())
        orphaned_clips_file.close()

    for line in old_speech_map:
        if line not in speech_map and old_speech_map[line] != "":
            orphaned_clips[line] = old_speech_map[line]
    
    orphaned_clips_file = open(orphaned_clips_path, 'w')
    orphaned_clips_file.write(json.dumps(orphaned_clips, indent=4))
    orphaned_clips_file.close()

    speech_map_file = open(speech_map_path, 'w')
    speech_map_file.write(json.dumps(speech_map, indent=4))
    speech_map_file.close()



if sys.argv[1] == "update_json":
    update_json(sys.argv[2])
if sys.argv[1] == "insert":
    generate_speech_map(sys.argv[2])
