import sys, os, json, math, re, timestamp_manager, palette_codec
from binary_functions import *
from PIL import Image
from pathlib import Path
import xml.etree.ElementTree as xml_garbage

HORIZONTAL = 0
VERTICAL = 1

class Stripe:
    x = 0
    y = 0

    previous_read_x = -1
    previous_read_y = -1

    height = 144
    direction = HORIZONTAL

    pixels = []

    def __init__(self, height, direction):
        self.height = height
        self.direction = direction

        self.pixels = [0] * (height * 8)
    
    def reset(self, direction):
        self.x = 0
        self.y = 0
        self.direction = direction
    
    def write_color(self, color):
        if not self.within_bounds():
            return

        self.pixels[self.y * 8 + self.x] = color

        if self.direction == HORIZONTAL:
            self.x += 1
            if self.x >= 8:
                self.x = 0
                self.y += 1
        elif self.direction == VERTICAL:
            self.y += 1
            if self.y >= self.height:
                self.y = 0
                self.x += 1
    
    def read_color(self):
        if not self.within_bounds():
            return 0

        pixel = self.pixels[self.y * 8 + self.x]

        self.previous_read_x = self.x
        self.previous_read_y = self.y

        if self.direction == HORIZONTAL:
            self.x += 1
            if self.x >= 8:
                self.x = 0
                self.y += 1
        elif self.direction == VERTICAL:
            self.y += 1
            if self.y >= self.height:
                self.y = 0
                self.x += 1
                
        return pixel
    
    def get_coordinates_of_most_recent_read(self):
        return (self.previous_read_x, self.previous_read_y)

    def read_color_at_coordinate(self, temp_x, temp_y):
        self.previous_read_x = temp_x
        self.previous_read_y = temp_y

        return self.pixels[temp_y * 8 + temp_x]

    def write_colors_from_byte(self, byte):
        i = 7
        while i >= 0:
            bit = (byte >> i) & 1
            self.write_color(bit)
            i -= 1

    def within_bounds(self):
        return (self.x < 8) and (self.y < self.height)

class Bitstream:
    data = []

    byte_index = 0
    bit_index = 0
    byte = 0

    def __init__(self, data):
        self.data = data
        self.byte = data[0]
    
    def read_bit(self):
        if self.byte_index >= len(self.data):
            return 0
        
        bit = (self.byte >> self.bit_index) & 1

        self.bit_index += 1

        if self.bit_index == 8:
            self.bit_index = 0

            self.byte_index += 1

            if self.within_bounds():
                self.byte = self.data[self.byte_index]
        
        return bit
    
    def read_integer(self, integer_size):
        value = 0

        for i in range(integer_size):
            bit = self.read_bit()
            value += bit << i
        
        return value

    
    def within_bounds(self):
        return self.byte_index < len(self.data)
    
    def write_bit(self, bit):
        self.byte = self.byte | (bit << self.bit_index)
        self.data[self.byte_index] = self.byte

        self.bit_index += 1
        if self.bit_index == 8:
            self.bit_index = 0

            self.byte_index += 1

            self.byte = 0
            self.data.append(0)
        
        
    
    def write_integer(self, value, integer_size):
        for i in range(integer_size):
            bit = (value >> i) & 1
            self.write_bit(bit)


COPY_PREVIOUS_COLUMN = 2
DITHER = 3

def decode_stripe_ega(stripe_data, height):
    stripe = Stripe(height, VERTICAL)

    p = 0

    while p < len(stripe_data):
        byte = stripe_data[p]
        p += 1

        command = (byte & 0xC0) >> 6

        if command == COPY_PREVIOUS_COLUMN:
            repeat = byte & 0x3F

            if repeat == 0:
                repeat = stripe_data[p]
                p += 1

            for i in range(repeat):
                previous_column = 8 * stripe.y + stripe.x - 1
                stripe.write_color(stripe.pixels[previous_column])

        elif command == DITHER:
            repeat = byte & 0x3F

            colors = stripe_data[p]
            p += 1

            if repeat == 0:
                repeat = stripe_data[p]
                p += 1

            color_a = colors & 0x0F
            color_b = (colors & 0xF0) >> 4

            dither_pattern = False

            for i in range(repeat):
                if dither_pattern:
                    stripe.write_color(color_a)
                else:
                    stripe.write_color(color_b)
                dither_pattern = not dither_pattern

        else:
            repeat = (byte & 0xF0) >> 4
            color = byte & 0x0F

            if repeat == 0:
                repeat = stripe_data[p]
                p += 1
            
            for i in range(repeat):
                stripe.write_color(color)
    
    return stripe

