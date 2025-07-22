#this program runs through all .txt files and runs the scummbler tool on them, nice and simple
import os, sys, re, json, zplane_decoder, box_decoder

tools_path = tools_path = os.path.join(sys.argv[0].replace("rescumm.py", "").replace("recompile.py", "").replace("insert_speech.py", ""), "Tools", "JestarJokin")
scummbler_py2_path = os.path.join(tools_path, "scummbler_py2", "src", "scummbler.py")
scummbler_exe_path = os.path.join(tools_path, "scummbler_exe", "scummbler.exe")
scummimg_path = os.path.join(tools_path, "scummimg_py3", "src", "scummimg.py")

def logo_sc_22_fix(bytecode):
	print("Fixing Logo Script 22")
	return bytecode.replace(b"\x05\x05\xff\x01", b"\x09\x0a\xff\x01")	

def map_en_sc_fix(bytecode):
	print("Fixing map enter script")
	return bytecode.replace(b"\x73\x04", b"\x33\x44").replace(b"\xf3\x04", b"\x33\xc4")
	

def get_scummbled_file_path(file_path, file_name, version):
	if version == "5":
		if file_name[:4] == "ENCD" or file_name[:4] == "EXCD" or file_name[:4] == "SCRP":
			return file_path.replace(".txt", ".SCRP")
		if file_name[:4] == "VERB":
			return file_path.replace(".txt", ".VERB")
		if file_name[:4] == "LSCR":
			return file_path.replace(".txt", ".LSCR")
	
	if version == "4":
		if file_name[:2] == "EN" or file_name[:2] == "EX" or file_name[:2] == "SC":
			return file_path.replace(".txt", ".SC")
		if file_name[:2] == "OC":
			return file_path.replace(".txt", ".OC")
		if file_name[:2] == "LS":
			return file_path.replace(".txt", ".LS")

def fix_bytecode_header(bytecode, file_name, version):
	if version == "5":
		if file_name[:4] == "ENCD":
			return bytecode.replace(b"SCRP", b"ENCD")
		elif file_name[:4] == "EXCD":
			return bytecode.replace(b"SCRP", b"EXCD")
	elif version == "4":
		if file_name[:2] == "EN":
			return bytecode.replace(b"SC", b"EN")
		elif file_name[:2] == "EX":
			return bytecode.replace(b"SC", b"EX")
	return bytecode

