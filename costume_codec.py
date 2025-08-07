import sys, os, json, math, re, timestamp_manager, palette_codec, image_codec
from binary_functions import *
from PIL import Image
from pathlib import Path

def decode_offset_table(encoded_offset_table, offset_count, base_offset):
    offset_table = []

    p = 0
    for i in range(offset_count):
        offset = le_decode(encoded_offset_table[p:p+2], 2) + base_offset
        p += 2

        offset_table.append(offset)
    
    return offset_table

def find_lowest_offset(offset_table):
    lowest_offset = -1

    for i in range(len(offset_table)):
        offset = offset_table[i]

        if offset == 2:
            continue
        
        if lowest_offset == -1 or offset < lowest_offset:
            lowest_offset = offset
    
    return lowest_offset

def get_ordered_offsets(offset_table):
    ordered_offsets = []

    for i in range(len(offset_table)):
        offset = offset_table[i]

        if offset <= 2:
            continue
        
        if offset in ordered_offsets:
            continue
        
        j = 0
        while j < len(ordered_offsets):
            if offset < ordered_offsets[j]:
                break

            j += 1
        
        ordered_offsets.insert(j, offset)
    
    return ordered_offsets

def encode_offset_table(chunks, start_offset, index_map, use_chunks_end_for_null_pointer):
    null_pointer = 0

    if use_chunks_end_for_null_pointer:
        null_pointer = start_offset
        for chunk in chunks:
            null_pointer += len(chunk)

    encoded_offset_table = []

    for entry in index_map:
        if entry == -1:
            encoded_offset_table += le_encode(null_pointer, 2)
        else:
            offset = start_offset
            for i in range(entry):
                offset += len(chunks[i])
            
            encoded_offset_table += le_encode(offset, 2)
    
    return encoded_offset_table

def get_palette_index_prioritising_global_colors(color, palette):
    i = 0xc0
    while i < len(palette):
        if palette[i][0] == color[0] and palette[i][1] == color[1] and palette[i][2] == color[2]:
            return i
        i += 1
    
    i = 0
    while i < len(palette):
        if palette[i][0] == color[0] and palette[i][1] == color[1] and palette[i][2] == color[2]:
            return i
        i += 1
    
    print("Error: Color not in palette")
    exit()

