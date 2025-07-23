import os, sys, json, midi_decoder

event_templates_path = os.path.join("PythonScripts", "Resources", "midi_event_templates.json")
event_templates_file = open(event_templates_path, 'r')
event_templates = json.loads(event_templates_file.read())
event_templates_file.close()

instruments_path = os.path.join("PythonScripts", "Resources", "instruments.json")
instruments_file = open(instruments_path, 'r')
instruments_raw_data = json.loads(instruments_file.read())
instruments_file.close()

master_instrument_map_path = os.path.join("PythonScripts", "Resources", "master_instrument_map.json")
master_instrument_map_file = open(master_instrument_map_path, 'r')
master_instrument_map = json.loads(master_instrument_map_file.read())
master_instrument_map_file.close()

def build_header(midi_header):
    header = midi_header

    header["format"] = 2
    header["track count"] = 1

    return header

def get_delta_time(event):
    delta_time = 0

    i = len(event["delta time"]) - 1
    
    while i >= 0:
        if i == len(event["delta time"]) - 1:
            delta_time += event["delta time"][i]
        else:
            power = len(event["delta time"]) - 1 - i
            delta_time += pow(128, power) * (event["delta time"][i] & 0x7F)

        i -= 1

    return delta_time

def get_status(event, running_status):
    if event["status"] == "running":
        return running_status
    else:
        return event["status"]

def set_delta_time(event, delta_time):
    power = 0

    delta_time_bytes = []
    
    while pow(0x80, power+1) <= delta_time:
        power += 1
    
    while power >= 0:
        byte = int(delta_time / pow(0x80, power))
        if power > 0:
            byte += 0x80
        
        delta_time_bytes.append(byte)
        delta_time = delta_time % pow(0x80, power)
        power -= 1

    event["delta time"] = delta_time_bytes
    return event

def set_status(event, status):
    event["status"] = status
    return event

def set_channel(event, channel):
    status = int(event["status"],16)
    event["status"] = hex((status & 0xF0) + channel)
    event["channel"] = channel
    return event

def events_remaining(event_pointers, tracks):
    for i in range(len(tracks)):
        if event_pointers[i] < len(tracks[i]):
            return True
    return False

def set_up_test_instrument(start_point, track):
    instrument = event_templates["test instrument"].copy()
    instrument["data"] = ["0x7d", "0x10", hex(track), "0x1"]
    instrument["data"] += instruments_raw_data[str(start_point + track)]

    return instrument

def find_tempo(tracks):
    for track in tracks:
        for event in track["events"]:
            if event["class"] == "meta" and event["type"] == "0x51":
                return event["data"]