S_WRITE_COLOR = 0
S_READ_COMMAND = 1
S_SET_COLOR = 2
S_SHIFT_COLOR = 3
S_REPEAT_COLOR = 4

def decode_stripe_vga(stripe_data, height):
    key = stripe_data[0]

    palette_index_size = key % 10
    direction = math.floor(key / 10) % 2
    alt_algorithm = key >= 50

    stripe = Stripe(height, direction)

    if key == 1:
        # rare uncompressed case which shows up occasionally
        stripe.pixels = stripe_data[1:]
        return stripe

    color = stripe_data[1]
    stripe.write_color(color)
    color_shift = -1


    state = S_WRITE_COLOR

    bitstream = Bitstream(stripe_data[2:])

    while bitstream.within_bounds():
        if state == S_WRITE_COLOR:
            bit = bitstream.read_bit()

            if bit == 0:
                stripe.write_color(color)
            elif bit == 1:
                state = S_READ_COMMAND
        
        elif state == S_READ_COMMAND:
            bit = bitstream.read_bit()

            if bit == 0:
                state = S_SET_COLOR
            elif bit == 1:
                state = S_SHIFT_COLOR
        
        elif state == S_SET_COLOR:
            color_shift = -1
            color = bitstream.read_integer(palette_index_size)
            stripe.write_color(color)

            state = S_WRITE_COLOR
        
        elif state == S_SHIFT_COLOR and not alt_algorithm:
            bit = bitstream.read_bit()

            if bit == 1:
                color_shift *= -1

            color += color_shift
            stripe.write_color(color)

            state = S_WRITE_COLOR
        
        elif state == S_SHIFT_COLOR and alt_algorithm:
            command = bitstream.read_integer(3) - 4

            if command == 0:
                state = S_REPEAT_COLOR
            else:
                color_shift = command
                color += color_shift
                stripe.write_color(color)

                state = S_WRITE_COLOR
        
        elif state == S_REPEAT_COLOR and alt_algorithm:
            repeat_count = bitstream.read_integer(8)

            for i in range(repeat_count):
                stripe.write_color(color)
            
            state = S_WRITE_COLOR

    return stripe


def decode_stripe_zplane(stripe_data, height):
    stripe = Stripe(height, HORIZONTAL)

    p = 0

    while p < len(stripe_data):
        count = stripe_data[p]
        p += 1

        if count & 0x80:
            count = count & 0x7f

            byte = 0
            if p < len(stripe_data):
                byte = stripe_data[p]
                p += 1

            while count > 0:
                stripe.write_colors_from_byte(byte)
                count -= 1
        else:
            while count > 0:
                byte = stripe_data[p]
                p += 1

                stripe.write_colors_from_byte(byte)
                count -= 1
    
    while stripe.within_bounds():
        stripe.write_color(0)
    
    return stripe

def decode_stripes(encoded_data, video_type, offset_table, width, height):
    stripe_count = int(width / 8)
    stripes = []

    for i in range(stripe_count):
        encoded_stripe = encoded_data[offset_table[i]:offset_table[i+1]]
        
        stripe = []
        if video_type == 'ega':
            stripe = decode_stripe_ega(encoded_stripe, height)
        elif video_type == 'vga':
            stripe = decode_stripe_vga(encoded_stripe, height)
        elif video_type == 'zplane':
            stripe = decode_stripe_zplane(encoded_stripe, height)

        stripes.append(stripe)
    
    return stripes

word_size_table = {
    'ega': 2,
    'vga': 4,
    'zplane': 2
}

def decode_offset_table(encoded_data, width, word_size, base_offset):
    stripe_count = int(width / 8)
    p = 0
    offset_table = []

    for i in range(stripe_count):
        offset = le_decode(encoded_data[p:p+word_size], word_size) - base_offset
        
        offset_table.append(offset)
        p += word_size

    offset_table.append(len(encoded_data))

    return offset_table

