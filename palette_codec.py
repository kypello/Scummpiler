import os, sys
from PIL import Image

def get_clut_data(clut_path):
    clut_file = open(clut_path, 'rb')
    clut_data = clut_file.read()
    clut_file.close()

    return clut_data

def decode(clut_data):
    palette = []
    
    offset = 8
    while offset < len(clut_data):
        color = (clut_data[offset], clut_data[offset+1], clut_data[offset+2], 255)
        palette.append(color)
        offset += 3
    
    return palette

def save_to_png(palette, png_path):
    palette_image = Image.new(mode="RGB", size=(16,16))

    for y in range(16):
        for x in range(16):
            color = palette[y * 16 + x]
            palette_image.putpixel((x, y), color)
    
    palette_image.save(png_path)

def clut_to_png(clut_path):
    png_path = clut_path.replace(".dmp", ".png")

    clut_data = get_clut_data(clut_path)
    palette = decode(clut_data)
    save_to_png(palette, png_path)

    print("Decoded " + clut_path + " to " + png_path)



def get_palette_from_png(png_path):
    palette = []

    image_file = Image.open(png_path)
    palette_image = image_file.load()

    for y in range(16):
        for x in range(16):
            color = palette_image[x, y]
            palette.append(color)
    
    return palette

def encode(palette, version):
    clut_data = []

    if version == "4":
        clut_data = [0x08, 0x03, 0x00, 0x00, 0x50, 0x41, 0x00, 0x03]
    elif version == "5":
        clut_data = [0x43, 0x4c, 0x55, 0x54, 0x00, 0x00, 0x03, 0x08]
    else:
        print("Version (4 or 5) must be specified.")
        exit()

    for color in palette:
        clut_data.append(color[0])
        clut_data.append(color[1])
        clut_data.append(color[2])

    return clut_data

def save_to_clut(clut_data, clut_path):
    clut_file = open(clut_path, 'wb')
    clut_file.write(bytes(clut_data))
    clut_file.close()

def png_to_clut(png_path, version):
    clut_path = png_path.replace(".png", ".dmp")

    palette = get_palette_from_png(png_path)
    clut_data = encode(palette, version)
    save_to_clut(clut_data, clut_path)

    print("Encoded " + png_path + " to " + clut_path)


if __name__ == "__main__":
    if sys.argv[1] == 'e':
        png_to_clut(sys.argv[2], sys.argv[3])

    if sys.argv[1] == 'd':
        clut_to_png(sys.argv[2])