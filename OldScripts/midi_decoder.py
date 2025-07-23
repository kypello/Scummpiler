import os, sys, json

def decode_header(midi_data):
    header_info = {}

    format = midi_data[0x9]
    track_count = midi_data[0xA] * 0x100 + midi_data[0xB]
    division = midi_data[0xC] * 0x100 + midi_data[0xD]

    header_info["format"] = format
    header_info["track count"] = track_count

    if division & 0x8000:
        header_info["division format"] = 1
    else:
        header_info["division format"] = 0
        header_info["ticks per quarter note"] = division & 0x7FFF
    
    return header_info

def get_track_length(midi_data, track_start):
    track_length = midi_data[track_start + 4] * 0x1000000 + midi_data[track_start + 5] * 0x10000 + midi_data[track_start + 6] * 0x100 + midi_data[track_start + 7]
    return track_length + 8

def decode_track(track_data):
    track_info = {}

    offset = 8

    running_status = 0

    event_infos = []

    while offset < len(track_data):
        event_info = {}

        event_info["delta time"] = [track_data[offset]]

        while track_data[offset] >= 0x80:
            offset += 1
            event_info["delta time"].append(track_data[offset])

        if track_data[offset+1] == 0xFF:
            event_info["class"] = "meta"
            event_info["status"] = hex(0xFF)

            event_type = track_data[offset+2]
            event_info["type"] = hex(event_type)

            event_length = track_data[offset+3]

            if event_type == 0x00:
                event_info["meaning"] = "sequence number"
            elif event_type == 0x03:
                event_info["meaning"] = "sequence/track name"
                event_info["text"] = track_data[offset+4:offset+4+event_length].decode('utf-8')
            elif event_type == 0x2F:
                event_info["meaning"] = "end of track"
            elif event_type == 0x51:
                event_info["meaning"] = "set tempo"
            elif event_type == 0x54:
                event_info["meaning"] = "smpte offset"
            elif event_type == 0x58:
                event_info["meaning"] = "time signature"
            elif event_type == 0x59:
                event_info["meaning"] = "key signature"

            event_data = []

            i = 0
            while i < event_length:
                event_data.append(hex(track_data[offset + 4 + i]))
                i += 1

            event_info["data"] = event_data

            offset += event_length + 4

        elif track_data[offset+1] == 0xF0 or track_data[offset+1] == 0xF7:
            event_info["class"] = "sysex"
            event_info["status"] = hex(track_data[offset+1])
            
            event_length = track_data[offset+2]

            event_data = []

            i = 0
            while i < event_length:
                event_data.append(hex(track_data[offset + 3 + i]))
                i += 1

            event_info["data"] = event_data

            offset += event_length + 3
        else:
            event_info["class"] = "midi"

            status = track_data[offset+1]
            if status & 0x80:
                event_info["status"] = hex(status)
                running_status = status
            else:
                event_info["status"] = "running"
                status = running_status
                offset -= 1
            

            if status & 0xF0 == 0xF0:
                event_info["type"] = "system"
                event_info["data"] = "not implemented"
                
                if status == 0xF2:
                    offset += 4
                elif status == 0xF3:
                    offset += 3

            elif status & 0x80:
                event_info["type"] = "channel"
                event_info["channel"] = status & 0x0F

                event_type = status & 0xF0

                if event_type == 0x80:
                    event_info["meaning"] = "note off"
                    event_info["note"] = track_data[offset+2]
                    event_info["velocity"] = track_data[offset+3]

                    event_info["data"] = [hex(track_data[offset+2]), hex(track_data[offset+3])]
                    offset += 4
                elif event_type == 0x90:
                    event_info["meaning"] = "note on"
                    event_info["note"] = track_data[offset+2]
                    event_info["velocity"] = track_data[offset+3]

                    event_info["data"] = [hex(track_data[offset+2]), hex(track_data[offset+3])]
                    offset += 4
                elif event_type == 0xA0:
                    event_info["meaning"] = "polyphonic key pressure"
                    event_info["note"] = track_data[offset+2]
                    event_info["pressure"] = track_data[offset+3]

                    event_info["data"] = [hex(track_data[offset+2]), hex(track_data[offset+3])]
                    offset += 4
                elif event_type == 0xB0:
                    event_info["meaning"] = "control change"
                    event_info["controller"] = track_data[offset+2]
                    event_info["value"] = track_data[offset+3]

                    event_info["data"] = [hex(track_data[offset+2]), hex(track_data[offset+3])]
                    offset += 4
                elif event_type == 0xC0:
                    event_info["meaning"] = "program change"
                    event_info["program"] = track_data[offset+2]

                    event_info["data"] = [hex(track_data[offset+2])]
                    offset += 3
                elif event_type == 0xD0:
                    event_info["meaning"] = "channel pressure"
                    event_info["pressure"] = track_data[offset+2]

                    event_info["data"] = [hex(track_data[offset+2])]
                    offset += 3
                elif event_type == 0xE0:
                    event_info["meaning"] = "pitch wheel change"
                    event_info["value"] = track_data[offset+3] * 0b1000000 + track_data[offset+2]
                    
                    event_info["data"] = [hex(track_data[offset+2]), hex(track_data[offset+3])]
                    offset += 4
            else:
                print("Huh????? status " + hex(status))
                break

        


        event_infos.append(event_info)
    
    track_info["events"] = event_infos
    return track_info


