import sys, os, json

def get_boxes(box_data):
    box_count = box_data[9] * 0x100 + box_data[8]
    boxes = []

    offset = 10

    for i in range(box_count):
        box = {}

        box["index"] = i

        box["top_left"] = (box_data[offset+1] * 0x100 + box_data[offset], box_data[offset+3] * 0x100 + box_data[offset+2])
        box["top_right"] = (box_data[offset+5] * 0x100 + box_data[offset+4], box_data[offset+7] * 0x100 + box_data[offset+6])
        box["bottom_right"] = (box_data[offset+9] * 0x100 + box_data[offset+8], box_data[offset+11] * 0x100 + box_data[offset+10])
        box["bottom_left"] = (box_data[offset+13] * 0x100 + box_data[offset+12], box_data[offset+15] * 0x100 + box_data[offset+14])

        box["zplane_enabled"] = box_data[offset+16]
        box["flags"] = {}

        flags_byte = box_data[offset+17]

        box["flags"]["mirror_x"] = flags_byte & 0x08 > 0
        box["flags"]["mirror_y"] = flags_byte & 0x10 > 0
        box["flags"]["ignore_scale"] = flags_byte & 0x20 > 0
        box["flags"]["locked"] = flags_byte & 0x40 > 0
        box["flags"]["invisible"] = flags_byte & 0x80 > 0
        box["flags"]["unk_0"] = flags_byte & 0x01 > 0
        box["flags"]["unk_1"] = flags_byte & 0x02 > 0
        box["flags"]["unk_2"] = flags_byte & 0x04 > 0

        scale = box_data[offset+19] * 0x100 + box_data[offset+18]

        box["scale"] = {}
        if scale & 0x8000:
            box["scale"]["type"] = "dynamic"
            box["scale"]["table_index"] = scale & 0x7FFF
        else:
            box["scale"]["type"] = "fixed"
            box["scale"]["factor"] = scale

        boxes.append(box)
        offset += 20
    
    return boxes

def get_nav_tables(matrix_data, box_count):
    nav_tables = []
    offset = 8

    for i in range(box_count):
        nav_table = []
        while matrix_data[offset] != 0xFF:
            entry = {}
            entry["range"] = (matrix_data[offset], matrix_data[offset+1])
            entry["goto"] = matrix_data[offset+2]
            nav_table.append(entry)

            offset += 3
        
        nav_tables.append(nav_table)
        offset += 1
    
    return nav_tables

def get_scale_table(scale_data):
    scale_table = []

    offset = 8

    for i in range(4):
        entry = {}
        entry["index"] = i

        entry["y1"] = scale_data[offset+3] * 0x100 + scale_data[offset+2]
        entry["scale1"] = scale_data[offset+1] * 0x100 + scale_data[offset]
        entry["y2"] = scale_data[offset+7] * 0x100 + scale_data[offset+6]
        entry["scale2"] = scale_data[offset+5] * 0x100 + scale_data[offset+4]

        scale_table.append(entry)
        offset += 8
    
    return scale_table

def decode(room_path, output_path):
    boxd_file = open(os.path.join(room_path, "ROOM", "BOXD.dmp"), 'rb')
    box_data = boxd_file.read()
    boxd_file.close()

    boxm_file = open(os.path.join(room_path, "ROOM", "BOXM.dmp"), 'rb')
    matrix_data = boxm_file.read()
    boxm_file.close()

    scal_file = open(os.path.join(room_path, "ROOM", "SCAL.dmp"), 'rb')
    scale_data = scal_file.read()
    scal_file.close()

    boxes = get_boxes(box_data)
    nav_tables = get_nav_tables(matrix_data, len(boxes))

    for i in range(len(boxes)):
        boxes[i]["navigation_table"] = nav_tables[i]
    
    scale_table = get_scale_table(scale_data)

    output_info = {}
    output_info["boxes"] = boxes
    output_info["scale_table"] = scale_table

    output_file = open(output_path, 'w')
    output_file.write(json.dumps(output_info, indent=4))
    output_file.close()

def get_coordinate_data(coord):
    data = []

    data.append(coord[0] & 0xFF)
    data.append((coord[0] & 0xFF00) >> 8)
    data.append(coord[1] & 0xFF)
    data.append((coord[1] & 0xFF00) >> 8)

    return data