class Pict:
    image = []

    width = 0
    height = 0
    relative_x = 0
    relative_y = 0
    move_x = 0
    move_y = 0

    spritesheet_x = 0
    spritesheet_y = 0

    redirect_limb = 0
    redirect_pict = 0

    image_data = []

    limb_numer = 0
    frame_number = 0

    def __init__(self):
        self.image = []
        self.image_data = []
        self.name = ""
    
    def decode(self, encoded_pict, limb_number, frame_number, allow_redirectable_picts, palette):
        p = 0

        self.width = le_decode(encoded_pict[p:p+2], 2)
        p += 2

        self.height = le_decode(encoded_pict[p:p+2], 2)
        p += 2

        self.relative_x = signed_decode(le_decode(encoded_pict[p:p+2], 2))
        p += 2

        self.relative_y = signed_decode(le_decode(encoded_pict[p:p+2], 2))
        p += 2

        self.move_x = signed_decode(le_decode(encoded_pict[p:p+2], 2))
        p += 2

        self.move_y = signed_decode(le_decode(encoded_pict[p:p+2], 2))
        p += 2

        if allow_redirectable_picts:
            self.redirect_limb = encoded_pict[p]
            p += 1

            self.redirect_pict = encoded_pict[p]
            p += 1
        
        self.image_data = encoded_pict[p:]

        self.limb_number = limb_number
        self.frame_number = frame_number

        if len(self.image_data) > 0:
            self.decode_image(palette)
    
    def decode_image(self, palette):
        p = 0
        x = 0
        y = 0

        self.image = Image.new(mode = "RGB", size = (self.width, self.height))

        color_mask = 0xf0
        color_shift = 4
        repeat_mask = 0x0f

        if len(palette) == 32:
            color_mask = 0xf8
            color_shift = 3
            repeat_mask = 0x07

        while x < self.width:
            byte = self.image_data[p]
            p += 1

            color = (byte & color_mask) >> color_shift
            repeat = byte & repeat_mask

            if repeat == 0:
                repeat = self.image_data[p]
                p += 1
            
            for i in range(repeat):
                self.image.putpixel((x, y), palette[color])

                y += 1
                if y == self.height:
                    y = 0
                    x += 1

                    if x == self.width:
                        break

    def encode(self, palette, allow_redirectable_picts):
        encoded_pict = []

        encoded_pict += le_encode(self.width, 2)
        encoded_pict += le_encode(self.height, 2)
        encoded_pict += le_encode(signed_encode(self.relative_x), 2)
        encoded_pict += le_encode(signed_encode(self.relative_y), 2)
        encoded_pict += le_encode(signed_encode(self.move_x), 2)
        encoded_pict += le_encode(signed_encode(self.move_y), 2)

        if allow_redirectable_picts:
            encoded_pict.append(self.redirect_limb)
            encoded_pict.append(self.redirect_pict)
        
        color_shift = 4
        repeat_mask = 0x0f

        if len(palette) == 32:
            color_shift = 3
            repeat_mask = 0x07

        x = 0
        y = 0

        while x < self.width:
            repeat_count = 0
            repeating_color = self.image.getpixel((x, y))
            
            while x < self.width and repeat_count < 0xff:
                color = self.image.getpixel((x, y))

                if color != repeating_color:
                    break
                else:
                    repeat_count += 1

                    y += 1
                    if y >= self.height:
                        y = 0
                        x += 1
            
            palette_index = image_codec.get_palette_index(repeating_color, palette)

            if repeat_count > repeat_mask:
                encoded_pict.append(palette_index << color_shift)
                encoded_pict.append(repeat_count)
            else:
                encoded_pict.append((palette_index << color_shift) | repeat_count)

        return encoded_pict

    def serialise(self):
        return {
            "Spritesheet X": self.spritesheet_x,
            "Spritesheet Y": self.spritesheet_y,
            "Width": self.width,
            "Height": self.height,
            "Relative X": self.relative_x,
            "Relative Y": self.relative_y,
            "Move X": self.move_x,
            "Move Y": self.move_y,
            "Redirect limb": self.redirect_limb,
            "Redirect pict": self.redirect_pict 
        }
    
    def deserialise(self, serialised_pict, spritesheet):
        self.spritesheet_x = serialised_pict["Spritesheet X"]
        self.spritesheet_y = serialised_pict["Spritesheet Y"]
        self.width = serialised_pict["Width"]
        self.height = serialised_pict["Height"]
        self.relative_x = serialised_pict["Relative X"]
        self.relative_y = serialised_pict["Relative Y"]
        self.move_x = serialised_pict["Move X"]
        self.move_y = serialised_pict["Move Y"]
        self.redirect_limb = serialised_pict["Redirect limb"]
        self.redirect_pict = serialised_pict["Redirect pict"]

        spritesheet_section = (self.spritesheet_x, self.spritesheet_y, self.spritesheet_x + self.width, self.spritesheet_y + self.height)
        self.image = spritesheet.crop(spritesheet_section)

class Limb:
    offset_table = []

    pict_index_map = []

    def __init__(self):
        self.offset_table = []
        self.pict_index_map = []
    
    def decode(self, encoded_limb, base_offset):
        self.offset_table = decode_offset_table(encoded_limb, int(len(encoded_limb) / 2), base_offset)
        self.pict_index_map = []
    
    def serialise(self):
        return self.pict_index_map
    
    def deserialise(self, serialised_limb):
        self.pict_index_map = serialised_limb

