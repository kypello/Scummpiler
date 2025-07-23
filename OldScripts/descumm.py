#this program goes through all files unpacked by scummpacker and
#runs the descumm tool made by scummvm team on all scripts

import os, sys, re, json
from subprocess import run

tools_path = os.path.join(sys.argv[0].replace("descumm.py", "").replace("decompile.py", ""), "Tools")
descumm_path = os.path.join(tools_path, "ScummVMTools", "descumm.exe")
verb_helper_p2_path = os.path.join(tools_path, "JestarJokin", "scummbler_py2", "src", "verb_helper.py")
verb_helper_exe_path = os.path.join(tools_path, "JestarJokin", "scummbler_exe", "verb_helper.exe")
scummimg_path = os.path.join(tools_path, "JestarJokin", "scummimg_py3", "src", "scummimg.py")

floppy_verb_table = {
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
	"D": "talk_to"
}

cd_verb_table = {
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
	"5B": "assign_inventory_icon",
	"FF": "default"
}

def label_verbs(descumm_text, version):
	start_line = 0
	verb_table = {}

	if version == "4":
		start_line = 2
		verb_table = floppy_verb_table
	elif version == "5":
		start_line = 1
		verb_table = cd_verb_table
	
	line_num = -1
	for line in descumm_text.splitlines():
		line_num += 1
		
		if line_num < start_line:
			continue

		if line.strip().replace(' ','')[1] != '-':
			break
		
		verb_pointer = line.strip().replace(' ','').split('-')

		if verb_pointer[0] in verb_table:
			descumm_text = descumm_text.replace(verb_pointer[1], verb_table[verb_pointer[0]])
	
	return descumm_text

def verify_descummable(file_name, version):
	#these are common filenames that can be descummed
	descummable_cd = ["SCRP", "LSCR", "ENCD", "EXCD", "VERB"]
	descummable_floppy = ["SC", "LS", "EN", "EX", "OC"]

	if version == "5" and file_name[:4] in descummable_cd:
		return True
	if version == "4" and file_name[:2] in descummable_floppy:
		return True
	
	return False

def get_lines_list(descummed_text):
	raw_lines = re.findall("Text\((.*)", descummed_text)
	raw_lines.extend(re.findall("[^t]Name\((.*)", descummed_text))
	raw_lines.extend(re.findall("PutCodeInString\([^,]+, (.*)", descummed_text))
	raw_lines.extend(re.findall("setObjectName\([^,]+,(.*)", descummed_text))				

	lines = []

	for raw_line in raw_lines:
		pos = -1
		nest_level = 1

		while nest_level > 0:
			pos += 1
			if raw_line[pos] == '(':
				nest_level += 1
			elif raw_line[pos] == ')':
				nest_level -= 1
		
		raw_line = raw_line[:pos]
		
		if raw_line == "":
			continue
		
		line = ""
		segments = raw_line.split(" + ")

		for segment in segments:
			if segment[0] == '"':
				line += segment[1:len(segment)-1].replace("<", "\\<").replace(">", "\\>")
			else:
				line += "<" + segment + ">"
		
		if line != " ":
			lines.append(line)

	return lines

def fix_version_4_object_header(descumm_output, file_path, windows_mode):
	if descumm_output == "Events:\nEND\n":
		dmp_file = open(file_path, "rb")
		dmp_file_length = len(dmp_file.read())
		dmp_file.close()

		hex_string = hex(dmp_file_length+3).replace("0x", "00").upper()

		descumm_output = "Events:\n    8 - " + hex_string + "\n[" + hex_string + "] (00) stopObjectCode();\nEND\n"

	object_info = ""
	
	if windows_mode:
		object_info = run(verb_helper_exe_path + ' "' + file_path + '"', capture_output = True, shell = True).stdout
	else:
		object_info = run('python2 ' + verb_helper_p2_path + ' "' + file_path + '"', capture_output = True, shell = True).stdout

	object_info = object_info.replace(b"\x88", "\\x88".encode()).replace(b"\x82", "\\x82".encode()).replace(b"\x0F", "\\x0F".encode()).replace(b"\x07", "\\x07".encode())

	descumm_output = object_info.decode() + descumm_output

	return descumm_output

def fix_descumm_output(raw_descumm_output):
	fixed_descumm_output = raw_descumm_output.replace("^", "...").replace("unknown8(8224)", "newline()").replace("VAR_TIMER_TOTAL", "VAR_TMR_4").replace("setXY(,", ",setXY(").replace(")keepText()", ") + keepText()").replace(")getName(", ") + getName(").replace(")getString(", ") + getString(").replace(")getVerb(", ") + getVerb(")
	
	return fixed_descumm_output

