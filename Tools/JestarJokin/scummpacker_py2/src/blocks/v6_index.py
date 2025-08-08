import os
import xml.etree.ElementTree as et
import scummpacker_util as util
from v5_base import BlockDefaultV5

class BlockMAXSV6(BlockDefaultV5):
    name = "MAXS"
    xml_structure = (
        ("variables", 'i', 'num_vars'),
        ("unknown_1", 'i', 'unknown_1'),
        ("bit_variables", 'i', 'bit_vars'),
        ("local_objects", 'i', 'local_objects'),
        ("arrays", 'i', 'num_arrays'),
        ("unknown_2", 'i', 'unknown_2'),
        ("verbs", 'i', 'verbs'),
        ("floating_objects", 'i', 'floating_objects'),
        ("inventory_objects", 'i', 'inventory_objects'),
        ("rooms", 'i', 'rooms'),
        ("scripts", 'i', 'scripts'),
        ("sounds", 'i', 'sounds'),
        ("character_sets", 'i', 'char_sets'),
        ("costumes", 'i', 'costumes'),
        ("global_objects", 'i', 'global_objects')
    )
    struct_data = {
        'size' : 30,
        'format' : "<15H",
        'attributes' : 
            ('num_vars',
            'unknown_1',
            'bit_vars',
            'local_objects',
            'num_arrays',
            'unknown_2',
            'verbs',
            'floating_objects',
            'inventory_objects',
            'rooms',
            'scripts',
            'sounds',
            'char_sets',
            'costumes',
            'global_objects')
    }

    def _read_data(self, resource, start, decrypt, room_start=0):
        """
        Block Name	   (4 bytes)
        Block Size	   (4 bytes BE)
        Variables	   (2 bytes)
        Unknown	   (2 bytes)
        Bit Variables	   (2 bytes)
        Local Objects	   (2 bytes)
        Arrays		   (2 bytes)
        Unknown	   (2 bytes)
        Verbs		   (2 bytes)
        Floating Objects  (2 bytes)
        Inventory Objects (2 bytes)
        Rooms		   (2 bytes)
        Scripts	   (2 bytes)
        Sounds  	   (2 bytes)
        Character Sets	   (2 bytes)
        Costumes	   (2 bytes)
        Global Objects	   (2 bytes)
        """
        self.read_struct_data(self.struct_data, resource, decrypt)

    def save_to_file(self, path):
        root = et.Element("maximums")

        self.generate_xml_node(root)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "maxs.xml"))

    def load_from_file(self, path):
        self.size = self.struct_data['size'] + self.block_name_length + 4
        self._load_header_from_xml(path)

    def _load_header_from_xml(self, path):
        tree = et.parse(path)
        root = tree.getroot()

        self.read_xml_node(root)

    def _write_data(self, resource, encrypt):
        """ Assumes it's writing to a resource."""
        self.write_struct_data(self.struct_data, resource, encrypt)


class BlockAARYV6(BlockDefaultV5):
    name = "AARY"
    
    def _read_data(self, resource, start, decrypt, room_start=0):

        self.arrays = []

        array_num = util.str2int(resource.read(2), crypt_val=(self.crypt_value if decrypt else None))
        while array_num != 0:

            a = util.str2int(resource.read(2), crypt_val=(self.crypt_value if decrypt else None))
            b = util.str2int(resource.read(2), crypt_val=(self.crypt_value if decrypt else None))
            c = util.str2int(resource.read(2), crypt_val=(self.crypt_value if decrypt else None))

            self.arrays.append( (array_num, a, b, c) )

            array_num = util.str2int(resource.read(2), crypt_val=(self.crypt_value if decrypt else None))

    def save_to_file(self, path):
        root = et.Element("arrays")

        for num, a, b, c in self.arrays:
            array_node = et.SubElement(root, "array-entry")
            et.SubElement(array_node, "num").text = util.int2xml(num)
            et.SubElement(array_node, "a").text = util.int2xml(a)
            et.SubElement(array_node, "b").text = util.int2xml(b)
            et.SubElement(array_node, "c").text = util.int2xml(c)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "aary.xml"))

    def load_from_file(self, path):
        tree = et.parse(path)
        #root = tree.getroot()

        self.arrays = []
        for array_node in tree.getiterator("array-entry"):
            num = util.xml2int(array_node.find("num").text)
            a = util.xml2int(array_node.find("a").text)
            b = util.xml2int(array_node.find("b").text)
            c = util.xml2int(array_node.find("c").text)
            self.arrays.append( (num, a, b, c) )

        # each array definition is 8 bytes, plus 2 bytes to mark the end of
        #  the AARY block.
        self.size = len(self.arrays) * 8 + 2 + self.block_name_length + 4

    def save_to_resource(self, resource, room_start=0):
        self._write_header(resource, True)
        for num, a, b, c in self.arrays:
            resource.write(util.int2str(num, 2, crypt_val=self.crypt_value))
            resource.write(util.int2str(a, 2, crypt_val=self.crypt_value))
            resource.write(util.int2str(b, 2, crypt_val=self.crypt_value))
            resource.write(util.int2str(c, 2, crypt_val=self.crypt_value))
        # Write the terminating value.
        resource.write(util.int2str(0, 2, crypt_val=self.crypt_value))