def encode_boxes(boxes):
    box_data = []

    box_count = len(boxes)

    box_data.append(box_count & 0xFF)
    box_data.append((box_count & 0xFF00) >> 8)

    for box in boxes:
        tl = box["top_left"]
        tr = box["top_right"]
        br = box["bottom_right"]
        bl = box["bottom_left"]

        box_data += get_coordinate_data(tl)
        box_data += get_coordinate_data(tr)
        box_data += get_coordinate_data(br)
        box_data += get_coordinate_data(bl)

        box_data.append(box["zplane_enabled"])

        flag_byte = 0

        if box["flags"]["unk_0"]:
            flag_byte |= 0x01
        if box["flags"]["unk_1"]:
            flag_byte |= 0x02
        if box["flags"]["unk_2"]:
            flag_byte |= 0x04
        if box["flags"]["mirror_x"]:
            flag_byte |= 0x08
        if box["flags"]["mirror_y"]:
            flag_byte |= 0x10
        if box["flags"]["ignore_scale"]:
            flag_byte |= 0x20
        if box["flags"]["locked"]:
            flag_byte |= 0x40
        if box["flags"]["invisible"]:
            flag_byte |= 0x80
        
        box_data.append(flag_byte)

        scale = 0

        if box["scale"]["type"] == "fixed":
            scale = box["scale"]["factor"]
        elif box["scale"]["type"] == "dynamic":
            scale = box["scale"]["table_index"] | 0x8000

        box_data.append(scale & 0xFF)
        box_data.append((scale & 0xFF00) >> 8)
    
    header_data = [0x42, 0x4F, 0x58, 0x44, 0x00, 0x00]
    size = len(box_data) + 8
    header_data.append((size & 0xFF00) >> 8)
    header_data.append(size & 0xFF)

    box_data = header_data + box_data
    return box_data

def encode_matrix(boxes):
    matrix_data = []

    box_count = len(boxes)

    for box in boxes:
        nav_table = box["navigation_table"]

        for entry in nav_table:
            matrix_data.append(entry["range"][0])
            matrix_data.append(entry["range"][1])
            matrix_data.append(entry["goto"])
        
        matrix_data.append(0xFF)
    
    header_data = [0x42, 0x4F, 0x58, 0x4D, 0x00, 0x00]
    size = len(matrix_data) + 8
    header_data.append((size & 0xFF00) >> 8)
    header_data.append(size & 0xFF)

    matrix_data = header_data + matrix_data
    return matrix_data

def encode_scale(scale_table):
    scale_data = [0x53, 0x43, 0x41, 0x4C, 0x00, 0x00, 0x00, 0x28]

    for entry in scale_table:
        scale_data.append(entry["scale1"] & 0xFF)
        scale_data.append((entry["scale1"] & 0xFF00) >> 8)

        scale_data.append(entry["y1"] & 0xFF)
        scale_data.append((entry["y1"] & 0xFF00) >> 8)

        scale_data.append(entry["scale2"] & 0xFF)
        scale_data.append((entry["scale2"] & 0xFF00) >> 8)

        scale_data.append(entry["y2"] & 0xFF)
        scale_data.append((entry["y2"] & 0xFF00) >> 8)
    
    return scale_data

def encode(input_path, room_path):
    input_file = open(input_path, 'r')
    box_info = json.loads(input_file.read())
    input_file.close()

    boxes = box_info["boxes"]
    scale_table = box_info["scale_table"]

    box_data = encode_boxes(boxes)
    matrix_data = encode_matrix(boxes)
    scale_data = encode_scale(scale_table)

    boxd_file = open(os.path.join(room_path, "ROOM", "BOXD.dmp"), 'wb')
    boxd_file.write(bytes(box_data))
    boxd_file.close()

    boxm_file = open(os.path.join(room_path, "ROOM", "BOXM.dmp"), 'wb')
    boxm_file.write(bytes(matrix_data))
    boxm_file.close()

    scal_file = open(os.path.join(room_path, "ROOM", "SCAL.dmp"), 'wb')
    scal_file.write(bytes(scale_data))
    scal_file.close()

def compare(path1, path2):
    file1 = open(path1, 'rb')
    data1 = file1.read()
    file1.close()

    file2 = open(path2, 'rb')
    data2 = file2.read()
    file2.close()

    for i in range(len(data1)):
        if data1[i] != data2[i]:
            print("Data at offset " + hex(i) + " is different")

if __name__ == "__main__":
    if sys.argv[1] == 'd':
        decode(sys.argv[2], sys.argv[3])
    if sys.argv[1] == 'e':
        encode(sys.argv[2], sys.argv[3])
    if sys.argv[1] == 'c':
        compare(sys.argv[2], sys.argv[3])