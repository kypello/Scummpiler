import sys, os, json, timestamp_manager
from binary_functions import *
from pathlib import Path

def decode_box_data(box_data, version):
    p = 0

    box_count = 0

    if version == "4":
        box_count = box_data[p]
        p += 1
    
    elif version == "5":
        box_count = le_decode(box_data[p:p+2], 2)
        p += 2

    boxes = []

    for i in range(box_count):
        box = {}

        box["index"] = i

        vertices = []

        for j in range(4):
            vertices.append( ( signed_decode( le_decode(box_data[p:p+2], 2) ), signed_decode( le_decode(box_data[p+2:p+4], 2) ) ) )
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

        scale = le_decode(box_data[p:p+2], 2)
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
    
def decode_matrix_data(matrix_data):
    p = 0
    i = 0

    matrices = []

    while p < len(matrix_data) - 1:
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
        i += 1
    
    return matrices

def separate_data_v4(box_matrix_data):
    box_count = box_matrix_data[6]
    box_data_end = 6 + 1 + 20 * box_count

    box_data = box_matrix_data[6:box_data_end]
    matrix_data = box_matrix_data[box_data_end:]

    return (box_data, matrix_data)

def decode(encoded_file_path, version, timestamp_manager):
    print(f"Decoding {encoded_file_path}")

    encoded_file = open(encoded_file_path, 'rb')
    encoded_data = encoded_file.read()
    encoded_file.close()

    decoded_data = {}
    file_type = ""

    if version == '4':
        file_type = "combined"

        (encoded_box_data, encoded_matrix_data) = separate_data_v4(encoded_data)
        decoded_data["boxes"] = decode_box_data(encoded_box_data, version)
        decoded_data["matrices"] = decode_matrix_data(encoded_matrix_data)

    elif version == '5':
        if encoded_file_path.name.endswith("BOXD.dmp"):
            file_type = "box"
            decoded_data = decode_box_data(encoded_data[8:], version)

        elif encoded_file_path.name.endswith("BOXM.dmp"):
            file_type = "matrix"
            decoded_data = decode_matrix_data(encoded_data[8:])


    decoded_file_path = Path(encoded_file_path.parent, encoded_file_path.name.replace(".dmp", ".json"))

    decoded_file = open(decoded_file_path, 'w')
    decoded_file.write(json.dumps(decoded_data, indent=4))
    decoded_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(decoded_file_path)


def encode_box_data(boxes, version):
    box_data = []

    box_count = len(boxes)

    if version == "4":
        box_data.append(box_count)
    elif version == "5":
        box_data += le_encode(box_count, 2)

    for box in boxes:
        vertices = box["vertices"]

        for vertex in vertices:
            box_data += le_encode(signed_encode(vertex[0]), 2)
            box_data += le_encode(signed_encode(vertex[1]), 2)

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

        box_data += le_encode(scale, 2)
    
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

def encode(decoded_file_path, version, timestamp_manager):
    print(f"Encoding {decoded_file_path}")

    decoded_file = open(decoded_file_path, 'r')
    decoded_data = json.loads(decoded_file.read())
    decoded_file.close()

    encoded_data = []
    file_type = ""

    if version == '4':
        encoded_box_data = encode_box_data(decoded_data["boxes"], version)
        encoded_matrix_data = encode_matrix_data(decoded_data["matrices"])

        header = [0x42, 0x58]
        encoded_data_length = 6 + len(encoded_box_data) + len(encoded_matrix_data)

        encoded_data = le_encode(encoded_data_length, 4) + header + encoded_box_data + encoded_matrix_data
        file_type = "combined"

    elif version == '5':
        header = []

        if decoded_file_path.name.endswith("BOXD.json"):
            file_type = "box"
            encoded_data = encode_box_data(decoded_data, version)
            header = [0x42, 0x4f, 0x58, 0x44]

        elif decoded_file_path.name.endswith("BOXM.json"):
            file_type = "matrix"
            encoded_data = encode_matrix_data(decoded_data)
            header = [0x42, 0x4f, 0x58, 0x4d]

        encoded_data_length = 8 + len(encoded_data)
        encoded_data = header + be_encode(encoded_data_length, 4) + encoded_data
    
    encoded_file_path = Path(decoded_file_path.parent, decoded_file_path.name.replace(".json", ".dmp"))
    encoded_file = open(encoded_file_path, 'wb')
    encoded_file.write(bytes(encoded_data))
    encoded_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(decoded_file_path)

if __name__ == "__main__":
    if sys.argv[1] == 'decode':
        decode(Path(sys.argv[2]).resolve(), sys.argv[3], [])

    elif sys.argv[1] == 'encode':
        encode(Path(sys.argv[2]).resolve(), sys.argv[3], [])






