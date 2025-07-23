import os, re, json

unpacked = "Unpacked"

table = {}
highest = 0

for subdir, dirs, files in os.walk(unpacked):
    for file_name in files:
        if file_name == "OBHD.xml":
            file = open(subdir + "/" + file_name, "r")
            object_def = file.read()
            file.close()

            object_name = " "

            if "<name>" in object_def:
                object_name = re.search("<name>(.*)</name>", object_def).group(1)
            
            object_id = re.search("<id>(.*)</id>", object_def).group(1)

            if int(object_id) > highest:
                highest = int(object_id)

            table[object_id] = object_name

sorted_table = {}

for i in range(0, highest+1):
    for object_id in table:
        if int(object_id) == i:
            if table[object_id] != " ":
                sorted_table[int(object_id)] = table[object_id]
                break

json_file = open("object_registry.json", "w")
json_file.write(json.dumps(sorted_table, indent = 4))
json_file.close()

