import sys
from PIL import Image
import xml.etree.ElementTree as et

def decode_offset_table(zplane_data, width):
    stripe_count = int(width / 8)
    index = 8
    offset_table = []

    for i in range(stripe_count):
        offset = zplane_data[index + 1] * 0x100 + zplane_data[index]
        offset_table.append(offset)
        index += 2

    offset_table.append(len(zplane_data))

    return offset_table

def decode_stripes(zplane_data, offset_table, width, height):
    stripe_count = int(width / 8)
    stripes = []

    for i in range(stripe_count):
        stripe = []
        index = offset_table[i]

        while index < offset_table[i+1]:
            count = zplane_data[index]
            index += 1

            if count & 0x80:
                count &= 0x7f
                byte = zplane_data[index]
                index += 1

                while count > 0:
                    stripe.append(byte)
                    count -= 1
            else:
                while count > 0:
                    byte = zplane_data[index]
                    index += 1
                    stripe.append(byte)
                    count -= 1
        
        while len(stripe) < height:
            stripe.append(0)

        stripes.append(stripe)
        print("Stripe " + str(i) + " decoded")
    
    return stripes

def export_stripes_to_image(stripes, width, height):
    image = Image.new(mode="RGB", size=(width, height))
    stripe_count = int(width / 8)

    for stripe in range(stripe_count):
        for row in range(height):
            mask = 0b10000000
            byte = stripes[stripe][row]

            for pixel in range(8):
                if byte & mask:
                    image.putpixel((stripe * 8 + pixel, row), (255, 255, 255, 255))
                else:
                    image.putpixel((stripe * 8 + pixel, row), (0, 0, 0, 0))
                
                mask = mask >> 1

    return image

def get_dimensions(header_path):
    header_data = et.parse(header_path)
    header_root = header_data.getroot()

    if header_path.endswith("RMHD.xml"):
        width = int(header_root[0].text)
        height = int(header_root[1].text)
        return width, height
    elif header_path.endswith("OBHD.xml"):
        width = int(header_root[2][2].text)
        height = int(header_root[2][3].text)
        return width, height
    
    print("Error: header file not recognized")
    return 0, 0


def decode(zplane_path, header_path, output_path):
    width, height = get_dimensions(header_path)

    zplane_file = open(zplane_path, 'rb')
    zplane_data = zplane_file.read()
    zplane_file.close()

    offset_table = decode_offset_table(zplane_data, width)
    stripes = decode_stripes(zplane_data, offset_table, width, height)
    image = export_stripes_to_image(stripes, width, height)
    
    image.save(output_path)
    image.show()

def get_stripes_from_image(image, stripe_count, height):
    stripes = []

    for x in range(stripe_count):
        stripe = []
        for y in range(height):
            byte = 0
            mask = 0b10000000

            for pixel_offset in range(8):
                pixel = image[x * 8 + pixel_offset, y]

                if pixel[0] > 0:
                    byte = byte | mask
                
                mask = mask >> 1
            stripe.append(byte)
        stripes.append(stripe)
    
    return stripes

def encode_stripes(stripes, height):
    encoded_stripes = []

    UNDECIDED = 0
    REPEATING = 1
    NONREPEATING = 2

    for stripe_num in range(len(stripes)):
        stripe = stripes[stripe_num]
        encoded_stripe = []

        row = 0
        byte_buffer = []
        repeat_length = 0
        sequence_type = UNDECIDED

        #print("Stripe " + str(stripe_num))

        while row < height:
            byte = stripe[row]
            row += 1

            if len(byte_buffer) > 0 and byte == byte_buffer[len(byte_buffer) - 1] and repeat_length < 127:
                if sequence_type == UNDECIDED and repeat_length == 1:
                    sequence_type = REPEATING
                elif sequence_type == NONREPEATING and repeat_length == 2:
                    nonrepeating_length = len(byte_buffer) - 2
                    encoded_stripe.append(nonrepeating_length)

                    #print("Nonrepeating sequence of length " + str(nonrepeating_length))
                    #print(hex(nonrepeating_length))

                    for i in range(nonrepeating_length):
                        encoded_stripe.append(byte_buffer[i])
                        #print(hex(byte_buffer[i]))
                    
                    #print('')

                    byte_buffer = [byte, byte]
                    sequence_type = REPEATING

                repeat_length += 1
            else:
                if sequence_type == UNDECIDED and len(byte_buffer) > 0:
                    sequence_type = NONREPEATING
                elif sequence_type == REPEATING:
                    encoded_stripe.append(repeat_length | 0b10000000)
                    encoded_stripe.append(byte_buffer[0])

                    #print("Repeating sequence of length " + str(repeat_length))
                    #print(hex(repeat_length | 0b10000000))
                    #print(hex(byte_buffer[0]))
                    #print('')

                    byte_buffer = []
                    sequence_type = UNDECIDED

                repeat_length = 1

            
            byte_buffer.append(byte)
        
        if sequence_type == REPEATING:
            encoded_stripe.append(repeat_length | 0b10000000)
            encoded_stripe.append(byte_buffer[0])

            #print("Repeating sequence of length " + str(repeat_length))
            #print(hex(repeat_length | 0b10000000))
            #print(hex(byte_buffer[0]))

        elif sequence_type == NONREPEATING or sequence_type == UNDECIDED:
            buffer_length = len(byte_buffer)
            encoded_stripe.append(buffer_length)

            #print("Nonrepeating sequence of length " + str(len(byte_buffer)))
            #print(hex(len(byte_buffer)))

            for i in range(buffer_length):
                encoded_stripe.append(byte_buffer[i])
                #print(hex(byte_buffer[i]))
        
        encoded_stripes.append(encoded_stripe)
        #print('')
    
    return encoded_stripes

def generate_offset_table(stripes):
    header_length = 8
    table_length = 2 * len(stripes)

    offset = header_length + table_length

    offset_table = []

    for stripe in stripes:
        offset_table.append(offset & 0xFF)
        offset_table.append((offset & 0xFF00) >> 8)
        offset += len(stripe)
    
    return offset_table

def generate_header(offset_table, stripes):
    header = [0x5a, 0x50, 0x30, 0x31, 0x00, 0x00]

    header_length = 8
    offset_table_length = len(offset_table)

    stripes_length = 0
    for stripe in stripes:
        stripes_length += len(stripe)
    
    full_length = header_length + offset_table_length + stripes_length

    header.append((full_length & 0xFF00) >> 8)
    header.append(full_length & 0xFF)

    return header

def encode(image_path, header_path, output_path):
    width, height = get_dimensions(header_path)
    stripe_count = int(width / 8)

    image_file = Image.open(image_path)
    image = image_file.load()

    stripes = get_stripes_from_image(image, stripe_count, height)
    encoded_stripes = encode_stripes(stripes, height)
    offset_table = generate_offset_table(encoded_stripes)
    header = generate_header(offset_table, encoded_stripes)

    zplane_data = header + offset_table
    for i in range(stripe_count):
        zplane_data += encoded_stripes[i]
    
    zplane_file = open(output_path, 'wb')
    zplane_file.write(bytes(zplane_data))
    zplane_file.close()

if __name__ == "__main__":
    if sys.argv[1] == 'e':
        encode(sys.argv[2], sys.argv[3], sys.argv[4])

    elif sys.argv[1] == 'd':
        decode(sys.argv[2], sys.argv[3], sys.argv[4])