def composite_image_from_stripes(stripes, palette, width, height):
    width = len(stripes) * 8

    image = Image.new(mode = "RGB", size = (width, height))
    is_blank = True

    stripe_count = len(stripes)

    for i in range(stripe_count):
        for y in range(height):
            for x in range(8):
                palette_index = stripes[i].pixels[y * 8 + x]

                image.putpixel((i * 8 + x, y), palette[palette_index])

                if palette_index != 0:
                    is_blank = False
    
    return (image, is_blank)


ega_palette = [
    (0x00, 0x00, 0x00), (0x00, 0x00, 0xaa),
    (0x00, 0xaa, 0x00), (0x00, 0xaa, 0xaa),
    (0xaa, 0x00, 0x00), (0xaa, 0x00, 0xaa),
    (0xaa, 0x55, 0x00), (0xaa, 0xaa, 0xaa),
    (0x55, 0x55, 0x55), (0x55, 0x55, 0xff),
    (0x55, 0xff, 0x55), (0x55, 0xff, 0xff),
    (0xff, 0x55, 0x55), (0xff, 0x55, 0xff),
    (0xff, 0xff, 0x55), (0xff, 0xff, 0xff),
]

ega_palette_catppuccin = [
    (0x30, 0x34, 0x36), (0x54, 0x6e, 0xa9),
    (0x65, 0x97, 0x60), (0x5d, 0xa2, 0xaf),
    (0xc0, 0x58, 0x5a), (0xca, 0x9e, 0xe6),
    (0xef, 0x9f, 0x76), (0x94, 0x9c, 0xbb),
    (0x62, 0x68, 0x80), (0x8c, 0xaa, 0xee),
    (0xa6, 0xe3, 0xa1), (0x99, 0xd1, 0xdb),
    (0xe7, 0x82, 0x84), (0xf4, 0xb8, 0xe4),
    (0xe5, 0xc8, 0x90), (0xf2, 0xd5, 0xcf)
]




zplane_palette = [(0x00, 0x00, 0x00), (0xff, 0xff, 0xff)]

def decode_subimage(encoded_data, version, video_type, width, height, base_offset, palette=[]):
    if video_type == 'ega':
        palette = ega_palette
    elif video_type == 'zplane':
        palette = zplane_palette
    
    word_size = word_size_table[video_type]

    offset_table = decode_offset_table(encoded_data, width, word_size, base_offset)

    stripes = decode_stripes(encoded_data, video_type, offset_table, width, height)

    (image, is_blank) = composite_image_from_stripes(stripes, palette, width, height)

    return (image, is_blank)

def get_image_dimensions(image_path, version, image_type):
    header_path = ""

    if image_type == 'object':
        if version == '4':
            header_path = Path(image_path.parents[0], "OBHD.xml")
        elif version == '5':
            header_path = Path(image_path.parents[1], "OBHD.xml")
    elif image_type == 'room':
        if version == '4':
            header_path = Path(image_path.parents[0], "HD.xml")
        elif version == '5':
            header_path = Path(image_path.parents[2], "RMHD.xml")
    
    xml_tree = xml_garbage.parse(header_path)
    xml_root = xml_tree.getroot()

    width, height = 0, 0

    if image_type == 'object':
        if version == '4':
            width = int(xml_root.find("code").find("width").text) * 8
            height = int(xml_root.find("code").find("height").text)

        elif version == '5':
            width = int(xml_root.find("image").find("width").text)
            height = int(xml_root.find("image").find("height").text)

    elif image_type == 'room':
        width = int(xml_root.find("width").text)
        height = int(xml_root.find("height").text)
    
    return (width, height)

def get_object_id(image_path):
    header_path = Path(image_path.parent, "OBHD.xml")

    xml_tree = xml_garbage.parse(header_path)
    xml_root = xml_tree.getroot()

    object_id = int(xml_root.find("id").text)
    return object_id

def get_palette(image_path, version, image_type):
    palette_path = []

    if image_type == 'object':
        if version == '4':
            palette_path = Path(image_path.parents[2], "PA.dmp")
        elif version == '5':
            palette_path = Path(image_path.parents[3], "CLUT.dmp")
    elif image_type == 'room':
        if version == '4':
            palette_path = Path(image_path.parents[0], "PA.dmp")
        elif version == '5':
            palette_path = Path(image_path.parents[2], "CLUT.dmp")
    
    palette = palette_codec.decode(palette_path, version, [], False)
    return palette

