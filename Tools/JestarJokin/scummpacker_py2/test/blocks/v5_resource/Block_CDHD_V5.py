import cStringIO as StringIO
import os
import unittest
import xml.etree.ElementTree as et
from blocks.v5_resource import *

class BlockCDHDV5TestCase(unittest.TestCase):
    def setUp(self):
        self.block = BlockCDHDV5(4, 0x69)

    def populate_block(self):
        self.block.obj_id = 1001
        self.block.x = 1
        self.block.y = 2
        self.block.width = 3
        self.block.height = 4
        self.block.flags = 5
        self.block.parent = 6
        self.block.walk_x = 7
        self.block.walk_y = 8
        self.block.actor_dir = 9

    def test_BlockCDHDV5_generate_xml_node(self):
        root = et.Element("object")
        self.populate_block()

        self.block.generate_xml_node(root)
        expected_values = dict(
            x = "1",
            y = "2",
            width = "3",
            height = "4",
            flags = "0x5",
            parent = "6",
            walk_x = "7",
            walk_y = "8",
            actor_dir = "9",
        )

        code = root.find("code")
        self.assert_(code is not None, "V5 Object Code Header (CDHD) blocks should add a 'code' node to the combined object XML.")

        for k, v in expected_values.items():
            node = code.find(k)
            val = node.text
            self.assertEqual(val, v, "XML value for %s was %s, expected %s" % (k, val, v))

    def test_BlockCDHDV5_load_header_from_xml(self):
        """ This test makes use of a special XML file."""
        path = os.path.join(os.getcwd(), "test", "blocks", "v5_OBHD.xml")
        self.block._load_header_from_xml(path)
        self.assertEqual(self.block.obj_id, 1001)
        self.assertEqual(self.block.x, 1)
        self.assertEqual(self.block.y, 2)
        self.assertEqual(self.block.width, 3)
        self.assertEqual(self.block.height, 4)
        self.assertEqual(self.block.flags, 5)
        self.assertEqual(self.block.parent, 6)
        self.assertEqual(self.block.walk_x, 7)
        self.assertEqual(self.block.walk_y, 8)
        self.assertEqual(self.block.actor_dir, 9)
        
    def test_BlockCDHDV5_read_data(self):
        """ Tests that values are mapped from a packed resource file into
        the Block object."""
        resource = StringIO.StringIO(
            "\xE9\x03" + # object ID in LE order
            "\x01" + # x
            "\x02" + # y
            "\x03" + # width
            "\x04" + # height
            "\x05" + # flags
            "\x06" + # parent
            "\x07\x00" + # walk_x
            "\x08\x00" + # walk_y
            "\x09" # actor_dir
        )

        decrypt = False
        self.block.size = 13
        def mock_read_raw_data(resource, size, descrypt):
            return resource.read(size)
        self.block._read_raw_data = mock_read_raw_data
        self.block._read_data(resource, 0, decrypt)
        self.assertEqual(self.block.obj_id, 1001)
        self.assertEqual(self.block.x, 1)
        self.assertEqual(self.block.y, 2)
        self.assertEqual(self.block.width, 3)
        self.assertEqual(self.block.height, 4)
        self.assertEqual(self.block.flags, 5)
        self.assertEqual(self.block.parent, 6)
        self.assertEqual(self.block.walk_x, 7)
        self.assertEqual(self.block.walk_y, 8)
        self.assertEqual(self.block.actor_dir, 9)
        
    def test_BlockCDHDV5_write_data(self):
        resource = StringIO.StringIO()
        
        self.populate_block()
        encrypt = False
        self.block._write_data(resource, encrypt)
        
        self.assertEqual(
            resource.getvalue(),
            "\xE9\x03" + # object ID in LE order
            "\x01" + # x
            "\x02" + # y
            "\x03" + # width
            "\x04" + # height
            "\x05" + # flags
            "\x06" + # parent
            "\x07\x00" + # walk_x
            "\x08\x00" + # walk_y
            "\x09" # actor_dir
        )
        

if __name__ == '__main__':
    unittest.main()