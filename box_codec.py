import sys, os, json

def le_decode(bytes):
    return bytes[1] * 0x100 + bytes[0]

def le_encode(value):
    return [value & 0xff, (value & 0xff00) >> 8]

def le_encode_32(value):
    return [value & 0xff, (value & 0xff00) >> 8, (value & 0xff0000) >> 16, (value & 0xff000000) >> 24]

def be_encode_32(value):
    return [(value & 0xff000000) >> 24, (value & 0xff0000) >> 16, (value & 0xff00) >> 8, value & 0xff]

def signed(value):
    return ((value & 0x8000) >> 15) * -0x8000 + (value & 0x7fff)

def signed_encode(value):
    return ((value & 0x80000000) >> 16) + (value & 0x7fff)

def decode_box_data(box_data, version):
    p = 0

    box_count = 0

    if version == "4":
        box_count = box_data[p]
        p += 1
    
    elif version == "5":
        box_count = le_decode(box_data[p:p+2])
        p += 2

    boxes = []

    for i in range(box_count):
        box = {}

        box["index"] = i

        vertices = []

        for j in range(4):
            vertices.append( ( signed( le_decode(box_data[p:p+2]) ), signed( le_decode(box_data[p+2:p+4]) ) ) )
            p += 4
        
        box["vertices"] = vertices

        box["zplane_enabled"] = box_data[p]
        p += 1

        box["flags"] = {}

        flags_byte = box_data[p]
        p += 1

        box["flags"]["mirror_x"] = flags_byte & 0x08 > 0
        box["flags"]["mirror_y"] = flags_byte & 0x10 > 0
        box["flags"]["ignore_scale"] = flags_byte & 0x20 > 0
        box["flags"]["locked"] = flags_byte & 0x40 > 0
        box["flags"]["invisible"] = flags_byte & 0x80 > 0
        box["flags"]["unk_0"] = flags_byte & 0x01 > 0
        box["flags"]["unk_1"] = flags_byte & 0x02 > 0
        box["flags"]["unk_2"] = flags_byte & 0x04 > 0

        scale = le_decode(box_data[p:p+2])
        p += 2

        box["scale"] = {}
        if scale & 0x8000:
            box["scale"]["type"] = "dynamic"
            box["scale"]["table_index"] = scale & 0x7FFF
        else:
            box["scale"]["type"] = "fixed"
            box["scale"]["factor"] = scale

        boxes.append(box)
    
    return boxes
    
    

def decode_matrix_data(matrix_data, box_count):
    p = 0

    matrices = []

    for i in range(box_count):
        matrix = {}
        entries = []
        while matrix_data[p] != 0xFF:
            entry = {}
            entry["range_start"] = matrix_data[p]
            entry["range_end"] = matrix_data[p+1]
            entry["goto"] = matrix_data[p+2]
            entries.append(entry)

            p += 3
        
        matrix["index"] = i
        matrix["table"] = entries
        matrices.append(matrix)
        p += 1
    
    return matrices

def read_data_v4(room_path):
    bx_file = open(os.path.join(room_path, "BX.dmp"), 'rb')
    box_matrix_data = bx_file.read()
    bx_file.close()

    box_count = box_matrix_data[6]
    box_data_end = 6 + 1 + 20 * box_count

    box_data = box_matrix_data[6:box_data_end]
    matrix_data = box_matrix_data[box_data_end:]

    return (box_data, matrix_data)

def read_data_v5(room_path):
    boxd_file = open(os.path.join(room_path, "BOXD.dmp"), 'rb')
    box_data = boxd_file.read()[8:]
    boxd_file.close()

    boxm_file = open(os.path.join(room_path, "BOXM.dmp"), 'rb')
    matrix_data = boxm_file.read()[8:]
    boxm_file.close()

    return (box_data, matrix_data)

def write_json_v4(room_path, boxes, matrices):
    output_info = {}
    output_info["boxes"] = boxes
    output_info["matrices"] = matrices

    output_path = os.path.join(room_path, "BX.json")

    output_file = open(output_path, 'w')
    output_file.write(json.dumps(output_info, indent=4))
    output_file.close()

