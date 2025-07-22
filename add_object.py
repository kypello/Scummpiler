import os, sys, json
import xml.etree.ElementTree as et

resources_path = os.path.join(sys.argv[0].replace("add_object.py", ""), "Resources")
obhd_template_path = os.path.join(resources_path, "OBHD_Template.xml")
verb_template_path = os.path.join(resources_path, "VERB.dmp")
verb_script_template_path = os.path.join(resources_path, "VERB.txt")

def locate_available_id(room_path, mark_as_donated = False):
    objects_path = os.path.join(room_path, "ROOM", "objects")
    donor_list_path = os.path.join(room_path, "donor_list.json")

    donor_list = []
    if os.path.exists(donor_list_path):
        donor_list_file = open(donor_list_path, 'r')
        donor_list = json.loads(donor_list_file.read())
        donor_list_file.close()

    for object_name in os.listdir(objects_path):
        object_path = os.path.join(objects_path, object_name)

        if not os.path.isdir(object_path):
            continue
        
        object_id = int(object_name[:4])

        if not object_id in donor_list:
            donor_list.append(object_id)
            donor_list_file = open(donor_list_path, 'w')
            donor_list_file.write(json.dumps(donor_list))
            donor_list_file.close()

            return object_id
    
    print("ERROR: Donor room is out of objects!!")
    exit()
    return "0"

def make_object_folder(room_path, object_name, object_id):
    object_folder_name = str(object_id)
    while len(object_folder_name) < 4:
        object_folder_name = "0" + object_folder_name
    object_folder_name += "_" + object_name

    object_path = os.path.join(room_path, "ROOM", "objects", object_folder_name)
    os.mkdir(object_path)

    return object_path

def add_obhd_file(object_path, object_name, object_id):
    obhd_template_file = open(obhd_template_path, 'r')
    obhd = obhd_template_file.read()
    obhd_template_file.close()

    if object_name == "":
        obhd = obhd.replace("<name>NAME</name>", "<name />")
    else:
        obhd = obhd.replace("NAME", object_name)
    
    obhd = obhd.replace("ID", str(object_id))

    obhd_path = os.path.join(object_path, "OBHD.xml")
    obhd_file = open(obhd_path, 'w')
    obhd_file.write(obhd)
    obhd_file.close()

def add_verb_file(object_path):
    verb_template_file = open(verb_template_path, 'rb')
    verb_data = verb_template_file.read()
    verb_template_file.close()

    verb_path = os.path.join(object_path, "VERB.dmp")

    verb_file = open(verb_path, 'wb')
    verb_file.write(verb_data)
    verb_file.close()

    verb_script_template_file = open(verb_script_template_path, 'r')
    verb_script = verb_script_template_file.read()
    verb_script_template_file.close()

    verb_script_path = os.path.join(object_path, "VERB.txt")

    verb_script_file = open(verb_script_path, 'w')
    verb_script_file.write(verb_script)
    verb_script_file.close()

def increment_room_object_count(room_path):
    rmhd_path = os.path.join(room_path, "ROOM", "RMHD.xml")

    rmhd_data = et.parse(rmhd_path)
    rmhd_root = rmhd_data.getroot()

    object_count = int(rmhd_root[2].text)
    object_count += 1
    rmhd_root[2].text = str(object_count)

    rmhd_data.write(rmhd_path)

def insert_into_order_file(room_path, object_id):
    order_file_path = os.path.join(room_path, "ROOM", "objects", "order.xml")
    order_data = et.parse(order_file_path)
    order_root = order_data.getroot()

    new_order_entry = et.Element("order-entry")
    new_order_entry.text = str(object_id)
    order_root[0].append(new_order_entry)
    order_root[1].append(new_order_entry)

    order_data.write(order_file_path)

def set_default_class_data(room_path, object_id, class_data):
    database_id = object_id + 1

    dobj_path = os.path.join(room_path, "..", "..", "..", "dobj.xml")
    dobj_data = et.parse(dobj_path)
    dobj_root = dobj_data.getroot()

    for object_entry in dobj_root:
        if object_entry[0].text == str(database_id):
            object_entry[3].text = class_data
            break
    
    dobj_data.write(dobj_path)

def add_object(room_path, object_name, class_data = "0x0", donor_room_path = ""):
    if donor_room_path == "":
        donor_room_path = os.path.join(room_path, "..", "LFLF_039_hellmaze")
    
    object_id = locate_available_id(donor_room_path, True)
    object_path = make_object_folder(room_path, object_name, object_id)
    add_obhd_file(object_path, object_name, object_id)
    add_verb_file(object_path)
    increment_room_object_count(room_path)
    insert_into_order_file(room_path, object_id)
    set_default_class_data(room_path, object_id, class_data)

    print("Added object " + object_name + " with ID " + str(object_id) + " to room " + room_path)


add_object(sys.argv[1], sys.argv[2])
