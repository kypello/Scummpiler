import xml.etree.ElementTree as et
import unittest
from blocks.v5_resource import *

class BlockOBCDV5TestCase(unittest.TestCase):
    def setUp(self):
        self.block = BlockOBCDV5(4, 0x69)

    def populate_block(self):
        class MockCDHD(object):
            def generate_xml_node(self, parent_xml_node):
                pass
        self.block.cdhd = MockCDHD()
        self.block.cdhd.x = 1
        self.block.cdhd.y = 2
        self.block.cdhd.width = 3
        self.block.cdhd.height = 4
        self.block.cdhd.flags = 5
        self.block.cdhd.parent = 6
        self.block.cdhd.walk_x = 7
        self.block.cdhd.walk_y = 8
        self.block.cdhd.actor_dir = 9

    def test_BlockOBCDV5_generate_xml_node(self):
        root = et.Element("object")
        self.populate_block()

        self.block.generate_xml_node(root)

        code = root.find("code")
        self.assert_(code is None, "V5 Object Code blocks should not add a 'code' node to the combined object XML.")

if __name__ == '__main__':
    unittest.main()