def descumm(input_path, version, args):
	line_table = {}

	windows_mode = os.name == "nt"
	
	timestamp_path = os.path.join(input_path, "compile_timestamps.json")
	timestamp_table = {}
	if os.path.exists(timestamp_path):
		timestamp_file = open(timestamp_path, "r")
		timestamp_table = json.loads(timestamp_file.read())
		timestamp_file.close()

	for subdir, dirs, files in os.walk(input_path): #for every file basically
		for file_name in files:
			file_path = os.path.join(subdir, file_name)
	
			#check if it's a script that can be descummed
			if file_name.endswith(".dmp") and verify_descummable(file_name, version):
				#run the descumm tool and send the results to "descummOutput.txt"
				local_file_path = file_path.replace(input_path, "")
				print("Script found: " + file_path)
				
				raw_descumm_output = ""

				if windows_mode:
					raw_descumm_output = os.popen(descumm_path + " -" + version + ' "' + file_path + '"').read()
				else:	
					raw_descumm_output = os.popen('wine ' + descumm_path + " -" + version + ' "' + file_path + '"').read()

				descumm_output = fix_descumm_output(raw_descumm_output)

				if version == "4" and file_name == "OC.dmp":
					descumm_output = fix_version_4_object_header(descumm_output, file_path, windows_mode)
				
				if file_name == "VERB.dmp" or file_name == "OC.dmp":
					descumm_output = label_verbs(descumm_output, version)

				lines = []
				if file_name == "OC.dmp":
					object_name = re.search('name "(.*)"', descumm_output).group(1)
					
					if object_name != "":
						lines.append(object_name)
				else:
					lines = get_lines_list(descumm_output)
				
				#write the result back into the original .dmp file
				#and also change it to .txt


				if len(lines) > 0 or "text_only" not in args:
					descumm_file_path = file_path[:-4].replace("SCRP", "DE_SCRP").replace("SC_", "DE_SC_") + ".txt"

					descummed_file = open(descumm_file_path, "w")
					descummed_file.write(descumm_output)
					descummed_file.close()

					timestamp_table[descumm_file_path.replace(input_path, "")] = os.path.getmtime(descumm_file_path)

					print("Valid script descummed: " + file_path)

					for line in lines:
						if line not in line_table:
							line_table[line] = line
				else:
					print("Script ignored: " + file_path)

			elif file_name == "OBHD.xml":
				object_file = open(file_path, "r")
				print("Object file found: " + file_path)
				object_file_text = object_file.read()
				object_file.close()

				if "<name>" in object_file_text:
					object_name = re.search("<name>(.*)</name>", object_file_text).group(1)
					line_table[object_name] = object_name
	
	if version == "5" and not "no_images" in args:
		background_image_path = os.path.join(input_path, "background.png")

		os.system('python3 ' + scummimg_path + ' ' + input_path + ' ' + background_image_path + ' -v 5 -d')

		timestamp_table[background_image_path.replace(input_path, "")] = os.path.getmtime(background_image_path)

		local_objects_path = os.path.join("ROOM", "objects")
		objects_path = os.path.join(input_path, local_objects_path)

		object_folders = [f.path for f in os.scandir(objects_path) if f.is_dir()]
		for object_folder in object_folders:
			image_folders = [f.path for f in os.scandir(object_folder) if f.is_dir()]
			for image_folder in image_folders:


				if not os.path.isfile(os.path.join(image_folder, "SMAP.dmp")):
					continue
				
				image_name = "Img" + image_folder.replace(objects_path, "").replace(os.path.sep, "_") + ".png"

				os.system('python3 ' + scummimg_path + ' "' + image_folder + '" "' + os.path.join(objects_path, image_name) + '" -v 7 -d')

				timestamp_table[os.path.sep + os.path.join(local_objects_path, image_name)] = os.path.getmtime(os.path.join(objects_path, image_name))


	timestamp_file = open(timestamp_path, "w")
	timestamp_file.write(json.dumps(timestamp_table, indent = 4))
	timestamp_file.close()

def verb_label_test():
	file = open("TEST_VERB.txt")
	verb_text = file.read()
	file.close()

	print(label_verbs(verb_text, 5))

if __name__ == "__main__":
	descumm(sys.argv[1], sys.argv[2], sys.argv)
	