def write_json_v5(room_path, boxes, matrices):
    boxd_file = open(os.path.join(room_path, "BOXD.json"), 'w')
    boxd_file.write(json.dumps(boxes, indent=4))
    boxd_file.close()

    boxm_file = open(os.path.join(room_path, "BOXM.json"), 'w')
    boxm_file.write(json.dumps(matrices, indent=4))
    boxm_file.close()

def decode(room_path, version):
    box_data = []
    matrix_data = []

    box_count = 0

    if version == "4":
        (box_data, matrix_data) = read_data_v4(room_path)
    elif version == "5":
        (box_data, matrix_data) = read_data_v5(room_path)
    
    boxes = decode_box_data(box_data, version)
    box_count = len(boxes)

    matrices = decode_matrix_data(matrix_data, box_count)

    if version == "4":
        write_json_v4(room_path, boxes, matrices)
    elif version == "5":
        write_json_v5(room_path, boxes, matrices)
    
    print("Decoded box and matrix data")





def encode_box_data(boxes, version):
    box_data = []

    box_count = len(boxes)

    if version == "4":
        box_data.append(box_count)
    elif version == "5":
        box_data += le_encode(box_count)

    for box in boxes:
        vertices = box["vertices"]

        for vertex in vertices:
            box_data += le_encode(signed_encode(vertex[0]))
            box_data += le_encode(signed_encode(vertex[1]))

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

        box_data += le_encode(scale)
    
    return box_data

def encode_matrix_data(matrices):
    matrix_data = []

    for matrix in matrices:
        table = matrix["table"]

        for entry in table:
            matrix_data.append(entry["range_start"])
            matrix_data.append(entry["range_end"])
            matrix_data.append(entry["goto"])
        
        matrix_data.append(0xFF)
    
    return matrix_data

def read_json_v4(room_path):
    bx_file = open(os.path.join(room_path, "BX.json"), 'r')
    bx = json.loads(bx_file.read())
    bx_file.close()

    return (bx["boxes"], bx["matrices"])

def read_json_v5(room_path):
    boxd_file = open(os.path.join(room_path, "BOXD.json"), 'r')
    boxes = json.loads(boxd_file.read())
    boxd_file.close()

    boxm_file = open(os.path.join(room_path, "BOXM.json"), 'r')
    matrices = json.loads(boxm_file.read())
    boxm_file.close()

    return (boxes, matrices)

def write_data_v4(room_path, box_data, matrix_data):
    bx_header = [0x42, 0x58]
    bx_data_length = 6 + len(box_data) + len(matrix_data)

    bx_data = le_encode_32(bx_data_length) + bx_header + box_data + matrix_data

    bx_file = open(os.path.join(room_path, "BX.dmp"), 'wb')
    bx_file.write(bytes(bx_data))
    bx_file.close()

def write_data_v5(room_path, box_data, matrix_data):
    boxd_header = [0x42, 0x4f, 0x58, 0x44]
    box_data_length = 8 + len(box_data)

    box_data = boxd_header + be_encode_32(box_data_length) + box_data

    boxd_file = open(os.path.join(room_path, "BOXD.dmp"), 'wb')
    boxd_file.write(bytes(box_data))
    boxd_file.close()

    boxm_header = [0x42, 0x4f, 0x58, 0x4d]
    matrix_data_length = 8 + len(matrix_data)
    
    matrix_data = boxm_header + be_encode_32(matrix_data_length) + matrix_data

    boxm_file = open(os.path.join(room_path, "BOXM.dmp"), 'wb')
    boxm_file.write(bytes(matrix_data))
    boxm_file.close()

def encode(room_path, version):
    boxes = []
    matrices = []

    if version == "4":
        (boxes, matrices) = read_json_v4(room_path)
    elif version == "5":
        (boxes, matrices) = read_json_v5(room_path)
    
    box_data = encode_box_data(boxes, version)
    matrix_data = encode_matrix_data(matrices)

    if version == "4":
        write_data_v4(room_path, box_data, matrix_data)
    elif version == "5":
        write_data_v5(room_path, box_data, matrix_data)
    
    print("Encoded box and matrix data")


if __name__ == "__main__":
    if sys.argv[1] == 'd':
        decode(sys.argv[2], sys.argv[3])
    if sys.argv[1] == 'e':
        encode(sys.argv[2], sys.argv[3])






