import sys, os, json, timestamp_manager
from binary_functions import *

def decode_scale_data(data):
    table = []

    p = 0

    while p < len(data):
        entry = {}

        entry["y1"] = signed_decode(le_decode(data[p+2:p+4]))
        entry["scale1"] = le_decode(data[p:p+2])
        entry["y2"] = signed_decode(le_decode(data[p+6:p+8]))
        entry["scale2"] = le_decode(data[p+4:p+6])

        table.append(entry)
        p += 8
    
    return table

def encode_scale_data(table):
    data = []

    for entry in table:
        data += le_encode(entry["scale1"])
        data += le_encode(signed_encode(entry["y1"]))
        data += le_encode(entry["scale2"])
        data += le_encode(signed_encode(entry["y2"]))
    
    return data

def decode(scale_data_file_path, version, timestamp_manager):
    scale_data_file = open(scale_data_file_path, 'rb')
    scale_data = scale_data_file.read()
    scale_data_file.close()

    scale_table = []

    if version == '4':
        scale_table = decode_scale_data(scale_data[6:])
    elif version == '5':
        scale_table = decode_scale_data(scale_data[8:])

    scale_table_file_path = scale_data_file_path.replace(".dmp", ".json")
    scale_table_file = open(scale_table_file_path, 'w')
    scale_table_file.write(json.dumps(scale_table, indent=4))
    scale_table_file.close()

    timestamp_manager.add_timestamp(scale_table_file_path)

    print(f"Decoded {scale_data_file_path} to {scale_table_file_path}")

def encode(scale_table_file_path, version):
    scale_table_file = open(scale_table_file_path, 'r')
    scale_table = json.loads(scale_table_file.read())
    scale_table_file.close()

    scale_data = encode_scale_data(scale_table)

    header = []

    if version == '4':
        header = le_encode_32(len(scale_data) + 6) + [0x53, 0x41]
    elif version == '5':
        header = [0x53, 0x43, 0x41, 0x4c] + be_encode_32(len(scale_data) + 8)
    
    scale_data = header + scale_data

    scale_data_file_path = scale_table_file_path.replace(".json", ".dmp")
    scale_data_file = open(scale_data_file_path, 'wb')
    scale_data_file.write(bytes(scale_data))
    scale_data_file.close()

    print(f"Encoded {scale_table_file_path} to {scale_data_file_path}")

if __name__ == "__main__":
    if sys.argv[1] == 'd':
        decode(sys.argv[2], sys.argv[3])
    if sys.argv[1] == 'e':
        encode(sys.argv[2], sys.argv[3])



