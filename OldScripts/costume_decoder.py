import sys, os, json
from PIL import Image

def get_room_palette(palette_data):
    palette = []
    
    offset = 8
    while offset < len(palette_data):
        color = (palette_data[offset], palette_data[offset+1], palette_data[offset+2], 255)
        palette.append(color)
        offset += 3
    return palette

def get_palette_length(costume_data):
    format_byte = costume_data[0x9]
    if format_byte & 0x1:
        return 32
    else:
        return 16

def get_costume_palette_map(costume_data):
    palette_map = []

    palette_length = get_palette_length(costume_data)
    
    offset = 10
    while offset < 10 + palette_length:
        palette_map.append(costume_data[offset])
        offset += 1
    return palette_map

def get_costume_palette(costume_data, room_palette):
    palette_map = get_costume_palette_map(costume_data)
    palette = []

    for i in range(len(palette_map)):
        palette.append(room_palette[palette_map[i]])

    return palette

def get_limb_offsets(costume_data):
    header_length = 10

    palette_length = get_palette_length(costume_data)
    
    anim_commands_offset_length = 2

    limb_offsets = []

    offset = header_length + palette_length + anim_commands_offset_length

    for i in range(16):
        limb_offset = costume_data[offset + 1] * 0x100 + costume_data[offset] + 2
        
        limb_offsets.append(limb_offset)
        offset += 2
    
    return limb_offsets

def get_anim_offsets(costume_data):
    header_length = 10

    palette_length = get_palette_length(costume_data)
    
    anim_commands_offset_length = 2

    limb_offsets_length = 32

    anim_offsets = []
    anim_count = costume_data[8] + 1

    offset = header_length + palette_length + anim_commands_offset_length + limb_offsets_length

    for i in range(anim_count):
        anim_offset = costume_data[offset + 1] * 0x100 + costume_data[offset] + 2
        anim_offsets.append(anim_offset)
        offset += 2
    
    return anim_offsets

def get_anim_commands_offset(costume_data):
    offset = 10 + get_palette_length(costume_data)

    return costume_data[offset + 1] * 0x100 + costume_data[offset] + 2

def get_anim_commands(costume_data, offset, limbs_start):
    anim_commands = []

    while offset < limbs_start:
        command = costume_data[offset]
        anim_commands.append(command)
        offset += 1
    
    return anim_commands

def get_limbs(costume_data, limb_offsets):
    limbs = []

    picts_start = limb_offsets[-1]

    for i in range(16):
        limb_offset = limb_offsets[i]

        if limb_offset == picts_start:
            break
        if i > 0 and limb_offset == limb_offsets[i-1]:
            limbs.append(0)
            continue

        limb = []

        next_limb_offset = limb_offset
        i_ = i
        while next_limb_offset == limb_offset:
            i_ += 1
            next_limb_offset = limb_offsets[i_]

        while limb_offset < next_limb_offset:
            pict_offset = costume_data[limb_offset + 1] * 0x100 + costume_data[limb_offset] + 2

            limb_offset += 2
            
            limb.append(pict_offset)
        
        limbs.append(limb)
    
    return limbs

def get_pict_lists(costume_data, limbs, picts_start):
    pict_lists = []
    pict_offsets = []

    limb_count = len(limbs)

    print(str(limbs))

    for i in range(limb_count):
        picts = []
        
        if limbs[i] == 0:
            pict_lists.append(0)
            continue

        pict_count = len(limbs[i])

        for j in range(pict_count):
            pict_offset = limbs[i][j]

            if pict_offset < picts_start:
                picts.append([0])
                continue
            
            next_pict_offset = 0
            i_ = i
            j_ = j
            pict_count_ = pict_count

            while next_pict_offset < picts_start or next_pict_offset == pict_offset:
                j_ += 1

                if limbs[i_] == 0 or j_ == len(limbs[i_]):
                    i_ += 1
                    j_ = 0
                
                if i_ == len(limbs):
                    next_pict_offset = len(costume_data)
                    continue
                
                print(str(i_))
                print(str(j_))
                if limbs[i_] != 0:
                    print(str(len(limbs[i_])))
                print('')

                if limbs[i_] != 0 and limbs[i_][j_] != 0:
                    next_pict_offset = limbs[i_][j_]

            pict = costume_data[pict_offset:next_pict_offset]

            picts.append(pict)
        
        pict_lists.append(picts)
    
    return pict_lists

