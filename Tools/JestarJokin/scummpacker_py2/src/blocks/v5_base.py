# TODO: sort out imports
from __future__ import with_statement
import array
import os
import scummpacker_control as control
import scummpacker_util as util
from common import *
from shared import BlockDefaultSharedV5V6

class BlockDefaultV5(BlockDefaultSharedV5V6):
    pass

class BlockSoundV5(BlockDefaultV5):
    """ Sound blocks store incorrect block size (it doesn't include the SOU/ADL/SBL header size)"""
    def _read_size(self, resource, decrypt):
        size = resource.read(4)
        if decrypt:
            size = util.crypt(size, self.crypt_value)
        return util.str2int(size, is_BE=util.BE) + 8

    def _write_header(self, outfile, encrypt):
        name = self.name
        if len(name) == 3:
            name = name + " "
        name = util.crypt(name, self.crypt_value) if encrypt else name
        outfile.write(name)
        size = util.int2str(self.size - 8, is_BE=util.BE, crypt_val=(self.crypt_value if encrypt else None))
        outfile.write(size)

    def _write_dummy_header(self, outfile, encrypt):
        """Writes placeholder information (block name, block size of 0)"""
        name = self.name
        if len(name) == 3:
            name = name + " "
        name = util.crypt(name, self.crypt_value) if encrypt else name
        outfile.write(name)
        size = util.int2str(0, is_BE=util.BE, crypt_val=(self.crypt_value if encrypt else None))
        outfile.write(size)

    def generate_file_name(self):
        return self.name.rstrip()

class BlockGloballyIndexedV5(BlockGloballyIndexed, BlockDefaultV5):
    lf_name = "LFLF"
    room_offset_name = "ROOM"

class BlockContainerV5(BlockContainer, BlockDefaultV5):
    block_ordering = [
        #"LECF", # don't... just don't.
        "LOFF",
        "LFLF",

        # Inside LFLF
        "ROOM",

        # Inside ROOM
        "RMHD",
        "CYCL",
        "TRNS",
        "EPAL",
        "BOXD",
        "BOXM",
        "CLUT",
        "SCAL",
        "RMIM",
         #Inside RMIM
         "RMIH",
         "IM", # IMxx
          #Inside IMxx
          "SMAP",
          "ZP", # ZPxx
        "objects",
        "OBIM",
         #Inside OBIM
         "IMHD",
         "IM",
          #Inside IMxx
          "SMAP",
          "BOMP", # appears in object 1045 in MI1CD.
          "ZP", # ZPxx
        "OBCD",
         #Inside OBCD
         "CDHD",
         "VERB",
         "OBNA",
        "scripts",
        "EXCD",
        "ENCD",
        "NLSC",
        "LSCR",

        # Inside LFLF
        "SCRP",
        "SOUN",
         # Inside SOUN
         "SOU",
         "SOU ",
         "ROL",
         "ROL ",
         "SBL",
         "SBL ",
         "ADL",
         "ADL ",
         "SPK",
         "SPK ",
        "COST",
        "CHAR"
    ]

    def _find_block_rank_lookup_name(self, block):
        rank_lookup_name = block.name
        # dumb crap here
        if rank_lookup_name[:2] == "ZP" or rank_lookup_name[:2] == "IM":
            rank_lookup_name = rank_lookup_name[:2]
        return rank_lookup_name