class Subanimation:
    limb_index = 0
    disable_limb = False

    command_sequence_start = 0
    command_sequence_length = 0
    loop = False

    def __init__(self):
        return
    
    def decode(self, encoded_subanimation, limb_index):
        self.limb_index = limb_index

        if encoded_subanimation[0] == 0xff and encoded_subanimation[1] == 0xff:
            self.disable_limb = True
        
        else:
            self.command_sequence_start = le_decode(encoded_subanimation[0:2], 2)

            end_byte = encoded_subanimation[2]
            
            self.command_sequence_length = end_byte & 0x7f
            self.loop = not (end_byte & 0x80)
    
    def encode(self):
        if self.disable_limb:
            return [0xff, 0xff]
        else:
            encoded_subanim = le_encode(self.command_sequence_start, 2)
            end_byte = self.command_sequence_length

            if not self.loop:
                end_byte |= 0x80
            
            encoded_subanim.append(end_byte)

            return encoded_subanim



    def serialise(self):
        return {
            "Limb": self.limb_index,
            "Disabled": self.disable_limb,
            "Command sequence start": self.command_sequence_start,
            "Command sequence length": self.command_sequence_length,
            "Loop": self.loop
        }
    
    def deserialise(self, serialised_subanim):
        self.limb_index = serialised_subanim["Limb"]
        self.disable_limb = serialised_subanim["Disabled"]
        self.command_sequence_start = serialised_subanim["Command sequence start"]
        self.command_sequence_length = serialised_subanim["Command sequence length"]
        self.loop = serialised_subanim["Loop"]

class Animation:
    subanims = []

    def __init__(self):
        self.subanims = []
    
    def decode(self, encoded_animation):
        limb_mask = le_decode(encoded_animation[0:2], 2)
        p = 2

        self.subanims = []

        for i in range(16):
            if limb_mask & (0x8000 >> i):
                subanimation = []
                subanim_length = 3

                disable_limb_check = le_decode(encoded_animation[p:p+2], 2)

                if disable_limb_check == 0xffff:
                    subanim_length -= 1

                subanimation = Subanimation()
                subanimation.decode(encoded_animation[p:p+subanim_length], i)
                p += subanim_length
                
                self.subanims.append(subanimation)
    
    def encode(self):
        encoded_anim = []

        limb_mask = 0

        for subanim in self.subanims:
            limb_mask |= 0x8000 >> subanim.limb_index
            encoded_subanim = subanim.encode()

            encoded_anim += encoded_subanim
        
        encoded_anim = le_encode(limb_mask, 2) + encoded_anim
        return encoded_anim

    def serialise(self, anim_number):
        serialised_subanims = []

        for subanim in self.subanims:
            serialised_subanims.append(subanim.serialise())
        
        return {
            "Animation number": anim_number,
            "Subanimations": serialised_subanims
        }
    
    def deserialise(self, serialised_anim):
        for serialised_subanim in serialised_anim["Subanimations"]:
            subanim = Subanimation()
            subanim.deserialise(serialised_subanim)
            self.subanims.append(subanim)


class Settings:
    anim_count = 0

    format_byte = 0
    palette_size = 0
    mirror_west_anims = False
    allow_redirectable_picts = False

    def __init__(self):
        self.anim_count = 0
        self.format_byte = 0
        self.palette_size = 0
        self.mirror_west_anims = False
        self.allow_redirectable_picts = False
    
    def decode(self, encoded_settings):
        self.anim_count = encoded_settings[0] + 1

        self.format_byte = encoded_settings[1]

        self.mirror_west_anims = not (self.format_byte & 0x40)
        self.palette_size = 16 + 16 * (self.format_byte & 1)
        self.allow_redirectable_picts = (self.format_byte & 0x7e) == 0x60

        if self.allow_redirectable_picts:
            print("This costume uses redirectable picts which i HAVEN'T implemented!!!")
    
    def encode(self):
        return [self.anim_count - 1, self.format_byte]

    def serialise(self):
        return {
            "Anim count": self.anim_count,
            "Format byte": self.format_byte,
            "Palette size": self.palette_size,
            "Mirror west anims": self.mirror_west_anims,
            "Allow redirectable picts": self.allow_redirectable_picts
        }
    
    def deserialise(self, serialised_settings):
        self.anim_count = serialised_settings["Anim count"]
        self.format_byte = serialised_settings["Format byte"]
        self.palette_size = serialised_settings["Palette size"]
        self.mirror_west_anims = serialised_settings["Mirror west anims"]
        self.allow_redirectable_picts = serialised_settings["Allow redirectable picts"]

