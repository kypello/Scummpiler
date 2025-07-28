import os, sys, re, json

from pathlib import Path


class TimestampManager:
    timestamp_table = {}

    timestamp_file_path = ""

    decomp_root_path = ""

    def __init__(self, decomp_root_path):
        self.decomp_root_path = Path(decomp_root_path).resolve()

    def normalize_file_path(self, file_path):
        absolute_path = Path(file_path).resolve()
        relative_path = absolute_path.relative_to(self.decomp_root_path)
        return relative_path

    def add_timestamp(self, file_path):
        normalized_file_path = self.normalize_file_path(file_path)

        self.timestamp_table[str(normalized_file_path)] = os.path.getmtime(file_path)
    
    def save_to_timestamp_file(self):
        timestamp_file_path = os.path.join(self.decomp_root_path, "timestamps.json")
        timestamp_file = open(timestamp_file_path, 'w')
        timestamp_file.write(json.dumps(self.timestamp_table, indent = 0))
        timestamp_file.close()

        
    
resolved_path = Path(sys.argv[1]).resolve()
print(resolved_path)
    