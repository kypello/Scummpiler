import os, json

cd_tables_path = "LineExtracts_CD/"
vga_tables_path = "LineExtracts_EGA/"

for file_name in os.listdir(cd_tables_path):
    cd_file = open(cd_tables_path + file_name, "r")
    cd_file_text = cd_file.read()
    cd_file.close()

    vga_file = open(vga_tables_path + file_name, "r")
    vga_file_text = vga_file.read()
    vga_file.close()

    cd_table = json.loads(cd_file_text)
    vga_table = json.loads(vga_file_text)

    #print('\n' + file_name)

    lines_added = False

    for line in vga_table:
        if line not in cd_table:
            cd_table[line] = line
            lines_added = True
            print(line)
    
    if lines_added:
        cd_file = open(cd_tables_path + file_name, "w")
        cd_file.write(json.dumps(cd_table, indent = 4))
        cd_file.close()