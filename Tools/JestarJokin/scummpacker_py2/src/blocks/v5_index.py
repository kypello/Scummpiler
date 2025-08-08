import os
import struct
import xml.etree.ElementTree as et
import scummpacker_control as control
import scummpacker_util as util
from common import *
from v5_base import *

class BlockRNAMV5(BlockRoomNames, BlockDefaultV5):
    name = "RNAM"

class BlockMAXSV5(BlockDefaultV5):
    name = "MAXS"

    def _read_data(self, resource, start, decrypt, room_start=0):
        """
        Block Name         (4 bytes)
        Block Size         (4 bytes BE)
        Variables          (2 bytes)
        Unknown            (2 bytes)
        Bit Variables      (2 bytes)
        Local Objects      (2 bytes)
        New Names?         (2 bytes)
        Character Sets     (2 bytes)
        Verbs?             (2 bytes)
        Array?             (2 bytes)
        Inventory Objects  (2 bytes)
        """
        data = resource.read(18)
        if decrypt:
            data = util.crypt(data, self.crypt_value)
        values = struct.unpack("<9H", data)
        del data

        self.num_vars, self.unknown_1, self.bit_vars, self.local_objects, \
            self.unknown_2, self.char_sets, self.unknown_3, self.unknown_4, \
            self.inventory_objects = values

    def save_to_file(self, path):
        root = et.Element("maximums")

        et.SubElement(root, "variables").text = util.int2xml(self.num_vars)
        et.SubElement(root, "unknown_1").text = util.int2xml(self.unknown_1)
        et.SubElement(root, "bit_variables").text = util.int2xml(self.bit_vars)
        et.SubElement(root, "local_objects").text = util.int2xml(self.local_objects)
        et.SubElement(root, "unknown_2").text = util.int2xml(self.unknown_2)
        et.SubElement(root, "character_sets").text = util.int2xml(self.char_sets)
        et.SubElement(root, "unknown_3").text = util.int2xml(self.unknown_3)
        et.SubElement(root, "unknown_4").text = util.int2xml(self.unknown_4)
        et.SubElement(root, "inventory_objects").text = util.int2xml(self.inventory_objects)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "maxs.xml"))

    def load_from_file(self, path):
        tree = et.parse(path)
        root = tree.getroot()

        self.size = 18 + self.block_name_length + 4

        self.num_vars = util.xml2int(root.find("variables").text)
        self.unknown_1 = util.xml2int(root.find("unknown_1").text)
        self.bit_vars = util.xml2int(root.find("bit_variables").text)
        self.local_objects = util.xml2int(root.find("local_objects").text)
        self.unknown_2 = util.xml2int(root.find("unknown_2").text)
        self.char_sets = util.xml2int(root.find("character_sets").text)
        self.unknown_3 = util.xml2int(root.find("unknown_3").text)
        self.unknown_4 = util.xml2int(root.find("unknown_4").text)
        self.inventory_objects = util.xml2int(root.find("inventory_objects").text)

    def _write_data(self, outfile, encrypt):
        """ Assumes it's writing to a resource."""
        data = struct.pack("<9H", self.num_vars, self.unknown_1, self.bit_vars, self.local_objects,
            self.unknown_2, self.char_sets, self.unknown_3, self.unknown_4,
            self.inventory_objects)
        if encrypt:
            data = util.crypt(data, self.crypt_value)
        outfile.write(data)

class BlockDOBJV5(BlockObjectIndexes, BlockDefaultV5):
    name = "DOBJ"
    class_data_size = 4


class BlockDROOV5(BlockRoomIndexes, BlockDefaultV5):
    """DROO indexes don't seem to be used in V5.

    Each game seems to have a different padding length."""
    name = "DROO"
    DEFAULT_PADDING_LENGTHS = {
        "MI1CD" : 100,
        "MI2" : 127,
        "FOA" : 99,
        # Ooooh some more stuff for V6! Hackorama!
        "DOTT" : 91,
        "SAM" : 94,
    }
    default_disk_or_room_number = 1 # this is quite vital!
    
    def _read_data(self, resource, start, decrypt, room_start=0):
        """We just don't care."""
        resource.seek(self.size - 8, os.SEEK_CUR)
    
    def save_to_resource(self, resource, room_start=0):
        """DROO blocks do not seem to be used in V5 games, so save dummy info."""
        self.size = 5 * self.padding_length + 2 + self.block_name_length + 4
        self._write_header(resource, True)
        resource.write(util.int2str(self.padding_length, 2, crypt_val=self.crypt_value))
        for _ in xrange(self.padding_length): # this is "file/disk number" rather than "room number" in V4
            resource.write(util.int2str(self.default_disk_or_room_number, 1, crypt_val=self.crypt_value))
        for _ in xrange(self.padding_length):
            resource.write(util.int2str(self.default_offset, 4, crypt_val=self.crypt_value))