class Costume:
    settings = []
    commands = []

    anim_index_map = []
    anims = []

    limb_index_map = []
    limbs = []

    picts = []

    palette = []


    def __init__(self):
        self.settings = []
        self.commands = []

        self.anim_index_map = []
        self.anims = []

        self.limb_index_map = []
        self.limbs = []

        self.picts = []

        self.palette = []
        
    def decode(self, encoded_costume, version, room_palette):
        base_offset = 0
        header_length = 6
        if version == '5':
            base_offset = 2
            header_length = 8

        p = header_length

        self.settings = Settings()
        self.settings.decode(encoded_costume[p:p+2])
        p += 2

        palette_map = encoded_costume[p:p + self.settings.palette_size]
        p += self.settings.palette_size

        self.palette = []
        for i in range(len(palette_map)):
            self.palette.append(room_palette[palette_map[i]])

        commands_offset = le_decode(encoded_costume[p:p+2], 2) + base_offset
        p += 2

        limb_offset_table = decode_offset_table(encoded_costume[p:p+32], 16, base_offset)
        p += 32

        anim_offset_table_length = 2 * self.settings.anim_count

        anim_offset_table = decode_offset_table(encoded_costume[p:p + anim_offset_table_length], self.settings.anim_count, base_offset)
        p += anim_offset_table_length


        self.decode_animations(encoded_costume, anim_offset_table, commands_offset)

        limbs_start = find_lowest_offset(limb_offset_table)
        self.commands = encoded_costume[commands_offset:limbs_start]

        self.decode_limbs(encoded_costume, limb_offset_table, base_offset)

        self.decode_picts(encoded_costume)        
    
    def save_palette(self, costume_folder_path):
        width = 8

        height = 2
        if self.settings.palette_size == 32:
            height = 4

        image = Image.new(mode = "RGB", size = (width, height))

        for y in range(height):
            for x in range(width):
                color = self.palette[y * width + x]
                image.putpixel((x, y), color)
        
        image_path = Path(costume_folder_path, "palette.png")
        image.save(image_path)

    def decode_animations(self, encoded_costume, offset_table, anims_end):
        ordered_anim_offsets = get_ordered_offsets(offset_table)

        self.anims = []
        self.anim_index_map = []

        offset_to_anim_index_map = {}

        for i in range(self.settings.anim_count):
            anim_offset = offset_table[i]

            if anim_offset <= 2:
                self.anim_index_map.append(-1)

            elif anim_offset in offset_to_anim_index_map:
                self.anim_index_map.append(offset_to_anim_index_map[anim_offset])
            
            else:
                offset_to_anim_index_map[anim_offset] = len(self.anims)
                self.anim_index_map.append(len(self.anims))

                next_anim_offset = 0

                if i == self.settings.anim_count - 1:
                    next_anim_offset = anims_end
                else:
                    for j in range(len(ordered_anim_offsets)):
                        if ordered_anim_offsets[j] == anim_offset:
                            if j == len(ordered_anim_offsets) - 1:
                                next_anim_offset = len(encoded_costume)
                            else:
                                next_anim_offset = ordered_anim_offsets[j + 1]
                            break


                encoded_animation = encoded_costume[anim_offset:next_anim_offset]

                animation = Animation()
                animation.decode(encoded_animation)
                self.anims.append(animation)


    def decode_limbs(self, encoded_costume, offset_table, base_offset):
        ordered_limb_offsets = get_ordered_offsets(offset_table)

        self.limbs = []
        self.limb_index_map = []

        offset_to_limb_index_map = {}

        first_pict_offset = -1

        for i in range(16):
            limb_offset = offset_table[i]

            if limb_offset <= 2:
                self.limb_index_map.append(-1)

            elif limb_offset in offset_to_limb_index_map:
                self.limb_index_map.append(offset_to_limb_index_map[limb_offset])
            
            else:
                next_limb_offset = 0

                for j in range(len(ordered_limb_offsets)):
                    if ordered_limb_offsets[j] == limb_offset:
                        if j == len(ordered_limb_offsets) - 1:
                            next_limb_offset = first_pict_offset
                        else:
                            next_limb_offset = ordered_limb_offsets[j + 1]
                        break
                
                encoded_limb = encoded_costume[limb_offset:next_limb_offset]

                if len(encoded_limb) == 0:
                    offset_to_limb_index_map[limb_offset] = -1
                    self.limb_index_map.append(-1)

                else:
                    offset_to_limb_index_map[limb_offset] = len(self.limbs)
                    self.limb_index_map.append(len(self.limbs))

                    limb = Limb()
                    limb.decode(encoded_limb, base_offset)
                    self.limbs.append(limb)

                    lowest_offset_within_limb = find_lowest_offset(limb.offset_table)
                    if first_pict_offset == -1 or lowest_offset_within_limb < first_pict_offset:
                        first_pict_offset = lowest_offset_within_limb


    def decode_picts(self, encoded_costume):
        all_pict_offsets = []
        for limb in self.limbs:
            all_pict_offsets += limb.offset_table

        ordered_pict_offsets = get_ordered_offsets(all_pict_offsets)

        limb_count = len(self.limbs)
        offset_to_pict_index_map = {}

        

        for i in range(limb_count):
            limb = self.limbs[i]
            frame_number = 0

            for j in range(len(limb.offset_table)):
                pict_offset = limb.offset_table[j]

                if pict_offset <= 2:
                    limb.pict_index_map.append(-1)
                
                elif pict_offset in offset_to_pict_index_map:
                    limb.pict_index_map.append(offset_to_pict_index_map[pict_offset])

                else:
                    offset_to_pict_index_map[pict_offset] = len(self.picts)
                    limb.pict_index_map.append(len(self.picts))

                    next_pict_offset = 0
                    for k in range(len(ordered_pict_offsets)):
                        if ordered_pict_offsets[k] == pict_offset:
                            if k == len(ordered_pict_offsets) - 1:
                                next_pict_offset = len(encoded_costume)
                            else:
                                next_pict_offset = ordered_pict_offsets[k + 1]
                            break

                    pict = Pict()
                    pict.decode(encoded_costume[pict_offset:next_pict_offset], i, frame_number, self.settings.allow_redirectable_picts, self.palette)
                    self.picts.append(pict)
                    frame_number += 1



    def encode_anims(self):
        encoded_anims = []

        for anim in self.anims:
            encoded_anim = anim.encode()
            encoded_anims.append(encoded_anim)
        
        return encoded_anims

    def encode_picts(self):
        encoded_picts = []

        for pict in self.picts:
            encoded_pict = pict.encode(self.palette, self.settings.allow_redirectable_picts)
            encoded_picts.append(encoded_pict)
        
        return encoded_picts

    def encode_limbs(self, encoded_picts, encoded_picts_start, base_offset):
        encoded_limbs = []

        for limb in self.limbs:
            encoded_limb = encode_offset_table(encoded_picts, encoded_picts_start - base_offset, limb.pict_index_map, False)
            encoded_limbs.append(encoded_limb)
        
        return encoded_limbs


    def encode(self, version, room_palette):
        base_offset = 0
        header_length = 6
        if version == '5':
            base_offset = 2
            header_length = 8
        
        encoded_settings = self.settings.encode()

        palette_map = []
        for color in self.palette:
            if len(room_palette) == 16:
                palette_index = image_codec.get_palette_index(color, room_palette)
                palette_map.append(palette_index)
            else:
                palette_index = get_palette_index_prioritising_global_colors(color, room_palette)
                palette_map.append(palette_index)

        encoded_anims = self.encode_anims()
        encoded_picts = self.encode_picts()

        encoded_anims_length = 0
        for encoded_anim in encoded_anims:
            encoded_anims_length += len(encoded_anim)

        encoded_limbs_length = 0
        for limb in self.limbs:
            encoded_limbs_length += len(limb.pict_index_map) * 2
        
        encoded_picts_length = 0
        for encoded_pict in encoded_picts:
            encoded_picts_length += len(encoded_pict)

        encoded_anims_start = header_length + 2 + self.settings.palette_size + 2 + 32 + self.settings.anim_count * 2
        commands_start = encoded_anims_start + encoded_anims_length
        encoded_limbs_start = commands_start + len(self.commands)
        encoded_picts_start = encoded_limbs_start + encoded_limbs_length

        encoded_limbs = self.encode_limbs(encoded_picts, encoded_picts_start, base_offset)        

        encoded_limb_offset_table = encode_offset_table(encoded_limbs, encoded_limbs_start - base_offset, self.limb_index_map, True)
        encoded_anim_offset_table = encode_offset_table(encoded_anims, encoded_anims_start - base_offset, self.anim_index_map, False)
        
        encoded_commands_offset = le_encode(commands_start - base_offset, 2)

        encoded_costume_length = encoded_picts_start + encoded_picts_length

        header = []
        if version == '4':
            header = le_encode(encoded_costume_length, 4) + [0x43, 0x4f]
        elif version == '5':
            header = [0x43, 0x4f, 0x53, 0x54] + be_encode(encoded_costume_length, 4)
        
        encoded_costume = header + encoded_settings + palette_map + encoded_commands_offset + encoded_limb_offset_table + encoded_anim_offset_table
        
        for encoded_anim in encoded_anims:
            encoded_costume += encoded_anim
        
        encoded_costume += self.commands

        for encoded_limb in encoded_limbs:
            encoded_costume += encoded_limb
        
        for encoded_pict in encoded_picts:
            encoded_costume += encoded_pict
        
        return encoded_costume

    def serialise(self):
        serialised_settings = self.settings.serialise()
        serialised_commands = []
        serialised_anims = []
        serialised_limbs = []
        serialised_picts = []

        for command in self.commands:
            serialised_commands.append(int(command))
        for i in range(len(self.anims)):
            serialised_anims.append(self.anims[i].serialise(i))
        for limb in self.limbs:
            serialised_limbs.append(limb.serialise())
        for pict in self.picts:
            serialised_picts.append(pict.serialise())
        
        serialised_data = {
            "Settings": serialised_settings,

            "Commands sequence": serialised_commands,

            "Animation index map": self.anim_index_map,
            "Animations": serialised_anims,
            "Limb index map": self.limb_index_map,
            "Limbs": serialised_limbs,
            "Picts": serialised_picts
        }

        return serialised_data

    def deserialise(self, serialised_costume, spritesheet):
        self.settings = Settings()
        self.settings.deserialise(serialised_costume["Settings"])

        self.commands = serialised_costume["Commands sequence"]

        self.anim_index_map = serialised_costume["Animation index map"]
        for serialised_anim in serialised_costume["Animations"]:
            anim = Animation()
            anim.deserialise(serialised_anim)
            self.anims.append(anim)
        
        self.limb_index_map = serialised_costume["Limb index map"]
        for serialised_limb in serialised_costume["Limbs"]:
            limb = Limb()
            limb.deserialise(serialised_limb)
            self.limbs.append(limb)
        
        for serialised_pict in serialised_costume["Picts"]:
            pict = Pict()
            pict.deserialise(serialised_pict, spritesheet)
            self.picts.append(pict)
        
        for i in range(self.settings.palette_size):
            color = spritesheet.getpixel((i, 0))
            self.palette.append(color)


