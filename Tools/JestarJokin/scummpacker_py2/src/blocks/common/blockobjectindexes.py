import xml.etree.ElementTree as et
import os
import scummpacker_util as util
from abstractblock import AbstractBlock

class BlockObjectIndexes(AbstractBlock):
    name = NotImplementedError("This property must be overridden by inheriting classes.")
    class_data_size = NotImplementedError("This property must be overridden by inheriting classes.")

    def _read_data(self, resource, start, decrypt, room_start=0):
        num_items = util.str2int(resource.read(2), crypt_val=(self.crypt_value if decrypt else None))
        self.objects = []
        # Read all owner+state values
        for _ in xrange(num_items):
            owner_and_state = util.str2int(resource.read(1), crypt_val=(self.crypt_value if decrypt else None))
            owner = (owner_and_state & 0xF0) >> 4
            state = owner_and_state & 0x0F
            self.objects.append([owner, state])
        # Read all class data values
        for i in xrange(num_items):
            class_data = util.str2int(resource.read(self.class_data_size), crypt_val=(self.crypt_value if decrypt else None))
            self.objects[i].append(class_data)

    def load_from_file(self, path):
        tree = et.parse(path)

        self.objects = []
        for obj_node in tree.getiterator("object-entry"):
            obj_id = int(obj_node.find("id").text)
            if obj_id != obj_id == len(self.objects) + 1:
                raise util.ScummPackerException("Entries in object ID XML must be in sorted order with no gaps in ID numbering.")
            owner = util.xml2int(obj_node.find("owner").text)
            state = util.xml2int(obj_node.find("state").text)
            class_data = util.xml2int(obj_node.find("class-data").text)
            self.objects.append([owner, state, class_data])

    def save_to_file(self, path):
        root = et.Element("object-directory")

        for i in xrange(len(self.objects)):
            owner, state, class_data = self.objects[i]
            obj_node = et.SubElement(root, "object-entry")
            et.SubElement(obj_node, "id").text = util.int2xml(i + 1)
            et.SubElement(obj_node, "owner").text = util.int2xml(owner)
            et.SubElement(obj_node, "state").text = util.int2xml(state)
            et.SubElement(obj_node, "class-data").text = util.hex2xml(class_data)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "dobj.xml"))

    def save_to_resource(self, resource, room_start=0):
        """ TODO: allow filling of unspecified values (e.g. if entries for
        86 and 88 exist but not 87, create a dummy entry for 87."""
        num_items = len(self.objects)

        entry_size = 1 + self.class_data_size
        self.size = entry_size * num_items + 2 + self.block_name_length + 4
        self._write_header(resource, True)

        resource.write(util.int2str(num_items, 2, crypt_val=self.crypt_value))
        self._save_table_data(resource)

    def _save_table_data(self, resource):
        for owner, state, _ in self.objects:
            combined_val = ((owner & 0x0F) << 4) | (state & 0x0F)
            resource.write(util.int2str(combined_val, 1, crypt_val=self.crypt_value))
        for _, _, class_data in self.objects:
            resource.write(util.int2str(class_data, self.class_data_size, crypt_val=self.crypt_value))

