import os, sys, json, timestamp_manager, image_codec
from binary_functions import *
from PIL import Image
from pathlib import Path

def decode_offset_table(encoded_offset_table, character_count, base_offset):
    offset_table = []

    p = 0
    for i in range(character_count):
        offset = le_decode(encoded_offset_table[p:p+4], 4) + base_offset
        p += 4

        if offset == base_offset:
            offset = -1

        offset_table.append(offset)
    
    return offset_table

def get_color_index(palette, color):
    for i in range(len(palette)):
        if palette[i] == color:
            return i
    return 0

class Character:
    width = 8
    height = 8
    sheet_x = 0
    sheet_y = 0
    x_offset = 0
    y_offset = 0

    image = []
    
    def decode(self, encoded_data, palette, bits_per_pixel):
        self.width = encoded_data[0]
        self.height = encoded_data[1]
        self.x_offset = encoded_data[2]
        self.y_offset = encoded_data[3]

        self.image = Image.new(mode = "RGB", size = (self.width, self.height))

        bitstream = image_codec.BitstreamBE(encoded_data[4:])

        y = 0

        while y < self.height:
            x = 0

            while x < self.width:
                color = palette[bitstream.read_integer(bits_per_pixel)]

                self.image.putpixel((x, y), color)

                x += 1
            y += 1

    def encode(self, image, palette):
        mapped_colors = []
        highest_mapped_color = 0
        is_all_background_color = True

        y = 0
        while y < self.height:
            x = 0

            while x < self.width:
                color = image.getpixel((x, y))
                mapped_color = get_color_index(palette, color)

                if mapped_color > highest_mapped_color:
                    highest_mapped_color = mapped_color
                if mapped_color != 0:
                    is_all_background_color = False
                
                mapped_colors.append(mapped_color)

                x += 1
            y += 1
        
        if is_all_background_color and self.width == 8 and self.height == 8:
            return -1
        if highest_mapped_color > 3:
            print("Cannot deal with color with more than 2 bits!!" + str(highest_mapped_color))
            exit()
        
        bits_per_pixel = 2
        
        bitstream = image_codec.BitstreamBE([0])

        for i in range(len(mapped_colors)):
            bitstream.write_integer(mapped_colors[i], bits_per_pixel)
        
        encoded_data = [self.width, self.height, self.x_offset, self.y_offset]
        encoded_data += bitstream.data
        return encoded_data

    
    def serialise(self):
        return {
            "x": self.sheet_x,
            "y": self.sheet_y,
            "width": self.width,
            "height": self.height,
            "x offset": self.x_offset,
            "y offset": self.y_offset
        }
    
    def deserialise(self, serialised_data):
        self.sheet_x = serialised_data["x"]
        self.sheet_y = serialised_data["y"]
        self.width = serialised_data["width"]
        self.height = serialised_data["height"]
        self.x_offset = serialised_data["x offset"]
        self.y_offset = serialised_data["y offset"]

def decode_characters(encoded_data, offset_table, character_count, palette, bits_per_pixel):
    characters = []
    
    for i in range(character_count):
        offset = offset_table[i]
        character = Character()

        if offset == -1:
            characters.append(character)
            continue

        next_offset = 0
        
        next_valid_offset_index = i + 1
        while next_valid_offset_index < character_count and offset_table[next_valid_offset_index] == -1:
            next_valid_offset_index += 1

        if next_valid_offset_index == character_count:
            next_offset = len(encoded_data)
        else:
            next_offset = offset_table[next_valid_offset_index]
            
        character.decode(encoded_data[offset:next_offset], palette, bits_per_pixel)
        
        characters.append(character)
    
    return characters

def build_character_sheet(characters, palette):
    sheet_width = 1
    sheet_height = 2

    grid_x = 0
    grid_y = 0

    row_width = 1
    row_height = 1

    background_color = palette[0]

    for i in range(len(characters)):
        character = characters[i]

        character.sheet_x = row_width
        character.sheet_y = sheet_height
        
        row_width += character.width + 1
        if row_height < character.height + 1:
            row_height = character.height + 1
        
        grid_x += 1
        if grid_x == 16 or i == len(characters) - 1:
            grid_x = 0
            grid_y += 1

            if row_width > sheet_width:
                sheet_width = row_width
            sheet_height += row_height

            row_width = 1
            row_height = 1
    
    sheet = Image.new(mode = "RGB", size = (sheet_width, sheet_height))
    sheet.paste((0, 0, 0), (0, 0, sheet_width, sheet_height))

    for i in range(15):
        sheet.putpixel((i, 0), palette[i])

    for i in range(len(characters)):
        character = characters[i]

        if character.image == []:
            sheet.paste(background_color, (character.sheet_x, character.sheet_y, character.sheet_x + character.width, character.sheet_y + character.height))
        else:
            sheet.paste(character.image, (character.sheet_x, character.sheet_y))

    return sheet

