import xml.etree.ElementTree as et
import scummpacker_util as util
from blocks.v6_base import BlockDefaultV6
import struct

class BlockIMHDV6(BlockDefaultV6):
    name = "IMHD"
    xml_structure = (
        ("image", 'n',
            (
            ("x", 'i', 'x'),
            ("y", 'i', 'y'),
            ("width", 'i', 'width'),
            ("height", 'i', 'height'),
            ("flags", 'h', 'flags'),
            ("unknown", 'h', 'unknown'),
            ("num_images", 'i', 'num_imnn'),
            ("num_zplanes", 'i', 'num_zpnn'),
            ("hotspots", 'c', 'do_hotspots_callback')
            )
        ),
    )
    struct_data = {
        'size' : 18,
        'format' : "<3H2B5H",
        'attributes' :
            ('obj_id',
            'num_imnn',
            'num_zpnn',
            'flags',
            'unknown',
            'x',
            'y',
            'width',
            'height',
            'num_hotspots')
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

        num hotspots : 16le (usually one for each IMnn, but there is one even
                       if no IMnn is present)
        hotspots
          x          : 16le signed
          y          : 16le signed
        """
        self.read_struct_data(self.struct_data, resource, decrypt)
        hotspots = []
        for _ in xrange(self.num_hotspots):
            data = resource.read(4)
            if decrypt:
                data = util.crypt(data, self.crypt_value)
            x, y = struct.unpack('<2H', data)
            hotspots.append((x, y))
        self.hotspots = hotspots
        self.size += self.num_hotspots * 2
            

    def load_from_file(self, path):
        self.name = "IMHD"
        # Note: size has to be adjusted by hotspot.
        self.size = self.struct_data['size'] + 8 # data + block header
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
        for x, y in self.hotspots:
            data = struct.pack('<2H', x, y)
            if encrypt:
                data = util.crypt(data, self.crypt_value)
            resource.write(data)

    def do_hotspots_callback(self, node, mode):
        if mode == 'r':
            self._read_hotspots_from_XML(node)
        elif mode == 'w':
            self._write_hotspots_to_XML(node)
        else:
            raise util.ScummPackerException("Only read or write supported in hotspots callback.")

    def _read_hotspots_from_XML(self, node):
        hotspots = []
        hotspot_nodes = node.findall("hotspot")
        for hn in hotspot_nodes:
            x = util.xml2int(hn.find("x").text)
            y = util.xml2int(hn.find("y").text)
            hotspots.append((x, y))
        self.hotspots = hotspots
        self.num_hotspots = len(hotspots)
        self.size += len(hotspots) * 2 * 2 # need to adjust size. * 2 for x, y, * 2 for 16-bits

    def _write_hotspots_to_XML(self, node):
        for x, y in self.hotspots:
            hotspot_node = et.SubElement(node, "hotspot")
            x_node = et.SubElement(hotspot_node, "x")
            y_node = et.SubElement(hotspot_node, "y")
            x_node.text = util.int2xml(x)
            y_node.text = util.int2xml(y)

