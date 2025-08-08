import cStringIO as StringIO
import os
import unittest
import xml.etree.ElementTree as et
from blocks.v5_resource import *

class BlockIMHDV5TestCase(unittest.TestCase):
    def setUp(self):
        self.block = BlockIMHDV5(4, 0x69)

    def populate_block(self):
        self.block.obj_id = 1001
        self.block.x = 1
        self.block.y = 2
        self.block.width = 3
        self.block.height = 4
        self.block.flags = 5
        self.block.unknown = 6
        self.block.num_imnn = 7
        self.block.num_zpnn = 8

    def test_BlockIMHDV5_generate_xml_node(self):
        root = et.Element("object")
        self.populate_block()

        self.block.generate_xml_node(root)
        expected_values = dict(
            x = "1",
            y = "2",
            width = "3",
            height = "4",
            flags = "0x5",
            unknown = "0x6",
            num_images = "7",
            num_zplanes = "8"
        )

        code = root.find("image")
        self.assert_(code is not None, "V5 Object Image Header IMHD blocks should add a 'image' node to the combined object XML.")

        for k, v in expected_values.items():
            node = code.find(k)
            val = node.text
            self.assertEqual(val, v, "XML value for %s was %s, expected %s" % (k, val, v))

    def test_BlockIMHDV5_load_header_from_xml(self):
        """ This test makes use of a special XML file."""
        path = os.path.join(os.getcwd(), "test", "blocks", "v5_OBHD.xml")
        self.block._load_header_from_xml(path)
        self.assertEqual(self.block.obj_id, 1001)
        self.assertEqual(self.block.x, 1)
        self.assertEqual(self.block.y, 2)
        self.assertEqual(self.block.width, 3)
        self.assertEqual(self.block.height, 4)
        self.assertEqual(self.block.flags, 5)
        self.assertEqual(self.block.unknown, 6)
        self.assertEqual(self.block.num_imnn, 7)
        self.assertEqual(self.block.num_zpnn, 8)
        
    def test_BlockIMHDV5_read_data(self):
        """ Tests that values are mapped from a packed resource file into
        the Block object."""
        resource = StringIO.StringIO(
            "\xE9\x03" + # object ID in LE order
            "\x01\x00" + # num imnn
            "\x02\x00" + # num zpnn
            "\x03" + # flags
            "\x04" + # unknown
            "\x05\x00" + # x
            "\x06\x00" + # y
            "\x07\x00" + # width
            "\x08\x00" # height
        )

        decrypt = False
        self.block.size = 16
        def mock_read_raw_data(resource, size, descrypt):
            return resource.read(size)
        self.block._read_raw_data = mock_read_raw_data
        self.block._read_data(resource, 0, decrypt)
        self.assertEqual(self.block.obj_id, 1001)
        self.assertEqual(self.block.num_imnn, 1)
        self.assertEqual(self.block.num_zpnn, 2)
        self.assertEqual(self.block.flags, 3)
        self.assertEqual(self.block.unknown, 4)
        self.assertEqual(self.block.x, 5)
        self.assertEqual(self.block.y, 6)
        self.assertEqual(self.block.width, 7)
        self.assertEqual(self.block.height, 8)

        
    def test_BlockIMHDV5_write_data(self):
        resource = StringIO.StringIO()
        
        self.populate_block()
        encrypt = False
        self.block._write_data(resource, encrypt)
        
        self.assertEqual(
            resource.getvalue(),
            "\xE9\x03" + # object ID in LE order
            "\x07\x00" + # num imnn
            "\x08\x00" + # num zpnn
            "\x05" + # flags
            "\x06" + # unknown
            "\x01\x00" + # x
            "\x02\x00" + # y
            "\x03\x00" + # width
            "\x04\x00" # height
        )
        

if __name__ == '__main__':
    unittest.main()
