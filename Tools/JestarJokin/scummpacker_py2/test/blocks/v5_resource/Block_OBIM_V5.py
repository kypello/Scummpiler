import xml.etree.ElementTree as et
import unittest
from blocks.v5_resource import *

class BlockOBIMV5TestCase(unittest.TestCase):
    def setUp(self):
        self.block = BlockOBIMV5(4, 0x69)

    def populate_block(self):
        class MockIMHD(object):
            def generate_xml_node(self, parent_xml_node):
                pass
        self.block.imhd = MockIMHD()
        self.block.imhd.x = 1
        self.block.imhd.y = 2
        self.block.imhd.width = 3
        self.block.imhd.height = 4
        self.block.imhd.flags = 5
        self.block.imhd.unknown = 6
        self.block.imhd.num_imnn = 7
        self.block.imhd.num_zpnn = 8

    def test_BlockOBIMV5_generate_xml_node(self):
        root = et.Element("object")
        self.populate_block()

        self.block.generate_xml_node(root)

        code = root.find("image")
        self.assert_(code is None, "V5 Object Image OBIM blocks should not add anything to the combined object XML.")

if __name__ == '__main__':
    unittest.main()