class BlockMIDISoundV5(BlockSoundV5):
    """ Saves the MDhd header data to a .mhd file, saves the rest of the block
    to a .mid file."""
    MDHD_SIZE = 16
    MDHD_DEFAULT_DATA = "\x4D\x44\x68\x64\x00\x00\x00\x08\x00\x00\x80\x7F\x00\x00\x00\x80"

    def load_from_file(self, path):
        self.name = os.path.splitext(os.path.split(path)[1])[0]
        mdhd_fname = os.path.splitext(path)[0] + ".mdhd"
        if os.path.isfile(mdhd_fname):
            #logging.debug("Loading mdhd from file: " + mdhd_fname)
            mdhd_file = file(mdhd_fname, 'rb')
            mdhd_data = self._read_raw_data(mdhd_file, self.MDHD_SIZE, False)
            mdhd_file.close()
        else:
            mdhd_data = self._generate_mdhd_header()
        self.mdhd_header = mdhd_data
        self.size = os.path.getsize(path) # size does not include ADL/ROL block header
        midi_file = file(path, 'rb')
        self._read_data(midi_file, 0, False)
        midi_file.close()

    def save_to_file(self, path):
        # Possibly the only MDhd block that is different:
        # MI1CD\LECF\LFLF_011\SOUN_043\SOU
        # 4D44 6864 0000 0008 0000 FF7F 0000 0080
        if self.mdhd_header.tostring() != self.MDHD_DEFAULT_DATA:
            outfile = file(os.path.join(path, self.generate_file_name() + ".mdhd"), 'wb')
            self._write_mdhd_header(outfile, False)
            outfile.close()
        outfile = file(os.path.join(path, self.generate_file_name() + ".mid"), 'wb')
        self._write_data(outfile, False)
        outfile.close()

    def save_to_resource(self, resource, room_start=0):
        self._write_header(resource, True)
        self._write_mdhd_header(resource, True)
        self._write_data(resource, True)

    def _read_header(self, resource, decrypt):
        """ Also reads the MDHD header."""
        super(BlockMIDISoundV5, self)._read_header(resource, decrypt)
        self.mdhd_header = self._read_raw_data(resource, self.MDHD_SIZE, decrypt)

    def _write_header(self, outfile, encrypt):
        """ Hack to support adding of MDHD header size."""
        name = self.name
        if len(name) == 3:
            name = name + " "
        name = util.crypt(name, self.crypt_value) if encrypt else name
        outfile.write(name)
        size = self.size + self.MDHD_SIZE # size includes MDHD header, does not include ADL/ROL block header
        size = util.int2str(size, is_BE=util.BE, crypt_val=(self.crypt_value if encrypt else None))
        outfile.write(size)

    def _write_mdhd_header(self, outfile, encrypt):
        outfile.write(util.crypt(self.mdhd_header, (self.crypt_value if encrypt else None)))

    def _generate_mdhd_header(self):
        return array.array('B', self.MDHD_DEFAULT_DATA)


class BlockIndexDirectoryV5(BlockIndexDirectory, BlockDefaultV5):
    DIR_TYPES = {
        #"DROO" : "ROOM", # handled separately.
        "DSCR" : "SCRP",
        "DSOU" : "SOUN",
        "DCOS" : "COST",
        "DCHR" : "CHAR"
        #"DOBJ" : "OBCD" # handled separately.
    }
    MIN_ENTRIES = {
        "MI1CD" : {
            "DSCR" : 199,
            "DSOU" : 150,
            "DCOS" : 150,
            "DCHR" : 7
        },
        "MI2" : {
            "DSCR" : 199,
            "DSOU" : 254,
            "DCOS" : 199,
            "DCHR" : 9
        },
        "FOA" : {
            "DSCR" : 200,
            "DSOU" : 250,
            "DCOS" : 244,
            "DCHR" : 5 # Talkie version is 6, floppy is 5.
        },
        # V6 stuff
        "DOTT" : {
            # Based on the floppy version.
            "DSCR" : 156,
            "DSOU" : 103,
            "DCOS" : 397,
            "DCHR" : 8
        },
        "SAM" : {
            "DSCR" : 123,
            "DSOU" : 95,
            "DCOS" : 341,
            "DCHR" : 6
        }
    }

    def _read_data(self, resource, start, decrypt, room_start=0):
        num_items = util.str2int(resource.read(2), crypt_val=(self.crypt_value if decrypt else None))
        room_nums = []
        i = num_items
        while i > 0:
            room_no = util.str2int(resource.read(1), crypt_val=(self.crypt_value if decrypt else None))
            room_nums.append(room_no)
            i -= 1
        offsets = []
        i = num_items
        while i > 0:
            offset = util.str2int(resource.read(4), crypt_val=(self.crypt_value if decrypt else None))
            offsets.append(offset)
            i -= 1

        for i, key in enumerate(zip(room_nums, offsets)):
            control.global_index_map.map_index(self.DIR_TYPES[self.name], key, i)
