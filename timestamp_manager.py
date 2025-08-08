import os, sys, re, json

from pathlib import Path


class TimestampManager:
    timestamp_table = {}

    timestamp_file_path = ""

    decomp_root_path = ""

    changes_found = False

    def __init__(self, decomp_root_path):
        self.decomp_root_path = decomp_root_path
        self.timestamp_file_path = Path(self.decomp_root_path, "timestamps.json")
        self.changes_found = False

    def normalize_path(self, path):
        relative_path = path.relative_to(self.decomp_root_path)
        return relative_path

    def find_most_recent_timestamp_in_folder(self, folder_path):
        most_recent_timestamp = 0
        for file_path in folder_path.iterdir():
            file_timestamp = file_path.stat().st_mtime

            if file_timestamp > most_recent_timestamp:
                most_recent_timestamp = file_timestamp
        
        return most_recent_timestamp

    def get_timestamp(self, path):
        if path.is_dir():
            return self.find_most_recent_timestamp_in_folder(path)
        else:
            return path.stat().st_mtime

    def add_timestamp(self, file_path):
        normalized_file_path = self.normalize_path(file_path)

        current_timestamp = self.get_timestamp(file_path)

        self.timestamp_table[str(normalized_file_path)] = current_timestamp
        self.changes_found = True

    def check_timestamp(self, file_path):
        normalized_file_path = self.normalize_path(file_path)

        if not str(normalized_file_path) in self.timestamp_table:
            return True

        logged_timestamp = self.timestamp_table[str(normalized_file_path)]
        current_timestamp = self.get_timestamp(file_path)

        return current_timestamp > logged_timestamp

    def touch_timestamp(self, file_path):
        if self.check_timestamp(file_path):
            self.add_timestamp(file_path)

    def check_for_existing_timestamps(self):
        if self.timestamp_file_path.exists():
            timestamp_file = open(self.timestamp_file_path, 'r')
            self.timestamp_table = json.loads(timestamp_file.read())
            timestamp_file.close()

    def save_to_timestamp_file(self):
        timestamp_file = open(self.timestamp_file_path, 'w')
        timestamp_file.write(json.dumps(self.timestamp_table, indent = 0))
        timestamp_file.close()
    

    