def build_spritesheet(picts, palette):
    palette_size = len(palette)
    background_color = palette[0]

    spritesheet_width = palette_size
    spritesheet_height = 9

    max_spritesheet_width = 640

    i = 0
    current_limb_number = 0

    while i < len(picts):
        row_width = 0
        row_height = 0

        while i < len(picts):
            pict = picts[i]

            if pict.limb_number > current_limb_number or row_width + pict.width > max_spritesheet_width:
                current_limb_number = pict.limb_number
                
                break
            
            else:
                pict.spritesheet_x = row_width
                pict.spritesheet_y = spritesheet_height

                row_width += pict.width

                if row_width < max_spritesheet_width:
                    row_width += 1

                if pict.height > row_height:
                    row_height = pict.height
                
                i += 1

        spritesheet_height += row_height + 1

        if row_width > spritesheet_width:
            spritesheet_width = row_width

        
    spritesheet = Image.new(mode = "RGB", size = (spritesheet_width, spritesheet_height))
    spritesheet.paste(palette[0], (0, 0, spritesheet_width, spritesheet_height))

    for i in range(palette_size):
        spritesheet.putpixel((i, 0), palette[i])

    for pict in picts:
        spritesheet.paste(pict.image, (pict.spritesheet_x, pict.spritesheet_y))

    return spritesheet

