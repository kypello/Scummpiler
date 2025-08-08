import os
from blocks.v5_base import BlockSoundV5

class BlockMIDIV6(BlockSoundV5):

    def load_from_file(self, path):
        self.name = os.path.splitext(os.path.split(path)[1])[0]
        self.size = os.path.getsize(path)
        midi_file = file(path, 'rb')
        self._read_data(midi_file, 0, False)
        self.size += 8 # dumped file does not include "MIDI" block header.
        midi_file.close()

    def save_to_file(self, path):
        outfile = file(os.path.join(path, self.generate_file_name() + ".mid"), 'wb')
        self._write_data(outfile, False)
        outfile.close()