def convert_pict_to_image(pict, palette):
    width = pict[1] * 0x100 + pict[0]
    height = pict[3] * 0x100 + pict[2]

    image = Image.new(mode="RGB", size=(width, height))

    offset = 12

    x = 0
    y = 0

    color_shift = 4
    color_mask = 0b00001111
    repeat_mask = 0b00001111

    large_palette = len(palette) > 16
    if large_palette:
        color_shift =  3
        color_mask = 0b00011111
        repeat_mask = 0b00000111

    while offset < len(pict):
        byte = pict[offset]
        color = (byte >> color_shift) & color_mask
        repeat_count = byte & repeat_mask

        if repeat_count == 0:
            offset += 1
            repeat_count = pict[offset]
        
        if color >= len(palette):
            color -= len(palette)

        while repeat_count > 0:
            image.putpixel((x, y), palette[color])

            repeat_count -= 1
            y += 1
            if y >= height:
                y = 0
                x += 1

                if x >= width:
                    return image
        offset += 1

    while y < height:
        image.putpixel((x, y), palette[0])
        y += 1

    return image

def get_index_in_palette(color, palette):
    for i in range(len(palette)):
        if palette[i][0] == color[0] and palette[i][1] == color[1] and palette[i][2] == color[2]:
            return i
    print("Error: color not in palette")
    return 0

def encode_image_to_pict(image, width, height, palette):
    rle = []

    color_shift = 4
    repeat_limit = 0b00001111

    large_palette = len(palette) > 16
    if large_palette:
        color_shift =  3
        repeat_limit = 0b00000111

    x = 0
    y = 0
    prev_color = image[x, y]
    repeat_count = 0

    while True:
        color = image[x, y]

        if color == prev_color and repeat_count < 255:
            repeat_count += 1
        else:
            color_index = get_index_in_palette(prev_color, palette)

            if repeat_count > repeat_limit:
                rle.append(color_index << color_shift)
                rle.append(repeat_count)
            else:
                byte = (color_index << color_shift) | repeat_count
                rle.append(byte)
            
            repeat_count = 1

        prev_color = color

        y += 1
        if y >= height:
            y = 0
            x += 1
            if x >= width:
                color_index = get_index_in_palette(prev_color, palette)

                if repeat_count > repeat_limit:
                    rle.append(color_index << color_shift)
                    rle.append(repeat_count)
                else:
                    byte = (color_index << color_shift) | repeat_count
                    rle.append(byte)
                break

    return rle

def get_format_info(costume_data):
    format_byte = costume_data[9]
    big_palette = format_byte & 0b00000001
    dont_mirror_x = format_byte & 0b10000000

    format_info = {}
    format_info["32_color_palette"] = big_palette
    format_info["mirror_x"] = 1 - dont_mirror_x
    format_info["unknown"] = format_byte & 0x7E
    
    return format_info

def get_pict_info(pict, pict_image_filename):
    if len(pict) == 1:
        return "empty pict"
    
    pict_info = {}

    width = pict[1] * 0x100 + pict[0]
    height = pict[3] * 0x100 + pict[2]

    rel_x = pict[5] * 0x100 + pict[4]
    rel_y = pict[7] * 0x100 + pict[6]

    mov_x = pict[9] * 0x100 + pict[8]
    mov_y = pict[11] * 0x100 + pict[10]

    pict_info["width"] = width
    pict_info["height"] = height
    pict_info["rel_x"] = rel_x | (-(rel_x & 0x8000))
    pict_info["rel_y"] = rel_y | (-(rel_y & 0x8000))
    pict_info["mov_x"] = mov_x | (-(mov_x & 0x8000))
    pict_info["mov_y"] = mov_y | (-(mov_y & 0x8000))
    pict_info["image_filename"] = pict_image_filename

    return pict_info

def get_anims(costume_data, anim_offsets, anim_commands_start):
    anims = []

    offset_count = len(anim_offsets)
    for i in range(offset_count):
        offset = anim_offsets[i]

        if offset <= 0x2:
            anims.append([0])
            continue

        i_ = i
        next_offset = 0
        while next_offset <= 0x2:
            if i_ == offset_count - 1:
                next_offset = anim_commands_start
            else:
                next_offset = anim_offsets[i_+1]
            i_ += 1
        
        print("Offset: " + str(offset))
        print("next offset: " + str(next_offset))

        anim = costume_data[offset:next_offset]
        anims.append(anim)
    
    return anims

