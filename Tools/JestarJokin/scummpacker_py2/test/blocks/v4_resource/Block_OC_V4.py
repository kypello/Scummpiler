import xml.etree.ElementTree as et
import unittest
import os
import cStringIO as StringIO
import array

from blocks.v4_resource import *

class BlockOCV4TestCase(unittest.TestCase):
    def setUp(self):
        self.block = BlockOCV4(2, 0x69)

    def populate_block(self):
        self.block.obj_id = 1001
        self.block.x = 1
        self.block.y = 2
        self.block.width = 3
        self.block.height = 160
        self.block.unknown = 5
        self.block.parent_state = 0x80
        self.block.parent = 7
        self.block.walk_x = 8
        self.block.walk_y = 9
        self.block.actor_dir = 4
        self.block.event_table = array.array('B', '\x0E')
        self.block.obj_name = "TestObject"
        self.block.script_data = array.array('B', '\x01\x02\x03\x04')

    def test_BlockOCV4_generate_xml_node(self):
        """ Tests that the block generates expected values in output XML. """
        root = et.Element("object")
        self.populate_block()

        self.block.generate_xml_node(root)
        expected_values = dict(
            x = "1",
            y = "2",
            width = "3",
            height = "160",
            unknown = "0x5",
            parent_state = "0x80",
            parent = "0x7",
            walk_x = "8",
            walk_y = "9",
            actor_dir = "4"
        )

        code = root.find("code")
        self.assert_(code is not None, "V4 Object Code blocks should add a 'code' node to the combined object XML.")

        for k, v in expected_values.items():
            node = code.find(k)
            val = node.text
            self.assertEqual(val, v, "XML value for %s was %s, expected %s" % (k, val, v))

    def test_BlockOCV4_load_header_from_xml(self):
        """ Tests that the block receives expected values from the XML.
        This test makes use of a special XML file."""
        path = os.path.join(os.getcwd(), "test", "blocks", "v4_OBHD.xml")
        self.block._load_header_from_xml(path)
        self.assertEqual(self.block.obj_id, 1001)
        self.assertEqual(self.block.x, 1)
        self.assertEqual(self.block.y, 2)
        self.assertEqual(self.block.width, 3)
        self.assertEqual(self.block.height, 160)
        self.assertEqual(self.block.unknown, 5)
        self.assertEqual(self.block.parent_state, 6)
        self.assertEqual(self.block.parent, 7)
        self.assertEqual(self.block.walk_x, 8)
        self.assertEqual(self.block.walk_y, 9)
        self.assertEqual(self.block.actor_dir, 4)

    def test_BlockOCV4_read_data(self):
        """ Tests that values are mapped from a packed resource file into
        the Block object."""
        script_data = "\x01\x02\x03\x04"
        resource = StringIO.StringIO(
            "\xE9\x03" + # object ID in LE order
            "\x01" + # unknown
            "\x02" + # x
            "\x83" + # y and parent state
            "\x04" + # width
            "\x05" + # parent
            "\x06\x00" + # walk_x
            "\x07\x00" + # walk_y
            "\x0A" + # height and actor_dir (height = 8, actor dir = 2)
            "\x0E" + # name offset
            "\x0E" + # verb table
            "TestObj\x00" + # object name
            script_data
        )

        decrypt = False
        self.block.size = 27
        def mock_read_raw_data(resource, size, descrypt):
            return resource.read(size)
        self.block._read_raw_data = mock_read_raw_data
        self.block._read_data(resource, 0, decrypt)
        self.assertEqual(self.block.obj_id, 1001)
        self.assertEqual(self.block.unknown, 1)
        self.assertEqual(self.block.x, 2)
        self.assertEqual(self.block.y, 3)
        self.assertEqual(self.block.parent_state, 0x80)
        self.assertEqual(self.block.width, 4)
        self.assertEqual(self.block.parent, 5)
        self.assertEqual(self.block.walk_x, 6)
        self.assertEqual(self.block.walk_y, 7)
        self.assertEqual(self.block.height, 8)
        self.assertEqual(self.block.actor_dir, 2)
        self.assertEqual(self.block.event_table, "\x0E")
        self.assertEqual(self.block.obj_name, "TestObj")
        self.assertEqual(self.block.script_data, script_data)

    def test_BlockOCV4_write_data(self):
        resource = StringIO.StringIO()

        def mock_write_raw_data(outfile, data, encrypt):
            return resource.write(data.tostring())
        self.block._write_raw_data = mock_write_raw_data
        
        self.populate_block()
        encrypt = False
        self.block._write_data(resource, encrypt)
        
        self.assertEqual(
            resource.getvalue(),
            "\xE9\x03" + # object ID in LE order
            "\x05" + # unknown
            "\x01" + # x
            "\x82" + # y and parent state
            "\x03" + # width
            "\x07" + # parent
            "\x08\x00" + # walk_x
            "\x09\x00" + # walk_y
            "\xA4" + # height and actor_dir (height = 8, actor dir = 2)
            "\x14" + # name offset
            "\x0E" + # verb table
            "TestObject\x00" + # object name
            "\x01\x02\x03\x04" # script data
        )
        
        resource.close()
        resource = StringIO.StringIO()
        
        # Test for empty verb table.
        self.block.event_table = array.array('B')
        self.block._write_data(resource, encrypt)
        #self.assertRaises(AssertionError, self.block._write_data, resource, encrypt)
        self.assertEqual(
            resource.getvalue(),
            "\xE9\x03" + # object ID in LE order
            "\x05" + # unknown
            "\x01" + # x
            "\x82" + # y and parent state
            "\x03" + # width
            "\x07" + # parent
            "\x08\x00" + # walk_x
            "\x09\x00" + # walk_y
            "\xA4" + # height and actor_dir (height = 8, actor dir = 2)
            "\x14" + # name offset
            "\x00" + # verb table
            "TestObject\x00" + # object name
            "\x01\x02\x03\x04" # script data
        )

        
if __name__ == '__main__':
    unittest.main()