def decode(input_path):
    input_file = open(input_path, 'rb')
    midi_data = input_file.read()
    input_file.close()

    midi_info = {}

    midi_info["header"] = decode_header(midi_data)

    track_infos = []
    offset = 14

    while offset < len(midi_data):
        track_length = get_track_length(midi_data, offset)

        track_info = decode_track(midi_data[offset:offset+track_length])
        track_infos.append(track_info)
        offset += track_length
        
    
    midi_info["tracks"] = track_infos

    return midi_info

def decode_floppy(input_path):
    input_file = open(input_path, 'rb')
    midi_data = input_file.read()
    input_file.close()

    midi_info = {}

    track_infos = []
    offset = 0x90

    track_info = decode_track(midi_data[offset:len(midi_data)])
    track_infos.append(track_info)
    
    midi_info["tracks"] = track_infos

    return midi_info

def encode_header(header_info):
    header_data = [0x4D, 0x54, 0x68, 0x64, 0x00, 0x00, 0x00, 0x06, 0x00]
    header_data.append(header_info["format"])
    header_data.append(0x00)
    header_data.append(header_info["track count"])
    header_data.append((header_info["ticks per quarter note"] & 0xFF00) >> 8)
    header_data.append(header_info["ticks per quarter note"] & 0xFF)

    return header_data

def encode_event(event_info):
    event_data = []
    
    event_data += event_info["delta time"]
    
    status = event_info["status"]
    if status != "running":
        event_data.append(int(status,16))
    
    if event_info["class"] == "meta":
        event_data.append(int(event_info["type"],16))
        event_data.append(len(event_info["data"]))
    elif event_info["class"] == "sysex":
        event_data.append(len(event_info["data"]))
    
    for byte in event_info["data"]:
        event_data.append(int(byte,16))
    
    return event_data

def encode_track(track_info):
    track_data = [0x4D, 0x54, 0x72, 0x6B, 0x00, 0x00, 0x00, 0x00]

    for event in track_info["events"]:
        track_data += encode_event(event)
    
    track_length = len(track_data) - 8

    track_data[4] = (track_length & 0xFF000000) >> 24
    track_data[5] = (track_length & 0xFF0000) >> 16
    track_data[6] = (track_length & 0xFF00) >> 8
    track_data[7] = track_length & 0xFF

    return track_data

def encode(midi_info, output_path):
    midi_data = encode_header(midi_info["header"])

    for track in midi_info["tracks"]:
        midi_data += encode_track(track)
    
    output_file = open(output_path, 'wb')
    output_file.write(bytes(midi_data))
    output_file.close()

if __name__ == "__main__":
    if sys.argv[1] == 'd':
        midi = decode(sys.argv[2])

        output_file = open(sys.argv[3], 'w')
        output_file.write(json.dumps(midi, indent=4))
        output_file.close()

    elif sys.argv[1] == 'e':
        input_file = open(sys.argv[2], 'r')
        midi = json.loads(input_file.read())
        input_file.close()

        encode(midi, sys.argv[3])