def rescumm(input_path, version):
	windows_mode = os.name == "nt"

	donor_list_path = os.path.join(input_path, "donor_list.json")
	if os.path.exists(donor_list_path):
		#print("Skipping object donor room")
		return False

	timestamp_path = os.path.join(input_path, "compile_timestamps.json")
	timestamp_table = {}

	if os.path.exists(timestamp_path):
		timestamp_file = open(timestamp_path, "r")
		timestamp_table = json.loads(timestamp_file.read())
		timestamp_file.close()

	files_rescummed = False

	for subdir, dirs, files in os.walk(input_path):
		for file_name in files:
			file_path = os.path.join(subdir, file_name)
			if file_name == "boxes.json" or file_name == "ADL.mid" or file_name.endswith(".png") or file_name.endswith("xml") or (file_name.endswith(".txt") and not "EN_" in file_name):
				local_file_path = file_path.replace(input_path, "")
				if not local_file_path in timestamp_table:
					timestamp_table[local_file_path] = 0
					
				if os.path.getmtime(file_path) == timestamp_table[local_file_path]:
					continue

				if file_name == "boxes.json":
					print("Attempting to encode walk boxes for " + input_path)
					box_decoder.encode(file_path, input_path)
				elif file_name.endswith(".png"):
					if file_name == "background.png":
						print("Attempting to encode background for " + input_path)
						os.system('python3 ' + scummimg_path + ' ' + input_path + ' ' + file_path + ' -v 5 -f -e')
					elif file_name == "zplane.png":
						print("Attempting to encode zplane for " + input_path)
						header_path = os.path.join(input_path, "ROOM", "RMHD.xml")
						output_path = os.path.join(input_path, "ROOM", "RMIM", "IM00", "ZP01.dmp")
						zplane_decoder.encode(file_path, header_path, output_path)
					else:
						print("Attempting to encode image " + file_path)
						local_objects_path = os.path.join("ROOM", "objects")
						image_name = file_name.replace(".png", "").replace("Img_", "").replace("Zpl_", "")
						image_folder = os.path.join(input_path, local_objects_path, image_name[:-5], image_name[-4:])
						if "Img_" in file_name:
							os.system('python3 ' + scummimg_path + ' "' + image_folder + '" "' + file_path + '" -v 7 -f -e')
						elif "Zpl_" in file_name:
							header_path = os.path.join(image_folder, "..", "OBHD.xml")
							output_path = os.path.join(image_folder, "ZP01.dmp")
							zplane_decoder.encode(file_path, header_path, output_path)
				elif file_name.endswith(".txt"):
					print("Attempting to rescumm " + file_path)

					file = open(file_path, "r")
					script_text_raw = file.read()
					file.close()

					if file_name == "VERB.txt" and len(script_text_raw) <= 12:
						print("Skipping empty verb")
						timestamp_table[local_file_path] = os.path.getmtime(file_path)
						files_rescummed = True
						continue

					script_text = script_text_raw.replace("\\xFA", " ").replace("...\"", "\u005E\u005E\"").replace("...", "\u005E")

					escape_chars = re.findall("\\\\x..", script_text)
					logo_sc_22_fix_needed = False
					map_en_sc_fix_needed = version == "4" and os.join("LF_063_map", "RO", "scripts", "EN") in file_path

					for escape_char in escape_chars:
						hex_value = escape_char[2:].lower()

						if hex_value == "0a" or hex_value == "09":
							hex_value = "05"
							if file_name == "SC_022.txt":
								logo_sc_22_fix_needed = True
							else:
								print("WOAH THERE")
								print("Possibly another goofy character in a different file?!")
								print(file_path)
								#exit()
						
						script_text = script_text.replace(escape_char, chr(int(hex_value, 16)))
					
					dmp_file_path = file_path.replace(".txt", ".dmp").replace("DE_", "")
					scummbled_file_path = get_scummbled_file_path(file_path.replace("DE_", ""), file_name.replace("DE_", ""), version)

					script_text_bytes = bytes(script_text, "utf-8")
					script_text_bytes = script_text_bytes.replace(b"\xC2\x88", b"\x88").replace(b"\xC2\x82", b"\x82")

					file = open(scummbled_file_path, "wb")
					file.write(script_text_bytes)
					file.close()

					if windows_mode:
						os.system(scummbler_exe_path + ' -v ' + version + ' -l "' + scummbled_file_path + '"')
					else:
						os.system('python2 ' + scummbler_py2_path + ' -v ' + version + ' -l "' + scummbled_file_path + '"')
					
					file = open(scummbled_file_path, "rb")
					bytecode = file.read()
					file.close()

					bytecode = fix_bytecode_header(bytecode, file_name.replace("DE_", ""), version)

					if logo_sc_22_fix_needed:
						bytecode = logo_sc_22_fix(bytecode)
					
					if map_en_sc_fix_needed:
						bytecode = map_en_sc_fix(bytecode)

					file = open(dmp_file_path, "wb")
					file.write(bytecode)
					file.close()
				
				timestamp_table[local_file_path] = os.path.getmtime(file_path)
				files_rescummed = True

	if files_rescummed:
		timestamp_file = open(timestamp_path, "w")
		timestamp_file.write(json.dumps(timestamp_table, indent = 4))
		timestamp_file.close()
	
	return files_rescummed
				

if __name__ == "__main__":
	rescumm(sys.argv[1], sys.argv[2])