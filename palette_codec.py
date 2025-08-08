import os, sys, timestamp_manager
from PIL import Image
from pathlib import Path

def save_to_png(palette, png_path):
    palette_image = Image.new(mode="RGB", size=(16,16))

    for y in range(16):
        for x in range(16):
            color = palette[y * 16 + x]
            palette_image.putpixel((x, y), color)
    
    palette_image.save(png_path)

def decode(encoded_file_path, version, timestamp_manager, save_to_file=True):
    if save_to_file:
        print(f"Decoding {encoded_file_path}")

    encoded_file = open(encoded_file_path, 'rb')
    encoded_data = encoded_file.read()
    encoded_file.close()

    palette = []
    
    p = 0
    if version == '4':
        p = 8

    elif version == '5':
        p = 8

    while p < len(encoded_data):
        color = (encoded_data[p], encoded_data[p+1], encoded_data[p+2], 255)
        palette.append(color)
        p += 3
    
    if save_to_file:
        decoded_file_path = Path(encoded_file_path.parent, encoded_file_path.name.replace(".dmp", ".png"))
        save_to_png(palette, decoded_file_path)

        if timestamp_manager != []:
            timestamp_manager.add_timestamp(decoded_file_path)

    return palette

def get_palette_from_png(png_file_path):
    palette = []

    image_file = Image.open(png_file_path)
    palette_image = image_file.load()

    for y in range(16):
        for x in range(16):
            color = palette_image[x, y]
            palette.append(color)
    
    return palette

def encode(png_file_path, version, timestamp_manager, save_to_file=True):
    palette = get_palette_from_png(png_file_path)

    if not save_to_file:
        return palette
    
    print(f"Encoding {png_file_path}")

    encoded_data = []

    if version == "4":
        encoded_data = [0x08, 0x03, 0x00, 0x00, 0x50, 0x41, 0x00, 0x03]
    elif version == "5":
        encoded_data = [0x43, 0x4c, 0x55, 0x54, 0x00, 0x00, 0x03, 0x08]
    else:
        print("Version (4 or 5) must be specified.")
        exit()

    for color in palette:
        encoded_data.append(color[0])
        encoded_data.append(color[1])
        encoded_data.append(color[2])

    encoded_file_path = Path(png_file_path.parent, png_file_path.name.replace(".png", ".dmp"))

    encoded_file = open(encoded_file_path, 'wb')
    encoded_file.write(bytes(encoded_data))
    encoded_file.close()

    if timestamp_manager != []:
        timestamp_manager.add_timestamp(png_file_path)
    
    return palette

if __name__ == "__main__":
    if sys.argv[1] == 'decode':
        decode(Path(sys.argv[2]).resolve(), sys.argv[3], [], True)

    elif sys.argv[1] == 'encode':
        encode(Path(sys.argv[2]).resolve(), sys.argv[3], [], True)