def get_room_palette(encoded_costume_path, version):
    room_palette_path = ""
    if version == '4':
        room_palette_path = Path(encoded_costume_path.parent, "RO", "PA.dmp")
    elif version == '5':
        room_palette_path = Path(encoded_costume_path.parent, "ROOM", "CLUT.dmp")
    
    room_palette = palette_codec.decode(room_palette_path, version, [], False)
    return room_palette

def decode(encoded_costume_path, version, timestamp_manager, video_type, room_palette=[]):
    print(f"Decoding {encoded_costume_path}")

    encoded_costume_path = Path(encoded_costume_path).resolve()

    encoded_file = open(encoded_costume_path, 'rb')
    encoded_costume = encoded_file.read()
    encoded_file.close()

    if video_type == 'ega':
        room_palette = image_codec.ega_palette
    elif video_type == 'vga' and room_palette == []:
        room_palette = get_room_palette(encoded_costume_path, version)

    costume = Costume()
    costume.decode(encoded_costume, version, room_palette)

    spritesheet = build_spritesheet(costume.picts, costume.palette)
    serialised_data = costume.serialise()

    json_file_path = Path(encoded_costume_path.parent, "_" + encoded_costume_path.name.replace(".dmp", "_animdata.json"))
    json_file = open(json_file_path, 'w')
    json_file.write(json.dumps(serialised_data, indent = 4))
    json_file.close()

    spritesheet_file_path = Path(encoded_costume_path.parent, "_" + encoded_costume_path.name.replace(".dmp", "_spritesheet.png"))
    spritesheet.save(spritesheet_file_path)

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(json_file_path)
        timestamp_manager.add_timestamp(spritesheet_file_path)