def identify_image_type(image_path, version):
    if version == '4':
        if image_path.name.startswith("OI."):
            return 'object'
        elif image_path.name.startswith("BM."):
            return 'room'
    elif version == '5':
        if image_path.parents[2].name == "objects":
            return 'object'
        elif image_path.parents[1].name == "RMIM":
            return 'room'

def flatten_file_path(initial_path, levels_to_go_up):
    file_name = initial_path.name

    for i in range(levels_to_go_up):
        file_name = initial_path.parents[i].name + "+" + file_name
    
    flattened_path = Path(initial_path.parents[levels_to_go_up], '_' + file_name)
    return flattened_path

def unflatten_file_path(flattened_path):
    unflattened_path = Path(flattened_path.parent)

    path_parts = flattened_path.name[1:].split('+')

    for path_part in path_parts:
        unflattened_path = Path(unflattened_path, path_part)

    return unflattened_path

def decode(encoded_file_path, version, timestamp_manager, video_type, palette=[]):
    print(f"Decoding {encoded_file_path}")

    encoded_file = open(encoded_file_path, 'rb')
    encoded_data = encoded_file.read()
    encoded_file.close()

    image_type = identify_image_type(encoded_file_path, version)

    (width, height) = get_image_dimensions(encoded_file_path, version, image_type)

    if video_type == 'vga' and palette == []:
        palette = get_palette(encoded_file_path, version, image_type)
    
    header_size = 8

    if version == '4':
        if image_type == 'room':
            header_size = 6
        
        word_size = word_size_table[video_type]
        
        if len(encoded_data) <= header_size + 4:
            return
        
        image_start = header_size + word_size
        image_end = le_decode(encoded_data[header_size:header_size + word_size], word_size) + header_size

        (image, is_blank) = decode_subimage(encoded_data[image_start:image_end], version, video_type, width, height, word_size, palette)
        
        image_file_path = Path(encoded_file_path.parent, encoded_file_path.name.replace(".dmp", "_image.png"))

        if image_type == 'object':
            image_file_path = flatten_file_path(image_file_path, 1)
        
        image.save(image_file_path)

        if timestamp_manager != []:
            timestamp_manager.add_timestamp(image_file_path)
        
        if len(encoded_data) <= image_end + 4:
            return
        
        (zplane, is_blank) = decode_subimage(encoded_data[image_end+2:], version, 'zplane', width, height, 2)
        
        if is_blank:
            return
        
        zplane_file_path = Path(image_file_path.parent, image_file_path.name.replace("_image", "_zplane"))

        zplane.save(zplane_file_path)

        if timestamp_manager != []:
            timestamp_manager.add_timestamp(zplane_file_path)

    elif version == '5':
        (image, is_blank) = decode_subimage(encoded_data[header_size:], version, video_type, width, height, header_size, palette)

        if is_blank:
            return

        image_file_path = Path(encoded_file_path.parent, encoded_file_path.name.replace(".dmp", ".png"))
        image_file_path = flatten_file_path(image_file_path, 2)
        image.save(image_file_path)

        if timestamp_manager != []:
            timestamp_manager.add_timestamp(image_file_path)




def get_palette_index(color, palette):
    for i in range(len(palette)):
        if palette[i][0] == color[0] and palette[i][1] == color[1] and palette[i][2] == color[2]:
            return i
    
    print("Error: Color not in palette")
    exit()

def split_image_to_stripes(image, palette):
    stripes = []
    width, height = image.size

    stripe_count = int(width / 8)

    for i in range(stripe_count):
        stripe = Stripe(height, HORIZONTAL)

        for y in range(height):
            for x in range(8):
                color = image.getpixel((i * 8 + x, y))

                palette_index = get_palette_index(color, palette)

                stripe.write_color(palette_index)
        
        stripes.append(stripe)
    
    return stripes


UNDECIDED = 0
REPEATING = 1
NONREPEATING = 2

