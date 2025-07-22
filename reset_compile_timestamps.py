import sys, os

def reset_timestamps(input_path):
    rooms = [f.path for f in os.scandir(input_path) if f.is_dir()]

    for room in rooms: