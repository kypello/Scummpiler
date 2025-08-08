import cStringIO as StringIO
import xml.etree.ElementTree as et
import unittest
import os
from blocks.v6_index import *

class BlockMAXSV6TestCase(unittest.TestCase):
    def setUp(self):
        self.block = BlockMAXSV6(4, 0x69)

    def populate_block(self):
        self.block.num_vars = 1
        self.block.unknown_1 = 2
        self.block.bit_vars = 3
        self.block.local_objects = 4
        self.block.num_arrays = 5
        self.block.unknown_2 = 6
        self.block.verbs = 7
        self.block.floating_objects = 8
        self.block.inventory_objects = 9
        self.block.rooms = 10
        self.block.scripts = 11
        self.block.sounds = 12
        self.block.char_sets = 13
        self.block.costumes = 14
        self.block.global_objects = 15

    def test_BlockMAXSV6_generate_xml_node(self):
        root = et.Element("maximums")
        self.populate_block()

        self.block.generate_xml_node(root)
        expected_values = dict(
            variables = "1",
            unknown_1 = "2",
            bit_variables = "3",
            local_objects = "4",
            arrays = "5",
            unknown_2 = "6",
            verbs = "7",
            floating_objects = "8",
            inventory_objects = "9",
            rooms = "10",
            scripts = "11",
            sounds = "12",
            character_sets = "13",
            costumes = "14",
            global_objects = "15"
        )
        
        for k, v in expected_values.items():
            node = root.find(k)
            self.assertFalse(node is None, "XML node was not found: %s" % k)
            val = node.text
            self.assertEqual(val, v, "XML value for %s was %s, expected %s" % (k, val, v))

    def test_BlockMAXSV6_load_header_from_xml(self):
        """ Tests that the block receives expected values from the XML.
        This test makes use of a special XML file."""
        path = os.path.join(os.getcwd(), "test", "blocks", "v6_MAXS.xml")
        self.block._load_header_from_xml(path)
        self.assertEqual(self.block.num_vars, 1)
        self.assertEqual(self.block.unknown_1, 2)
        self.assertEqual(self.block.bit_vars, 3)
        self.assertEqual(self.block.local_objects, 4)
        self.assertEqual(self.block.num_arrays, 5)
        self.assertEqual(self.block.unknown_2, 6)
        self.assertEqual(self.block.verbs, 7)
        self.assertEqual(self.block.floating_objects, 8)
        self.assertEqual(self.block.inventory_objects, 9)
        self.assertEqual(self.block.rooms, 10)
        self.assertEqual(self.block.scripts, 11)
        self.assertEqual(self.block.sounds, 12)
        self.assertEqual(self.block.char_sets, 13)
        self.assertEqual(self.block.costumes, 14)
        self.assertEqual(self.block.global_objects, 15)

    def test_BlockMAXSV6_read_data(self):
        """ Tests that values are mapped from a packed resource file into
        the Block object."""
        resource = StringIO.StringIO(
            "\x01\x00" + # num_vars
            "\x02\x00" + # unknown_1
            "\x03\x00" + # bit_vars
            "\x04\x00" + # local_objects
            "\x05\x00" + # num_arrays
            "\x06\x00" + # unknown_2
            "\x07\x00" + # verbs
            "\x08\x00" + # floating_objects
            "\x09\x00" + # inventory_objects
            "\x0A\x00" + # rooms
            "\x0B\x00" + # scripts
            "\x0C\x00" + # sounds
            "\x0D\x00" + # char_sets
            "\x0E\x00" + # costumes
            "\x0F\x00"   # global_objects
        )

        decrypt = False
        self.block.size = 30 + 4 + 4
        self.block._read_data(resource, 0, decrypt)
        self.assertEqual(self.block.num_vars, 1)
        self.assertEqual(self.block.unknown_1, 2)
        self.assertEqual(self.block.bit_vars, 3)
        self.assertEqual(self.block.local_objects, 4)
        self.assertEqual(self.block.num_arrays, 5)
        self.assertEqual(self.block.unknown_2, 6)
        self.assertEqual(self.block.verbs, 7)
        self.assertEqual(self.block.floating_objects, 8)
        self.assertEqual(self.block.inventory_objects, 9)
        self.assertEqual(self.block.rooms, 10)
        self.assertEqual(self.block.scripts, 11)
        self.assertEqual(self.block.sounds, 12)
        self.assertEqual(self.block.char_sets, 13)
        self.assertEqual(self.block.costumes, 14)
        self.assertEqual(self.block.global_objects, 15)

    def test_BlockMAXSV6_write_data(self):
        resource = StringIO.StringIO()

        self.populate_block()
        encrypt = False
        self.block._write_data(resource, encrypt)

        self.assertEqual(
            resource.getvalue(),
            "\x01\x00" + # num_vars
            "\x02\x00" + # unknown_1
            "\x03\x00" + # bit_vars
            "\x04\x00" + # local_objects
            "\x05\x00" + # num_arrays
            "\x06\x00" + # unknown_2
            "\x07\x00" + # verbs
            "\x08\x00" + # floating_objects
            "\x09\x00" + # inventory_objects
            "\x0A\x00" + # rooms
            "\x0B\x00" + # scripts
            "\x0C\x00" + # sounds
            "\x0D\x00" + # char_sets
            "\x0E\x00" + # costumes
            "\x0F\x00"   # global_objects
        )

if __name__ == '__main__':
    unittest.main()