def get_anim_info(anim):
    if len(anim) == 1:
        return "empty anim"
    
    anim_info = []

    limb_mask = anim[1] * 0x100 + anim[0]

    active_limbs = []

    for i in range(16):
        if limb_mask & (0b1000000000000000 >> i):
            active_limbs.append(i)
    
    offset = 2

    for i in range(len(active_limbs)):
        limb_info = {}

        limb_info["limb"] = active_limbs[i]

        start_index = anim[offset + 1] * 0x100 + anim[offset]

        if start_index == 0xFFFF:
            limb_info["disabled"] = 1
            offset += 2
        else:
            no_loop = anim[offset + 2] & 0b10000000
            sequence_length = anim[offset + 2] & 0b01111111

            limb_info["command_sequence_start"] = start_index
            limb_info["command_sequence_length"] = sequence_length
            
            if no_loop > 0:
                limb_info["looping"] = 0
            else:
                limb_info["looping"] = 1
            
            offset += 3
        
        anim_info.append(limb_info)
    
    return anim_info

def decode(costume_path, output_folder_path):
    palette_path = os.path.join(output_folder_path, "CLUT.dmp")

    costume_file = open(costume_path, 'rb')
    costume_data = costume_file.read()
    costume_file.close()

    palette_file = open(palette_path, 'rb')
    palette_data = palette_file.read()
    palette_file.close()

    room_palette = get_room_palette(palette_data)
    costume_palette = get_costume_palette(costume_data, room_palette)

    costume_info = {}
    costume_info["format"] = get_format_info(costume_data)

    costume_info["background_color"] = costume_palette[0]

    anim_commands_offset = get_anim_commands_offset(costume_data)
    limb_offsets = get_limb_offsets(costume_data)
    anim_offsets = get_anim_offsets(costume_data)

    anims = get_anims(costume_data, anim_offsets, anim_commands_offset)

    anim_infos = []
    for i in range(len(anims)):
        anim_info = {}
        anim_info["anim_index"] = i
        anim_info["limb_actions"] = get_anim_info(anims[i])
        anim_infos.append(anim_info)
    
    costume_info["anims"] = anim_infos

    anim_commands = get_anim_commands(costume_data, anim_commands_offset, limb_offsets[0])

    anim_commands_info = {}
    for i in range(len(anim_commands)):
        anim_commands_info[i] = anim_commands[i]

    costume_info["anim_commands"] = anim_commands

    limbs = get_limbs(costume_data, limb_offsets)
    pict_lists = get_pict_lists(costume_data, limbs, limb_offsets[-1])

    pict_images = []
    limb_infos = []

    for i in range(len(pict_lists)):
        limb_info = {}
        limb_info["limb_index"] = i

        pict_infos = []

        if pict_lists[i] == 0:
            limb_info = "empty limb"
        else:
            for j in range(len(pict_lists[i])):
                pict = pict_lists[i][j]
                pict_image_filename = str(i) + '_' + str(j) + ".png"

                if len(pict) > 1:
                    pict_image = convert_pict_to_image(pict, costume_palette)
                    pict_image.save(os.path.join(output_folder_path, pict_image_filename))

                pict_info = get_pict_info(pict, pict_image_filename)

                pict_images.append(pict)
                pict_infos.append(pict_info)

            limb_info["picts"] = pict_infos

        limb_infos.append(limb_info)
    
    costume_info["limbs"] = limb_infos

    pict_count = len(pict_images)
    print("Pict count: " + str(pict_count))
    
    costume_info_file = open(os.path.join(output_folder_path, "info.json"), 'w')
    costume_info_file.write(json.dumps(costume_info, indent=4))
    costume_info_file.close()

def generate_costume_palette_from_images(images, palette_length, background_color):
    palette = [background_color]

    for sublist in images:
        if sublist == 0:
            continue
            
        for image in sublist:
            if image == 0:
                continue
            
            width, height = image.size
            im = image.load()

            for y in range(height):
                for x in range(width):
                    color = im[x,y]

                    already_in_palette = False
                    for i in range(len(palette)):
                        palette_color = palette[i]

                        if palette_color[0] == color[0] and palette_color[1] == color[1] and palette_color[2] == color[2]:
                            already_in_palette = True
                            break
                    
                    if not already_in_palette:
                        #print(hex(color[0]) + " " + hex(color[1]) + " " + hex(color[2]))
                        palette.append(color)
    
    print("Palette size: " + str(len(palette)))

    while len(palette) < palette_length:
        palette.append((0, 0, 0, 255))
    
    return palette;

def get_palette_data(costume_palette, room_palette):
    palette_data = []

    for i in range(len(costume_palette)):
        costume_color = costume_palette[i]

        j = 255
        while j >= 0:
            room_color = room_palette[j]

            if costume_color[0] == room_color[0] and costume_color[1] == room_color[1] and costume_color[2] == room_color[2]:
                palette_data.append(j)
                break
            
            if j == 0:
                print("ERROR: Color " + hex(costume_color[0]) + " " + hex(costume_color[1]) + " " + hex(costume_color[2]) + " not in room palette!!")
                palette_data.append(0)
            
            j -= 1
    
    return palette_data


