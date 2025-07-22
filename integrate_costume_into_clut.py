import sys, costume_decoder

def encode_palette(palette):
    data = [0x43, 0x4c, 0x55, 0x54, 0x00, 0x00, 0x03, 0x08]

    for i in range(len(palette)):
        color = palette[i]
        data.append(color[0])
        data.append(color[1])
        data.append(color[2])
    
    return bytes(data)

def integrate_costume_into_room_palette(costume_path, original_room_palette_path, new_room_palette_path, output_path):
    costume_file = open(costume_path, 'rb')
    costume_data = costume_file.read()
    costume_file.close()

    original_room_palette_file = open(original_room_palette_path, 'rb')
    original_room_palette_data = original_room_palette_file.read()
    original_room_palette_file.close()

    new_room_palette_file = open(new_room_palette_path, 'rb')
    new_room_palette_data = new_room_palette_file.read()
    new_room_palette_file.close()

    costume_palette_map = costume_decoder.get_costume_palette_map(costume_data)
    original_room_palette = costume_decoder.get_room_palette(original_room_palette_data)
    new_room_palette = costume_decoder.get_room_palette(new_room_palette_data)

    i = 1
    while i < len(costume_palette_map):
        new_room_palette[costume_palette_map[i]] = original_room_palette[costume_palette_map[i]]
        i += 1
    
    new_room_palette_data = encode_palette(new_room_palette)

    new_room_palette_file = open(output_path, 'wb')
    new_room_palette_file.write(new_room_palette_data)
    new_room_palette_file.close()

def relocate_original_room_palette_colors(costume_path, original_room_palette_path, new_room_palette_path, output_path, relocation_start):
    costume_file = open(costume_path, 'rb')
    costume_data = costume_file.read()
    costume_file.close()

    original_room_palette_file = open(original_room_palette_path, 'rb')
    original_room_palette_data = original_room_palette_file.read()
    original_room_palette_file.close()

    new_room_palette_file = open(new_room_palette_path, 'rb')
    new_room_palette_data = new_room_palette_file.read()
    new_room_palette_file.close()

    costume_palette_map = costume_decoder.get_costume_palette_map(costume_data)
    original_room_palette = costume_decoder.get_room_palette(original_room_palette_data)
    new_room_palette = costume_decoder.get_room_palette(new_room_palette_data)

    offset = relocation_start

    i = 1
    while i < len(costume_palette_map):
        new_room_palette[offset + i] = original_room_palette[costume_palette_map[i]]
        i += 1
    
    new_room_palette_data = encode_palette(new_room_palette)

    new_room_palette_file = open(new_room_palette_path, 'wb')
    new_room_palette_file.write(new_room_palette_data)
    new_room_palette_file.close()

#relocate_original_room_palette_colors(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]))
integrate_costume_into_room_palette(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])