def decode(encoded_file_path, version, timestamp_manager):
    print(f"Decoding {encoded_file_path}")

    encoded_file = open(encoded_file_path, 'rb')
    encoded_data = encoded_file.read()
    encoded_file.close()

    color_map = encoded_data[14:14+15]

    palette = []
    
    for i in range(15):
        palette.append(image_codec.ega_palette[color_map[i]])
    
    bits_per_pixel = encoded_data[29]
    font_height = encoded_data[30]

    character_count = le_decode(encoded_data[31:31+2], 2)

    offset_table = decode_offset_table(encoded_data[33:33 + (character_count * 4)], character_count, 29)
    characters = decode_characters(encoded_data, offset_table, character_count, palette, bits_per_pixel)
    
    character_sheet = build_character_sheet(characters, palette)

    serialised_characters = []
    for i in range(character_count):
        serialised_characters.append(characters[i].serialise())

    serialised_font_data = {
        "bits per pixel": bits_per_pixel,
        "font height": font_height
    }

    serialised_data = {
        "font metadata": serialised_font_data,
        "character metadata": serialised_characters
    }
        
    json_file_path = Path(encoded_file_path.parent, "_" + encoded_file_path.name.replace(".dmp", ".json"))
    json_file = open(json_file_path, 'w')
    json_file.write(json.dumps(serialised_data, indent = 4))
    json_file.close()

    character_sheet_file_path = Path(encoded_file_path.parent, "_" + encoded_file_path.name.replace(".dmp", ".png"))
    character_sheet.save(character_sheet_file_path)

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(json_file_path)
        timestamp_manager.add_timestamp(character_sheet_file_path)

def find_matching_files(file_path):
    if ".json" in file_path.name:
        image_path = Path(file_path.parent, file_path.name.replace(".json", ".png"))
        return (image_path, file_path)
    
    elif ".png" in file_path.name:
        json_path = Path(file_path.parent, file_path.name.replace(".png", ".json"))
        return (file_path, json_path)

def encode_characters(serialised_characters, character_sheet, palette):
    encoded_characters = []
    
    for i in range(len(serialised_characters)):
        character = Character()
        
        character.deserialise(serialised_characters[i])
        image = character_sheet.crop((character.sheet_x, character.sheet_y, character.sheet_x + character.width, character.sheet_y + character.height))

        encoded_character = character.encode(image, palette)

        encoded_characters.append(encoded_character)
    
    return encoded_characters

def encode_offset_table(encoded_characters, base_offset):
    encoded_offset_table = []

    p = 0

    for i in range(len(encoded_characters)):
        if encoded_characters[i] == -1:
            encoded_offset_table += le_encode(0, 4)
        else:
            encoded_offset_table += le_encode(p + base_offset, 4)
            p += len(encoded_characters[i])
    return encoded_offset_table

def encode(decoded_file_path, version, timestamp_manager):
    (character_sheet_file_path, json_file_path) = find_matching_files(decoded_file_path)

    print(f"Encoding {character_sheet_file_path}")

    json_file = open(json_file_path, 'r')
    serialised_data = json.loads(json_file.read())
    json_file.close()

    serialised_characters = serialised_data["character metadata"]

    character_count = len(serialised_characters)
    character_sheet = Image.open(character_sheet_file_path)

    palette = []
    for i in range(15):
        palette.append(character_sheet.getpixel((i, 0)))

    encoded_characters = encode_characters(serialised_characters, character_sheet, palette)

    base_offset = 4 + 4 * character_count

    encoded_data = encode_offset_table(encoded_characters, base_offset)

    for i in range(character_count):
        if encoded_characters[i] == -1:
            continue
        encoded_data += encoded_characters[i]
    
    header = [0x43, 0x48, 0x41, 0x52]

    size = be_encode(33 + len(encoded_data), 4)
    size_alt = le_encode(10 + len(encoded_data), 4)

    unknown = [0x63, 0x03]

    color_map = []
    for i in range(15):
        color_map.append(get_color_index(image_codec.ega_palette, palette[i]))
    
    bits_per_pixel = serialised_data["font metadata"]["bits per pixel"]
    font_height = serialised_data["font metadata"]["font height"]
    character_count = len(encoded_characters)

    encoded_data = header + size + size_alt + unknown + color_map + [bits_per_pixel] + [font_height] + le_encode(character_count, 2) + encoded_data

    encoded_file_path = Path(decoded_file_path.parent, character_sheet_file_path.name[1:].replace(".png", ".dmp"))
    encoded_file = open(encoded_file_path, 'wb')
    encoded_file.write(bytes(encoded_data))
    encoded_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(json_file_path)
        timestamp_manager.add_timestamp(character_sheet_file_path)


if __name__ == "__main__":
    if sys.argv[1] == 'decode':
        decode(Path(sys.argv[2]).resolve(), sys.argv[3], [])

    elif sys.argv[1] == 'encode':
        encode(Path(sys.argv[2]).resolve(), sys.argv[3], [])



