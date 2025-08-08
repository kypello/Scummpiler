import xml.etree.ElementTree as et
import unittest
import os
import cStringIO as StringIO

from blocks.v4_resource import *

class BlockOIV4TestCase(unittest.TestCase):
    def setUp(self):
        self.block = BlockOIV4(2, 0x69)

    def populate_block(self):
        pass

    def test_BlockOIV4_generate_xml_node(self):
        """ Tests that the block generates expected values in output XML. """
        root = et.Element("object")
        self.populate_block()

        self.block.generate_xml_node(root)

        image = root.find("image")
        self.assert_(image is None, "V4 Object Image blocks should not output anything to the combined object XML.")

    def test_BlockOIV4_load_header_from_xml(self):
        """ Tests that the block receives expected values from the XML.
        This test makes use of a special XML file."""
        path = os.path.join(os.getcwd(), "test", "blocks", "v4_OBHD.xml")
        self.block._load_header_from_xml(path)
        self.assertEqual(self.block.obj_id, 1001)

    def test_BlockOIV4_read_data(self):
        """ Tests that values are mapped from a packed resource file into
        the Block object."""
        id_data = "\xE9\x03" # ID in LE order
        image_data = "\x01\x02\x03\x04" # image data
        resource = StringIO.StringIO(
            id_data +
            image_data
        )

        decrypt = False
        self.block.size = 6

        # Mock out _read_raw_data, since it requires a real file for
        #  the call to array.fromfile.
        def mock_read_raw_data(resource, size, descrypt):
            return resource.read(size)
        self.block._read_raw_data = mock_read_raw_data

        self.block._read_data(resource, 0, decrypt)
        self.assertEqual(self.block.obj_id, 1001)
        self.assertEqual(self.block.data, image_data)

if __name__ == '__main__':
    unittest.main()