def get_anim_data(anim_info):
    anim_data = []

    limb_actions = anim_info["limb_actions"]

    if limb_actions == "empty anim":
        return [0]
    
    limb_mask = 0
    for limb_action in limb_actions:
        limb_mask |= (0b1000000000000000 >> limb_action["limb"])
    
    anim_data.append(limb_mask & 0xFF)
    anim_data.append((limb_mask & 0xFF00) >> 8)

    for limb_action in limb_actions:
        if "disabled" in limb_action:
            anim_data.append(0xFF)
            anim_data.append(0xFF)
            continue
        
        sequence_start = limb_action["command_sequence_start"]
        sequence_length = limb_action["command_sequence_length"]
        noloop = limb_action["looping"] == 0

        anim_data.append(sequence_start & 0xFF)
        anim_data.append((sequence_start & 0xFF00) >> 8)

        if noloop:
            sequence_length |= 0b10000000
        
        anim_data.append(sequence_length)
    
    return anim_data
    
def get_format_data(format_info):
    format_byte = 0

    format_byte |= format_info["32_color_palette"]
    format_byte |= (1 - format_info["mirror_x"]) << 7
    format_byte |= format_info["unknown"]

    return [format_byte]

def get_anim_offset_data(anim_datas, anim_data_start):
    anim_offset_data = []
    offset = anim_data_start

    for anim_data in anim_datas:
        if len(anim_data) == 1:
            anim_offset_data.append(0)
            anim_offset_data.append(0)
            continue
        
        anim_offset_data.append(offset & 0xFF)
        anim_offset_data.append((offset & 0xFF00) >> 8)
        offset += len(anim_data)
    
    return anim_offset_data

def get_commands_offset_data(anim_data_start, anim_data_length):
    commands_offset_data = []

    commands_offset = anim_data_start + anim_data_length

    commands_offset_data.append(commands_offset & 0xFF)
    commands_offset_data.append((commands_offset & 0xFF00) >> 8)

    return commands_offset_data

def get_pict_data(pict_info, pict_image, palette):
    if pict_info == "empty pict":
        return [0]
    
    pict_data = []

    width = pict_info["width"]
    height = pict_info["height"]
    rel_x = pict_info["rel_x"]
    rel_y = pict_info["rel_y"]
    mov_x = pict_info["mov_x"]
    mov_y = pict_info["mov_y"]

    if rel_x < 0:
        rel_x += 1 << 16
    if rel_y < 0:
        rel_y += 1 << 16
    if mov_x < 0:
        mov_x += 1 << 16
    if mov_y < 0:
        mov_y += 1 << 16
    
    pict_data.append(width & 0xFF)
    pict_data.append((width & 0xFF00) >> 8)
    pict_data.append(height & 0xFF)
    pict_data.append((height & 0xFF00) >> 8)
    pict_data.append(rel_x & 0xFF)
    pict_data.append((rel_x & 0xFF00) >> 8)
    pict_data.append(rel_y & 0xFF)
    pict_data.append((rel_y & 0xFF00) >> 8)
    pict_data.append(mov_x & 0xFF)
    pict_data.append((mov_x & 0xFF00) >> 8)
    pict_data.append(mov_y & 0xFF)
    pict_data.append((mov_y & 0xFF00) >> 8)

    rle_data = encode_image_to_pict(pict_image.load(), width, height, palette)

    pict_data += rle_data
    return pict_data

def get_limb_data(pict_datas, pict_data_start):
    limb_data = []
    offset = pict_data_start

    for pict_data in pict_datas:
        if len(pict_data) == 1:
            limb_data.append(0)
            limb_data.append(0)
            continue
        
        limb_data.append(offset & 0xFF)
        limb_data.append((offset & 0xFF00) >> 8)

        offset += len(pict_data)
    
    return limb_data
    
def get_limb_offset_data(limb_datas, limb_data_start):
    limb_offset_data = []
    offset = limb_data_start

    for limb_data in limb_datas:
        limb_offset_data.append(offset & 0xFF)
        limb_offset_data.append((offset & 0xFF00) >> 8)

        offset += len(limb_data)
    
    while len(limb_offset_data) < 32:
        limb_offset_data.append(offset & 0xFF)
        limb_offset_data.append((offset & 0xFF00) >> 8)
    
    return limb_offset_data

