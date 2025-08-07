import sys, os, json, math, re, timestamp_manager, palette_codec
from binary_functions import *
from PIL import Image
from pathlib import Path




def decode_row(row_data, width):
    colors = []
    p = 0

    while len(colors) < width:
        byte = row_data[p]
        p += 1

        count = (byte >> 1) + 1

        if count > width:
            count = width
        
        if byte & 1:
            color = row_data[p]
            p += 1

            for i in range(count):
                colors.append(color)
        else:
            for i in range(count):
                color = row_data[p]
                p += 1

                colors.append(color)
    
    

    return colors


def decode(encoded_file_path, palette_file_path):
    encoded_file = open(encoded_file_path, 'rb')
    encoded_data = encoded_file.read()

    encoded_file.close()

    p = 10

    width = le_decode(encoded_data[p:p+2], 2)
    p += 2

    height = le_decode(encoded_data[p:p+2], 2)
    p += 2

    padding1 = le_decode(encoded_data[p:p+2], 2)
    p += 2

    padding2 = le_decode(encoded_data[p:p+2], 2)
    p += 2

    rows = []

    for y in range(height):
        row_length = le_decode(encoded_data[p:p+2], 2)
        p += 2

        row = decode_row(encoded_data[p:p+row_length], width)
        p += row_length

        rows.append(row)

        
    
    palette = palette_codec.decode(palette_file_path, '5', [], False)

    image = Image.new(mode="RGB", size=(width, height))


    for y in range(height):
        for x in range(width):
            color = rows[y][x]
            image.putpixel((x, y), palette[color])
    
    image.show()

decode(sys.argv[1], sys.argv[2])