def build_track(midi_tracks, instrument_map):
    adlib_track = {}
    events = []
    
    midi_tracks_to_be_included = []
    for i in range(len(midi_tracks)):
        if i > 15:
            break
        midi_tracks_to_be_included.append(i)
    
    track_count = len(midi_tracks_to_be_included)
    print(str(track_count))

    #instruments = ["whistle", "clarinet", "marimba", "click", "soft drum", "xylophone", "metronome", "guitar", "otamatone", "bass guitar"]
    #instruments = ["flute", "trumpet", "clarinet", "otamatone", "metronome", "soft drum", "steel drum", "click", "bass guitar", "marimba", "xylophone"]
    #instruments = ["steel drum", "click", "metronome", "soft drum", "otamatone", "guitar", "flute", "bass guitar"]


    events.append(event_templates["track name"])
    events.append(event_templates["smpte"])
    events.append(event_templates["time signature"])

    tempo_event = event_templates["tempo"]
    tempo_event["data"] = find_tempo(midi_tracks)
    events.append(tempo_event)

    events.append(event_templates["imuse init"])    

    for i in range(track_count):
        imuse_part_event = event_templates["imuse part"].copy()
        imuse_part_event["data"] = imuse_part_event["data"].copy()
        imuse_part_event["data"][2] = hex(i)
        events.append(imuse_part_event)
    
    for i in range(track_count):
        imuse_instrument_event = event_templates["instrument"].copy()
        imuse_instrument_event["data"] = ["0x7d", "0x10", hex(i), "0x1"]

        imuse_instrument_event["data"] += instruments_raw_data[master_instrument_map[instrument_map[str(i)]["instrument"]]]
        events.append(imuse_instrument_event)
    
    for i in range(track_count):
        volume_change_event = event_templates["volume change"].copy()
        volume_change_event["data"] = volume_change_event["data"].copy()
        volume_change_event["data"][1] = hex(instrument_map[str(i)]["volume"])
        volume_change_event = set_channel(volume_change_event, i)
        events.append(volume_change_event)
    
    running_status = 0
    delta_time_buffer = 0
    
    event_pointers = []
    og_tracks = []
    event_buffers = []
    running_statuses = []
    for i in range(track_count):
        event_pointers.append(0)
        og_tracks.append(midi_tracks[midi_tracks_to_be_included[i]]["events"])
        event_buffers.append(og_tracks[i][0])
        running_statuses.append("")
    
    total_delta_time = 0

    while events_remaining(event_pointers, og_tracks):
        shortest_delta_time = 9999999
        next_event = 0

        for i in range(track_count):
            if event_pointers[i] >= len(og_tracks[i]):
                continue
            
            event = event_buffers[i]
            delta_time = get_delta_time(event)

            if delta_time < shortest_delta_time:
                shortest_delta_time = delta_time
                next_event = i
        
        event = event_buffers[next_event]

        if event["class"] == "midi" and event["type"] == "channel" and (event["meaning"] == "note on" or event["meaning"] == "note off"):
            status = get_status(event, running_statuses[next_event])
            running_statuses[next_event] = status

            event = set_status(event, status)
            event = set_channel(event, next_event)
            event = set_delta_time(event, shortest_delta_time)
            event["data"][0] = hex(int(event["data"][0],16) + instrument_map[str(next_event)]["octave shift"] * 12)
            events.append(event)
            total_delta_time += shortest_delta_time

            event_pointers[next_event] += 1
            if event_pointers[next_event] < len(og_tracks[next_event]):
                event_buffers[next_event] = og_tracks[next_event][event_pointers[next_event]]

            for i in range(track_count):
                if i == next_event:
                    continue
                
                other_event = event_buffers[i]
                event_buffers[i] = set_delta_time(other_event, get_delta_time(other_event) - shortest_delta_time)
        else:
            event_pointers[next_event] += 1
            if event_pointers[next_event] < len(og_tracks[next_event]):
                new_event = og_tracks[next_event][event_pointers[next_event]]
                event_buffers[next_event] = set_delta_time(new_event, get_delta_time(new_event) + shortest_delta_time)

    if instrument_map["loop"]:
        imuse_loop_event = event_templates["imuse loop"].copy()
        imuse_loop_event["data"] = imuse_loop_event["data"].copy()
        
        beat_count = int(total_delta_time / 480) + 1

        imuse_loop_event["data"][15] = hex((beat_count & 0xF000) >> 12)
        imuse_loop_event["data"][16] = hex((beat_count & 0xF00) >> 8)
        imuse_loop_event["data"][17] = hex((beat_count & 0xF0) >> 4)
        imuse_loop_event["data"][18] = hex(beat_count & 0xF)

        events.append(imuse_loop_event)


    events.append(event_templates["track end"])


    adlib_track["events"] = events
    return adlib_track

def build_adlib(track_name):
    midi = midi_decoder.decode(os.path.join("InstrumentMaps", track_name + ".mid"))

    instrument_map_file = open(os.path.join("InstrumentMaps", track_name + ".json"), 'r')
    instrument_map = json.loads(instrument_map_file.read())
    instrument_map_file.close()

    adlib = {}

    adlib["header"] = build_header(midi["header"])
    adlib["tracks"] = [build_track(midi["tracks"], instrument_map)]

    midi_decoder.encode(adlib, instrument_map["path"])

def add_octave_shift_to_maps():
    for subdir, dirs, files in os.walk("InstrumentMaps"):
        for file_name in files:
            if file_name.endswith(".json"):
                file = open(os.path.join(subdir, file_name), 'r')
                instrument_map = json.loads(file.read())
                file.close()

                for track in instrument_map:
                    if not track.isdigit():
                        continue
                    
                    if not "volume" in instrument_map[track]:
                        instrument_map[track]["volume"] = 127
                    if not "instrument" in instrument_map[track]:
                        instrument_map[track]["instrument"] = "Flute"
                    instrument_map[track]["octave shift"] = 0
                
                file = open(os.path.join(subdir, file_name), 'w')
                file.write(json.dumps(instrument_map, indent=4))
                file.close()

def fix_delta_times():
    path = "scale.json"
    file = open(path, 'r')
    midi = json.loads(file.read())
    file.close()

    for track in midi["tracks"]:
        for event in track["events"]:
            event = set_delta_time(event, event["delta time"][0])
    
    path_updated = "scale_updates.json"
    file = open(path, 'w')
    file.write(json.dumps(midi, indent=4))
    file.close()

#fix_delta_times()
#add_octave_shift_to_maps()
build_adlib(sys.argv[1])

