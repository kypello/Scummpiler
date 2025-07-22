import os, sys, json, midi_decoder

def compare_instrument(instrument_a, instrument_b):
    i = 3
    while i < len(instrument_a):
        if instrument_a[i] != instrument_b[i]:
            return False
        i += 1
    return True




def find_instruments(path):
    instruments = []

    output_file = open(os.path.join("PythonScripts", "Resources", "instruments.json"), 'r')
    instrument_dict = json.loads(output_file.read())
    output_file.close()

    instrument_count = 0
    for instrument in instrument_dict:
        instrument_count += 1
    

    for subdir, dirs, files in os.walk(path):
        for file_name in files:
            if file_name == "ADL.mid":
                file_path = os.path.join(subdir, file_name)
                midi = midi_decoder.decode(file_path)

                for event in midi["tracks"][0]["events"]:
                    if event["class"] == "sysex" and (event["data"][1] == "0x10" or event["data"][1] == "0x11"):
                        start_point = 4
                        if event["data"][1] == "0x11":
                            start_point = 5

                        instrument = event["data"][start_point:len(event["data"])]
                        instrument_already_found = False

                        for found_instrument in instruments:
                            if compare_instrument(found_instrument, instrument):
                                instrument_already_found = True
                                break

                        if not instrument_already_found:
                            instrument_dict[instrument_count] = instrument
                            instruments.append(instrument)
                            instrument_count += 1
    
    print("Instrument count: " + str(len(instruments)))
    output_file = open(os.path.join("PythonScripts", "Resources", "instruments.json"), 'w')
    output_file.write(json.dumps(instrument_dict, indent=4))
    output_file.close()

find_instruments(sys.argv[1])