def encode_stripe_zplane(stripe):
    stripe.reset(HORIZONTAL)

    bitmask_stripe = []

    for y in range(stripe.height):
        row_bitmask = 0

        for x in range(8):
            row_bitmask = row_bitmask << 1
            row_bitmask |= stripe.read_color()
        
        bitmask_stripe.append(row_bitmask)
    
    encoded_stripe = []
    byte_buffer = []
    sequence_length = 0
    sequence_type = UNDECIDED

    for byte in bitmask_stripe:
        if sequence_type == UNDECIDED:
            if sequence_length == 1 and byte_buffer[0] == byte:
                sequence_type = REPEATING
            elif sequence_length == 1 and byte_buffer[0] != byte:
                sequence_type = NONREPEATING

        elif sequence_type == REPEATING:
            if byte != byte_buffer[0] or sequence_length == 0x7f:
                encoded_stripe.append(sequence_length | 0x80)
                encoded_stripe.append(byte_buffer[0])

                byte_buffer = []
                sequence_length = 0
                sequence_type = UNDECIDED
        
        elif sequence_type == NONREPEATING:
            if byte == byte_buffer[sequence_length - 1]:
                encoded_stripe.append(sequence_length - 1)
                encoded_stripe += byte_buffer[:sequence_length - 1]

                byte_buffer = [byte]
                sequence_length = 1
                sequence_type = REPEATING

            elif sequence_length == 0x7f:
                encoded_stripe.append(sequence_length)
                encoded_stripe += byte_buffer

                byte_buffer = []
                sequence_length = 0
                sequence_type = UNDECIDED
        
        byte_buffer.append(byte)
        sequence_length += 1
    
    if sequence_type == REPEATING:
        encoded_stripe.append(sequence_length | 0x80)
        encoded_stripe.append(byte_buffer[0])
    elif sequence_type == NONREPEATING or sequence_type == UNDECIDED:
        encoded_stripe.append(sequence_length)
        encoded_stripe += byte_buffer
    
    return encoded_stripe


CAN_REPEAT = 1
CAN_DITHER = 2
CAN_COPY = 4

def encode_ega_sequence(buffer, possible_sequences):
    repeat_count = len(buffer)

    encoded_sequence = []

    if possible_sequences & CAN_COPY:
        if repeat_count > 0b00111111:
            encoded_sequence = [0x80, repeat_count]
        else:
            encoded_sequence = [0x80 | repeat_count]
    
    elif possible_sequences & CAN_REPEAT:
        if repeat_count > 0b0111:
            encoded_sequence = [buffer[0], repeat_count]
        else:
            encoded_sequence = [(repeat_count << 4) | buffer[0]]
    
    elif possible_sequences & CAN_DITHER:
        color_a = buffer[0]
        color_b = buffer[1]

        if repeat_count > 0b00111111:
            encoded_sequence = [0xc0, (color_a << 4) | color_b, repeat_count]
        else:
            encoded_sequence = [0xc0 | repeat_count, (color_a << 4) | color_b]
    
    return encoded_sequence


def encode_stripe_ega(stripe):
    stripe.reset(VERTICAL)

    encoded_stripe = []

    possible_sequences_on_previous_byte = CAN_REPEAT | CAN_DITHER | CAN_COPY
    previous_byte_matched_previous_column = False
    buffer = []

    while stripe.within_bounds():
        (x, y) = (stripe.x, stripe.y)
        color = stripe.read_color()

        possible_sequences = possible_sequences_on_previous_byte

        color_matches_previous_column = x > 0 and color == stripe.read_color_at_coordinate(x - 1, y)

        if possible_sequences & CAN_REPEAT:
            if len(buffer) > 0 and color != buffer[len(buffer) - 1]:
                possible_sequences &= ~CAN_REPEAT
        
        if possible_sequences & CAN_DITHER:
            if len(buffer) >= 2 and color != buffer[len(buffer) - 2]:
                possible_sequences &= ~CAN_DITHER
        
        if possible_sequences & CAN_COPY:
            if not color_matches_previous_column:
                possible_sequences &= ~CAN_COPY
        

        if possible_sequences == 0 or len(buffer) == 0xff:
            encoded_sequence = []

            if len(buffer) == 2 and possible_sequences_on_previous_byte == CAN_DITHER:
                # absolutely disgusting

                encoded_sequence = [0x10 | buffer[0]]
                buffer = [buffer[1]]

                if buffer[0] == color:
                    possible_sequences = CAN_REPEAT
                else:
                    possible_sequences = CAN_DITHER
                
                if color_matches_previous_column and previous_byte_matched_previous_column:
                    possible_sequences |= CAN_COPY

            else:
                encoded_sequence = encode_ega_sequence(buffer, possible_sequences_on_previous_byte)
                buffer = []

                possible_sequences = CAN_REPEAT | CAN_DITHER

                if color_matches_previous_column:
                    possible_sequences |= CAN_COPY
            
            encoded_stripe += encoded_sequence
            
            
        
        buffer.append(color)
        possible_sequences_on_previous_byte = possible_sequences
        previous_byte_matched_previous_column = color_matches_previous_column
    
    encoded_sequence = encode_ega_sequence(buffer, possible_sequences_on_previous_byte)
    encoded_stripe += encoded_sequence
    
    return encoded_stripe


