import sys, os, json, timestamp_manager
from binary_functions import *
from pathlib import Path

def decode_scale_data(data):
    table = []

    p = 0

    while p < len(data):
        entry = {}

        entry["y1"] = signed_decode(le_decode(data[p+2:p+4], 2))
        entry["scale1"] = le_decode(data[p:p+2], 2)
        entry["y2"] = signed_decode(le_decode(data[p+6:p+8], 2))
        entry["scale2"] = le_decode(data[p+4:p+6], 2)

        table.append(entry)
        p += 8
    
    return table

def encode_scale_data(table):
    data = []

    for entry in table:
        data += le_encode(entry["scale1"], 2)
        data += le_encode(signed_encode(entry["y1"]), 2)
        data += le_encode(entry["scale2"], 2)
        data += le_encode(signed_encode(entry["y2"]), 2)
    
    return data

def decode(scale_data_file_path, version, timestamp_manager):
    print(f"Decoding {scale_data_file_path}")

    scale_data_file = open(scale_data_file_path, 'rb')
    scale_data = scale_data_file.read()
    scale_data_file.close()

    scale_table = []

    if version == '4':
        scale_table = decode_scale_data(scale_data[6:])
    elif version == '5':
        scale_table = decode_scale_data(scale_data[8:])

    scale_table_file_path = Path(scale_data_file_path.parent, scale_data_file_path.name.replace(".dmp", ".json"))
    scale_table_file = open(scale_table_file_path, 'w')
    scale_table_file.write(json.dumps(scale_table, indent=4))
    scale_table_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(scale_table_file_path)

def encode(scale_table_file_path, version, timestamp_manager):
    print(f"Encoding {scale_table_file_path}")

    scale_table_file = open(scale_table_file_path, 'r')
    scale_table = json.loads(scale_table_file.read())
    scale_table_file.close()

    scale_data = encode_scale_data(scale_table)

    header = []

    if version == '4':
        header = le_encode(len(scale_data) + 6, 4) + [0x53, 0x41]
    elif version == '5':
        header = [0x53, 0x43, 0x41, 0x4c] + be_encode(len(scale_data) + 8, 4)
    
    scale_data = header + scale_data

    scale_data_file_path = Path(scale_table_file_path.parent, scale_table_file_path.name.replace(".json", ".dmp"))
    scale_data_file = open(scale_data_file_path, 'wb')
    scale_data_file.write(bytes(scale_data))
    scale_data_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(scale_table_file_path)

if __name__ == "__main__":
    if sys.argv[1] == 'decode':
        decode(Path(sys.argv[2]).resolve(), sys.argv[3], [])

    elif sys.argv[1] == 'encode':
        encode(Path(sys.argv[2]).resolve(), sys.argv[3], [])



