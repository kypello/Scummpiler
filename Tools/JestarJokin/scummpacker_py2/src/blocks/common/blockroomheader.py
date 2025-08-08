import xml.etree.ElementTree as et
import os
import struct
import scummpacker_util as util
from abstractblock import AbstractBlock

class BlockRoomHeader(AbstractBlock):
    name = NotImplementedError("This property must be overridden by inheriting classes.")
    xml_structure = (
        ("width", 'i', 'width'),
        ("height", 'i', 'height'),
        ("num_objects", 'i', 'num_objects')
    )

    def _read_data(self, resource, start, decrypt, room_start=0):
        """
        width 16le
        height 16le
        num_objects 16le
        """
        data = resource.read(6)
        if decrypt:
            data = util.crypt(data, self.crypt_value)
        values = struct.unpack("<3H", data)
        del data

        # Unpack the values
        self.width, self.height, self.num_objects = values
        del values

    def load_from_file(self, path):
        self.size = 6 + self.block_name_length + 4
        self._load_header_from_xml(path)

    def _load_header_from_xml(self, path):
        tree = et.parse(path)
        root = tree.getroot()

        self.read_xml_node(root)

    def save_to_file(self, path):
        root = et.Element("room")

        self.generate_xml_node(root)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, self.name + ".xml"))

    def _write_data(self, outfile, encrypt):
        """ Assumes it's writing to a resource."""
        data = struct.pack("<3H", self.width, self.height, self.num_objects)
        if encrypt:
            data = util.crypt(data, self.crypt_value)
        outfile.write(data)