def encode_stripe_vga(stripe, alt_algorithm, direction):
    palette_index_size = 8

    stripe.reset(direction)
    current_color = stripe.read_color()

    key = 10 + palette_index_size
    if direction == HORIZONTAL:
        key += 10
    if alt_algorithm:
        key += 40

    bitstream = Bitstream([0])

    bitstream.write_integer(key, 8)
    bitstream.write_integer(current_color, 8)

    repeat_count = 0
    color_shift = -1

    while stripe.within_bounds():
        color = stripe.read_color()

        if color == current_color:
            repeat_count += 1
        else:
            if alt_algorithm and repeat_count > 13 and repeat_count < 32:
                bitstream.write_bit(1)
                bitstream.write_bit(1)
                bitstream.write_integer(0b100, 3)

                bitstream.write_integer(repeat_count, 5) #seems to only be able to handle 5 bits?

                bitstream.write_bit(0)
                bitstream.write_bit(0)
                bitstream.write_bit(0)
            else:
                for i in range(repeat_count):
                    bitstream.write_bit(0)

            repeat_count = 0
            bitstream.write_bit(1)

            difference = color - current_color

            if alt_algorithm and difference >= -4 and difference < 4:
                bitstream.write_bit(1)
                bitstream.write_integer(difference + 4, 3)
            elif (not alt_algorithm) and abs(difference) == 1:
                bitstream.write_bit(1)

                if difference == color_shift:
                    bitstream.write_bit(0)
                else:
                    bitstream.write_bit(1)
                    color_shift = difference
            else:
                bitstream.write_bit(0)
                bitstream.write_integer(color, palette_index_size)
                color_shift = -1

            current_color = color

    if alt_algorithm and repeat_count > 13 and repeat_count < 32:
        bitstream.write_bit(1)
        bitstream.write_bit(1)
        bitstream.write_integer(0b100, 3)

        bitstream.write_integer(repeat_count, 5)
    
        bitstream.write_bit(0)
        bitstream.write_bit(0)
        bitstream.write_bit(0)
    else:
        for i in range(repeat_count):
            bitstream.write_bit(0)

    return bitstream.data

def encode_stripe_vga_optimally(stripe):
    attempts = []

    #attempts.append(encode_stripe_vga(stripe, True, VERTICAL)) #this variation might not be valid in-engine, remove if so
    attempts.append(encode_stripe_vga(stripe, True, HORIZONTAL))
    attempts.append(encode_stripe_vga(stripe, False, VERTICAL))
    attempts.append(encode_stripe_vga(stripe, False, HORIZONTAL))

    smallest_size = 1000000
    smallest_index = -1

    for i in range(3):
        attempt_size = len(attempts[i])

        if attempt_size < smallest_size or smallest_index == -1:
            smallest_size = attempt_size
            smallest_index = i
    
    return attempts[smallest_index]


def encode_stripes(stripes, video_type):
    encoded_stripes = []

    for stripe in stripes:

        encoded_stripe = []

        if video_type == 'ega':
            encoded_stripe = encode_stripe_ega(stripe)
        elif video_type == 'vga':
            encoded_stripe = encode_stripe_vga_optimally(stripe)
        elif video_type == 'zplane':
            encoded_stripe = encode_stripe_zplane(stripe)
        
        encoded_stripes.append(encoded_stripe)
    
    return encoded_stripes

def pack_stripes_with_offsets(encoded_stripes, word_size, base_offset):
    encoded_subimage = []
    offset_table = []

    stripe_count = len(encoded_stripes)
    offset_table_length = word_size * stripe_count

    offset = base_offset + offset_table_length

    for encoded_stripe in encoded_stripes:
        offset_table += le_encode(offset, word_size)
        offset += len(encoded_stripe)

        encoded_subimage += encoded_stripe
    
    encoded_subimage = offset_table + encoded_subimage

    return encoded_subimage

