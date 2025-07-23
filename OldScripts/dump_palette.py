import os, sys, costume_decoder
from PIL import Image

def dump_room_palette(palette_path):
    palette_file = open(palette_path, 'rb')
    palette_data = palette_file.read()
    palette_file.close()

    room_palette = costume_decoder.get_room_palette(palette_data)

    print("Palette length: " + str(len(room_palette)))
    palette_image = Image.new(mode="RGB", size=(64,64))
    for y in range(16):
        for x in range(16):
            color = room_palette[y * 16 + x]
            print("Color " + str(y * 16 + x) + ": " + hex(color[0]) + " " + hex(color[1]) + " " + hex(color[2]))
            for ya in range(4):
                for xa in range(4):
                    palette_image.putpixel((x * 4 + xa, y * 4 + ya), color)
    palette_image.show()

def dump_costume_palette(room_palette_path, costume_path):
    room_palette_file = open(room_palette_path, 'rb')
    room_palette_data = room_palette_file.read()
    room_palette_file.close()

    costume_file = open(costume_path, 'rb')
    costume_data = costume_file.read()
    costume_file.close()

    room_palette = costume_decoder.get_room_palette(room_palette_data)
    costume_palette = costume_decoder.get_costume_palette(costume_data, room_palette)

    format_byte = costume_data[0x9]
    palette_length = 16
    if format_byte & 0x1:
        palette_length = 32

    palette_image = Image.new(mode="RGB", size=(32,int(palette_length / 2)))
    for y in range(int(palette_length / 8)):
        for x in range(8):
            color = costume_palette[y * 8 + x]
            print("Color " + str(y * 8 + x) + ": " + hex(color[0]) + " " + hex(color[1]) + " " + hex(color[2]))
            for ya in range(4):
                for xa in range(4):
                    palette_image.putpixel((x * 4 + xa, y * 4 + ya), color)
    palette_image.show()

def dump_images_palette(image_folder_path, start_index, end_index):
    images = []
    
    i = int(start_index)
    while i < int(end_index):
        image_path = os.path.join(image_folder_path, "Pict" + str(i) + ".png")
        image = Image.open(image_path)
        images.append(image)
        i += 1

    costume_palette = costume_decoder.generate_costume_palette_from_images(images)

    palette_image = Image.new(mode="RGB", size=(32,16))
    for y in range(4):
        for x in range(8):
            color = (0,0,0,255)
            color_index = y * 8 + x

            if (color_index < len(costume_palette)):
                color = costume_palette[y * 8 + x]
                
            print("Color " + str(y * 8 + x) + ": " + hex(color[0]) + " " + hex(color[1]) + " " + hex(color[2]))
            for ya in range(4):
                for xa in range(4):
                    palette_image.putpixel((x * 4 + xa, y * 4 + ya), color)
    
    palette_image.show()


if sys.argv[1] == "room":
    dump_room_palette(sys.argv[2])
elif sys.argv[1] == "costume":
    dump_costume_palette(sys.argv[2], sys.argv[3])
elif sys.argv[1] == "images":
    dump_images_palette(sys.argv[2], sys.argv[3], sys.argv[4])