def get_header_data(body_data_length):
    header_data = [0x43, 0x4F, 0x53, 0x54, 0x00, 0x00]
    data_length = body_data_length + 8

    header_data.append((data_length & 0xFF00) >> 8)
    header_data.append(data_length & 0xFF)

    return header_data

def encode(image_folder_path, output_path):
    room_palette_path = os.path.join(image_folder_path, "CLUT.dmp")

    room_palette_file = open(room_palette_path, 'rb')
    room_palette_data = room_palette_file.read()
    room_palette_file.close()

    costume_info_file = open(os.path.join(image_folder_path, "info.json"), 'r')
    costume_info = json.loads(costume_info_file.read())
    costume_info_file.close()

    anim_count = len(costume_info["anims"])
    anim_count_data = [anim_count - 1]

    format_data = get_format_data(costume_info["format"])

    header_data_length = 6
    format_animcount_data_length = 2

    palette_data_length = 0
    if costume_info["format"]["32_color_palette"] == 1:
        palette_data_length = 32
    else:
        palette_data_length = 16
    
    commands_offset_data_length = 2
    limbs_offset_data_length = 32
    anim_offset_data_length = 2 * anim_count

    anim_infos = costume_info["anims"]
    anim_datas = []

    for anim_info in anim_infos:
        anim_datas.append(get_anim_data(anim_info))
    
    anim_data_start = header_data_length + format_animcount_data_length + palette_data_length + commands_offset_data_length + limbs_offset_data_length + anim_offset_data_length
    anim_offset_data = get_anim_offset_data(anim_datas, anim_data_start)

    anim_data_length = 0
    for anim_data in anim_datas:
        if len(anim_data) == 1:
            continue
        anim_data_length += len(anim_data)

    commands_data = costume_info["anim_commands"]
    commands_offset_data = get_commands_offset_data(anim_data_start, anim_data_length)

    limb_images = []
    for limb_info in costume_info["limbs"]:
        images = []

        for pict_info in limb_info["picts"]:
            if pict_info == "empty pict":
                images.append(0)
                continue
            
            image_path = os.path.join(image_folder_path, pict_info["image_filename"])
            image = Image.open(image_path)
            images.append(image)
        
        limb_images.append(images)

    costume_palette = generate_costume_palette_from_images(limb_images, palette_data_length, costume_info["background_color"])
    room_palette = get_room_palette(room_palette_data)
    palette_data = get_palette_data(costume_palette, room_palette)

    pict_datas = []

    limb_count = len(costume_info["limbs"])
    for i in range(limb_count):
        limb_info = costume_info["limbs"][i]
        limb_pict_datas = []

        limb_pict_count = len(limb_info["picts"])
        
        for j in range(limb_pict_count):
            pict_info = limb_info["picts"][j]
            pict_image = limb_images[i][j]

            pict_data = get_pict_data(pict_info, pict_image, costume_palette)
            limb_pict_datas.append(pict_data)
        
        pict_datas.append(limb_pict_datas)
    
    limb_data_start = anim_data_start
    for anim_data in anim_datas:
        if len(anim_data) == 1:
            continue
        limb_data_start += len(anim_data)
    limb_data_start += len(commands_data)

    pict_data_start = limb_data_start
    for limb_info in costume_info["limbs"]:
        for pict_info in limb_info["picts"]:
            pict_data_start += 2
    
    limb_datas = []
    for i in range(limb_count):

        limb_data = get_limb_data(pict_datas[i], pict_data_start)

        limb_datas.append(limb_data)

        for pict_data in pict_datas[i]:
            if len(pict_data) > 1:
                pict_data_start += len(pict_data)
    
    limb_offset_data = get_limb_offset_data(limb_datas, limb_data_start)

    body_data = anim_count_data + format_data + palette_data + commands_offset_data + limb_offset_data + anim_offset_data
    for anim_data in anim_datas:
        if len(anim_data) > 1:
            body_data += anim_data
    body_data += commands_data
    for limb_data in limb_datas:
        body_data += limb_data
    for limb in pict_datas:
        if limb == 0:
            continue

        for pict_data in limb:
            if len(pict_data) > 1:
                body_data += pict_data
    
    body_data_length = len(body_data)

    header_data = get_header_data(body_data_length)

    costume_data = header_data + body_data

    output_file = open(output_path, 'wb')
    output_file.write(bytes(costume_data))
    output_file.close()

if __name__ == "__main__":
    if sys.argv[1] == 'd':
        decode(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'e':
        encode(sys.argv[2], sys.argv[3])