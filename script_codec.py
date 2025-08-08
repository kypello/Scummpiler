import os, sys, re, json, timestamp_manager
from subprocess import run
from pathlib import Path

python_scripts_path = Path(__file__).resolve().parent
tools_path = Path(python_scripts_path, "Tools")
descumm_path = Path(tools_path, "ScummVMTools", "descumm.exe")

verb_helper_py2_path = Path(tools_path, "JestarJokin", "scummbler_py2", "src", "verb_helper.py")
scummbler_py2_path = Path(tools_path, "JestarJokin", "scummbler_py2", "src", "scummbler.py")

verb_helper_exe_path = Path(tools_path, "JestarJokin", "scummbler_exe", "verb_helper.exe")
scummbler_exe_path = Path(tools_path, "JestarJokin", "scummbler_exe", "scummbler.exe")

object_functions_v4 = {
	"1": "open",
	"2": "close",
	"3": "give",
	"4": "turn_on",
	"5": "turn_off",
	"6": "push",
	"7": "pull",
	"8": "use",
	"9": "look_at",
	"A": "walk_to",
	"B": "pick_up",
	"D": "talk_to",
    "50": "receive_item",
    "5A": "highlight_with_cursor",
    "FF": "default"
}

object_functions_v5 = {
	"2": "open",
	"3": "close",
	"4": "give",
	"5": "push",
	"6": "pull",
	"7": "use",
	"8": "look_at",
	"9": "pick_up",
	"A": "talk_to",
	"B": "walk_to",
	"50": "receive_item",
	"5A": "highlight_with_cursor",
	"5B": "set_inventory_icon",
	"FF": "default"
}


def identify_script_type(script_path):
    if script_path.name.startswith("SC") or script_path.name.startswith("_SC"):
        return "global"
    elif script_path.name.startswith("LS"):
        return "local"
    elif script_path.name.startswith("EN"):
        return "enter"
    elif script_path.name.startswith("EX"):
        return "exit"
    elif script_path.name.startswith("OC") or script_path.name.startswith("VERB"):
        return "object"
    else:
        print(f"Error: file {script_path} of unrecognized script type")
        return "unknown"

def fix_descumm_glitches(script):
    #incorrect names
    script = script.replace("unknown8(8224)", "newline()").replace("VAR_TIMER_TOTAL", "VAR_TMR_4")

    #misplaced comma in drawObject() parameters
    script = script.replace("setXY(,", ", setXY(").replace("setImage(,", ", setImage(")

    #missing plus in string functions
    script = script.replace(")newline(", ") + newline(").replace(")wait(", ") + wait(").replace(")keepText(", ") + keepText(").replace(")getInt(", ") + getInt(").replace(")getName(", ") + getName(").replace(")getVerb(", ") + getVerb(").replace(")getString(", ") + getString(")

    return script

def fix_v4_object_metadata(script, file_path):
    if script == "Events\nEND\n":
        script = "Events\n    FF - default\n[default] stopObjectCode()\nEND\n"
    
    metadata = ""

    if os.name == 'posix':
        metadata = run(f'python2 {verb_helper_py2_path} "{file_path}"', capture_output = True, shell = True).stdout
    elif os.name == 'nt':
        metadata = run(f'{verb_helper_exe_path} "{file_path}"', capture_output = True, shell = True).stdout

    metadata = metadata.replace(b"\x88", "\\x88".encode()).replace(b"\x82", "\\x82".encode()).replace(b"\x0F", "\\x0F".encode()).replace(b"\x07", "\\x07".encode())
    script = metadata.decode() + script

    return script

def label_object_functions(script, version):
    object_functions = {}

    if version == '4':
        object_functions = object_functions_v4
    elif version == '5':
        object_functions = object_functions_v5

    lines = script.splitlines()

    for line in lines:
        if "Events:" in line:
            continue
        
        split_line = line.strip().split(' ')
        
        if len(split_line) < 2 or split_line[1] != '-':
            break
        
        if split_line[0] in object_functions:
            script = script.replace(split_line[2], object_functions[split_line[0]])
    
    return script

