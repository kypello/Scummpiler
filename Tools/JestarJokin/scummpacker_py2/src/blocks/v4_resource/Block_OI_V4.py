from __future__ import with_statement
import logging
import os
import struct
import xml.etree.ElementTree as et
import scummpacker_util as util
from blocks.v4_base import BlockDefaultV4

class BlockOIV4(BlockDefaultV4):
    """ Reads object ID but otherwise acts as generic block."""
    name = "OI"
    xml_structure = tuple()

    def _read_data(self, resource, start, decrypt, room_start=0):
        data = resource.read(2)
        if decrypt:
            data = util.crypt(data, self.crypt_value)
        self.obj_id = struct.unpack("<H", data)[0]
        self.data = self._read_raw_data(resource, self.size - (resource.tell() - start), decrypt)

    def load_from_file(self, path):
        self._load_header_from_xml(os.path.join(path, "OBHD.xml"))
        self._load_data_from_file(os.path.join(path, "OI.dmp"))
        self.size = self._calculate_size()

    def _load_header_from_xml(self, path):
        tree = et.parse(path)
        root = tree.getroot()

        # Shared
        self.obj_id = util.xml2int(root.find("id").text)

    def _load_data_from_file(self, path):
        with file(path, 'rb') as data_file:
            # Skip the header info
            data_file.seek(6 + 2)
            # read script data
            start_data = data_file.tell()
            data_file.seek(0, os.SEEK_END)
            end_data = data_file.tell()
            data_size = end_data - start_data
            data_file.seek(start_data, os.SEEK_SET)
            #logging.debug("Attempting to load %s. start_data = %s. end_data = %s. data_size = %s" % (path, start_data, end_data, data_size))
            data = self._read_raw_data(data_file, data_size, False)
            self.data = data

    def _write_data(self, outfile, encrypt):
        """ Assumes it's writing to a resource."""
        # Object header
        data = struct.pack("<H", self.obj_id)
        if encrypt:
            data = util.crypt(data, self.crypt_value)
        outfile.write(data)
        # Image data
        self._write_raw_data(outfile, self.data, encrypt)

    def _calculate_size(self):
        # block header + header data + data size
        return 6 + 2 + len(self.data)

