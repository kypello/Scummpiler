import xml.etree.ElementTree as et
import scummpacker_util as util
from blocks.v5_base import BlockDefaultV5

class BlockIMHDV5(BlockDefaultV5):
    name = "IMHD"
    xml_structure = (
        ("image", 'n', (
            ("x", 'i', 'x'),
            ("y", 'i', 'y'),
            ("width", 'i', 'width'),
            ("height", 'i', 'height'),
            ("flags", 'h', 'flags'),
            ("unknown", 'h', 'unknown'),
            ("num_images", 'i', 'num_imnn'),
            ("num_zplanes", 'i', 'num_zpnn')
            )
        ),
    )
    struct_data = {
        'size' : 16,
        'format' : "<3H2B4H",
        'attributes' :
            ('obj_id',
            'num_imnn',
            'num_zpnn',
            'flags',
            'unknown',
            'x',
            'y',
            'width',
            'height')
    }

    def _read_data(self, resource, start, decrypt, room_start=0):
        """
        obj id       : 16le
        num imnn     : 16le
        num zpnn     : 16le (per IMnn block)
        flags        : 8
        unknown      : 8
        x            : 16le
        y            : 16le
        width        : 16le
        height       : 16le

        not sure about the following, I think it's only applicable for SCUMM V6+:
        num hotspots : 16le (usually one for each IMnn, but there is one even
                       if no IMnn is present)
        hotspots
          x          : 16le signed
          y          : 16le signed
        """
        self.read_struct_data(self.struct_data, resource, decrypt)

    def load_from_file(self, path):
        self.name = "IMHD"
        self.size = 16 + 8 # data + block header
        self._load_header_from_xml(path)

    def _load_header_from_xml(self, path):
        tree = et.parse(path)
        root = tree.getroot()

        # Shared
        self.obj_id = util.xml2int(root.find("id").text)
        # Read image metadata using XML structure
        self.read_xml_node(root)

    def save_to_file(self, path):
        """ Combined OBHD.xml is saved in the ObjectBlockContainer."""
        return

    def _write_data(self, resource, encrypt):
        self.write_struct_data(self.struct_data, resource, encrypt)