def find_matching_files(file_path):
    if "_animdata.json" in file_path.name:
        spritesheet_path = Path(file_path.parent, file_path.name.replace("_animdata.json", "_spritesheet.png"))
        return (file_path, spritesheet_path)
    
    elif "_spritesheet.png" in file_path.name:
        json_path = Path(file_path.parent, file_path.name.replace("_spritesheet.png", "_animdata.json"))
        return (json_path, file_path)



def encode(decoded_costume_path, version, timestamp_manager, video_type, room_palette=[]):
    print(f"Encoding {decoded_costume_path}")

    decoded_costume_path = Path(decoded_costume_path).resolve()

    (json_file_path, spritesheet_file_path) = find_matching_files(decoded_costume_path)

    spritesheet = Image.open(spritesheet_file_path)

    json_file = open(json_file_path, 'r')
    serialised_costume = json.loads(json_file.read())
    json_file.close()

    if video_type == 'ega':
        room_palette = image_codec.ega_palette
    elif video_type == 'vga' and room_palette == []:
        room_palette = get_room_palette(decoded_costume_path, version)

    costume = Costume()

    costume.deserialise(serialised_costume, spritesheet)

    encoded_costume = costume.encode(version, room_palette)

    encoded_costume_path = Path(json_file_path.parent, json_file_path.name[1:].replace("_animdata.json", ".dmp"))
    encoded_costume_file = open(encoded_costume_path, 'wb')
    encoded_costume_file.write(bytes(encoded_costume))
    encoded_costume_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(json_file_path)
        timestamp_manager.add_timestamp(spritesheet_file_path)


if __name__ == "__main__":
    if sys.argv[1] == 'decode':
        decode(sys.argv[2], sys.argv[3], [], sys.argv[4])
    
    elif sys.argv[1] == 'encode':
        encode(sys.argv[2], sys.argv[3], [], sys.argv[4])