def decode(bytecode_file_path, version, timestamp_manager):
    print(f"Decoding {bytecode_file_path}")

    script_type = identify_script_type(bytecode_file_path)
    script = ""

    if os.name == 'posix':
        script = os.popen(f'wine {descumm_path} -{version} "{bytecode_file_path}"').read()
    elif os.name == 'nt':
        script = os.popen(f'{descumm_path} -{version} "{bytecode_file_path}"').read()

    script = fix_descumm_glitches(script)

    if script_type == "object":
        script = label_object_functions(script, version)

        if version == '4':
            script = fix_v4_object_metadata(script, bytecode_file_path)
    
    script_file_path = Path(bytecode_file_path.parent, bytecode_file_path.name.replace(".dmp", ".txt"))

    if script_type == "global":
        if version == '4':
            script_file_path = Path(script_file_path.parent, script_file_path.name.replace("SC_", "_SC_"))
        elif version == '5':
            script_file_path = Path(script_file_path.parent, script_file_path.name.replace("SCRP_", "_SCRP_"))
    
    script_file = open(script_file_path, 'w')
    script_file.write(script)
    script_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(script_file_path)
        
def prepare_special_characters(script):
    script = script.replace("\\xFA", " ")#.replace("...\"", "^^\"").replace("...", "^")

    escape_sequences = re.findall("\\\\x..", script)

    script = bytes(script, 'utf-8')

    for escape_sequence in escape_sequences:
        special_character = bytes.fromhex(escape_sequence[2:])
        escape_sequence = bytes(escape_sequence, 'utf-8')
        
        script = script.replace(escape_sequence, special_character)
    
    return script

def get_scummbler_file_extension(script_type, version):
    if script_type == "global" or script_type == "enter" or script_type == "exit":
        if version == '4':
            return ".SC"
        elif version == '5':
            return ".SCRP"
    elif script_type == "local":
        if version == '4':
            return ".LS"
        elif version == '5':
            return ".LSCR"
    elif script_type == "object":
        if version == '4':
            return ".OC"
        elif version == '5':
            return ".VERB"
    return ""

def fix_bytecode_header(bytecode, script_type, version):
    if version == '4':
        if script_type == "enter":
            bytecode = bytecode[:4] + [0x45, 0x4e] + bytecode[6:]
        elif script_type == "exit":
            bytecode = bytecode[:4] + [0x45, 0x58] + bytecode[6:]
    elif version == '5':
        if script_type == "enter":
            bytecode = [0x45, 0x4e, 0x43, 0x44] + bytecode[4:]
        elif script_type == "exit":
            bytecode = [0x45, 0x58, 0x43, 0x44] + bytecode[4:]
    return bytecode

def encode(script_file_path, version, timestamp_manager):
    print(f"Encoding {script_file_path}")

    script_type = identify_script_type(script_file_path)

    script_file = open(script_file_path, 'r')
    script = script_file.read()
    script_file.close()

    if script_type == "object" and len(script) <= 12:
        print(f"Empty object script {script_file_path} cannot be encoded")
        exit()
    
    script = prepare_special_characters(script)

    scummbler_file_extension = get_scummbler_file_extension(script_type, version)
    middleman_file_path = Path(script_file_path.parent, script_file_path.name.replace(".txt", scummbler_file_extension))

    middleman_file = open(middleman_file_path, 'wb')
    middleman_file.write(script)
    middleman_file.close()

    if os.name == 'posix':
        os.system(f'python2 {scummbler_py2_path} -v {version} -l "{middleman_file_path}"')
    elif os.name == 'nt':
        os.system(f'{scummbler_exe_path} -v {version} -l "{middleman_file_path}"')

    middleman_file = open(middleman_file_path, 'rb')
    bytecode = middleman_file.read()
    middleman_file.close()

    if script_type == "enter" or script_type == "exit":
        bytecode = fix_bytecode_header(bytecode, script_type, version)

    bytecode_file_path = Path(script_file_path.parent, script_file_path.name.replace(".txt", ".dmp"))
    if script_type == "global":
        bytecode_file_path = Path(bytecode_file_path.parent, bytecode_file_path.name.replace("_SC", "SC"))
    
    bytecode_file = open(bytecode_file_path, 'wb')
    bytecode_file.write(bytecode)
    bytecode_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(script_file_path)

if __name__ == "__main__":
    if sys.argv[1] == 'decode':
	    decode(Path(sys.argv[2]).resolve(), sys.argv[3], [])
    elif sys.argv[1] == 'encode':
        encode(Path(sys.argv[2]).resolve(), sys.argv[3], [])

