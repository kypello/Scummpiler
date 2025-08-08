import os
import struct
import xml.etree.ElementTree as et
import scummpacker_util as util
from blocks.v5_base import BlockDefaultV5

class BlockRMIHV5(BlockDefaultV5):
    name = "RMIH"
    xml_structure = (
        ("num_zbuffers", 'i', 'num_zbuffers'),
    )

    def _read_data(self, resource, start, decrypt, room_start=0):
        """
        Assumes it's reading from a resource.
        num_zbuffers 16le
        """
        data = resource.read(2)
        if decrypt:
            data = util.crypt(data, self.crypt_value)
        values = struct.unpack("<H", data)
        del data

        # Unpack the values
        self.num_zbuffers = values[0]
        del values

    def load_from_file(self, path):
        self.name = "RMIH"
        self.size = 2 + 8
        self._load_header_from_xml(path)

    def _load_header_from_xml(self, path):
        tree = et.parse(path)
        root = tree.getroot()

        self.read_xml_node(root)

    def save_to_file(self, path):
        root = et.Element("room_image")

        self.generate_xml_node(root)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "RMIH.xml"))

    def _write_data(self, outfile, encrypt):
        """ Assumes it's writing to a resource."""
        data = struct.pack("<H", self.num_zbuffers)
        if encrypt:
            data = util.crypt(data, self.crypt_value)
        outfile.write(data)