def encode_subimage(image, version, video_type, base_offset, palette=[]):

    if video_type == 'ega':
        palette = ega_palette
    elif video_type == 'zplane':
        palette = zplane_palette

    stripes = split_image_to_stripes(image, palette)

    encoded_stripes = encode_stripes(stripes, video_type)

    word_size = word_size_table[video_type]
    encoded_subimage = pack_stripes_with_offsets(encoded_stripes, word_size, base_offset)

    return encoded_subimage

def generate_blank_image(width, height):
    image = Image.new(mode = "RGB", size = (width, height))

    for y in range(height):
        for x in range(width):
            image.putpixel((x, y), (0, 0, 0))
    
    return image

def find_matching_files_v4(file_path):
    if "_image" in file_path.name:
        zplane_path = Path(file_path.parent, file_path.name.replace("_image", "_zplane"))
        return (file_path, zplane_path)
    
    elif "_zplane" in file_path.name:
        image_path = Path(file_path.parent, file_path.name.replace("_zplane", "_image"))
        return (image_path, file_path)


room_image_header_v4 = [0x42, 0x4d]
object_image_header_v4 = [0x4f, 0x49]
image_header_v5 = [0x53, 0x4d, 0x41, 0x50]
zplane_header_v5 = [0x5a, 0x50, 0x30, 0x31]

def encode(image_file_path, version, timestamp_manager, video_type, palette=[]):
    encoded_image = []

    encoded_file_path = Path(image_file_path.parent, image_file_path.name.replace("_image", "").replace("_zplane", "").replace(".png", ".dmp"))
    encoded_file_path = unflatten_file_path(encoded_file_path)

    image_type = identify_image_type(encoded_file_path, version)

    if video_type == 'vga' and palette == []:
        palette = get_palette(encoded_file_path, version, image_type)

    if version == '4':
        (image_file_path, zplane_file_path) = find_matching_files_v4(image_file_path)

        if zplane_file_path.exists():
            print(f"Encoding {image_file_path} and {zplane_file_path}")
        else:
            print(f"Encoding {image_file_path}")
        
        image = Image.open(image_file_path)
        word_size = word_size_table[video_type]
        encoded_smap = encode_subimage(image, version, video_type, word_size, palette)

        zplane = []
        if zplane_file_path.exists():
            zplane = Image.open(zplane_file_path)
        else:
            zplane = generate_blank_image(image.width, image.height)
        
        encoded_zplane = encode_subimage(zplane, version, 'zplane', 2)

        header = []
        if image_type == 'object':
            object_id = get_object_id(encoded_file_path)
            header = object_image_header_v4 + le_encode(object_id, 2)
        elif image_type == 'room':
            header = room_image_header_v4
        
        smap_length = word_size + len(encoded_smap)
        zplane_length = 2 + len(encoded_zplane)

        encoded_image_length = 4 + len(header) + smap_length + zplane_length

        encoded_image = le_encode(encoded_image_length, 4) + header + le_encode(smap_length, word_size) + encoded_smap + le_encode(zplane_length, 2) + encoded_zplane

        if timestamp_manager != []:
            timestamp_manager.add_timestamp(image_file_path)
            if zplane_file_path.exists():
                timestamp_manager.add_timestamp(zplane_file_path)

    elif version == '5':
        print(f"Encoding {image_file_path}")

        image = Image.open(image_file_path)

        encoded_subimage = encode_subimage(image, version, video_type, 8, palette)

        header = []
        if video_type == 'vga':
            header = image_header_v5
        elif video_type == 'zplane':
            header = zplane_header_v5

            #assuming zplane count never exceeds 1 digit
            zplane_number = re.search(r"ZP(\d+)\.png", image_file_path.name)

            if zplane_number:
                header[3] = 0x30 | int(zplane_number.group(1))
        
        encoded_image_length = 8 + len(encoded_subimage)

        encoded_image = header + be_encode(encoded_image_length, 4) + encoded_subimage

        if timestamp_manager != []:
            timestamp_manager.add_timestamp(image_file_path)

    encoded_file = open(encoded_file_path, 'wb')
    encoded_file.write(bytes(encoded_image))
    encoded_file.close()


if __name__ == "__main__":
    if sys.argv[1] == "decode":
        decode(Path(sys.argv[2]).resolve(), sys.argv[3], [], sys.argv[4])

    elif sys.argv[1] == "encode":
        encode(Path(sys.argv[2]).resolve(), sys.argv[3], [], sys.argv[4])


