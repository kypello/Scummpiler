import xml.etree.ElementTree as et
import os
import scummpacker_control as control
import scummpacker_util as util
from abstractblock import AbstractBlock

class BlockRoomNames(AbstractBlock):
    name_length = 9
    name = NotImplementedError("This property must be overridden by inheriting classes.")

    def _read_data(self, resource, start, decrypt, room_start=0):
        end = start + self.size
        self.room_names = []
        while resource.tell() < end:
            room_no = util.str2int(resource.read(1), crypt_val=(self.crypt_value if decrypt else None))
            if room_no == 0: # end of list marked by 0x00
                break
            room_name = resource.read(self.name_length)
            if decrypt:
                room_name = util.crypt(room_name, self.crypt_value)
            room_name = util.crypt(room_name, 0xFF).rstrip("\x00")
            self.room_names.append((room_no, room_name))
            control.global_index_map.map_index(self.name, room_no, room_name)

    def save_to_file(self, path):
        root = et.Element("room_names")

        for room_no, room_name in self.room_names:
            room = et.SubElement(root, "room")
            et.SubElement(room, "id").text = util.int2xml(room_no)
            et.SubElement(room, "name").text = util.escape_invalid_chars(room_name)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "roomnames.xml"))

    def load_from_file(self, path):
        tree = et.parse(path)
        root = tree.getroot()

        self.room_names = []
        for room in root.findall("room"):
            room_no = util.xml2int(room.find("id").text)
            room_name = room.find("name").text
            if room_name == None:
                room_name = ''
            room_name = util.unescape_invalid_chars(room_name)
            self.room_names.append((room_no, room_name))
            control.global_index_map.map_index(self.name, room_no, room_name)

    def save_to_resource(self, resource, room_start=0):
        self.size = 10 * len(self.room_names) + 1 + self.block_name_length + 4
        self._write_header(resource, True)
        for room_no, room_name in self.room_names:
            resource.write(util.int2str(room_no, 1, crypt_val=self.crypt_value))
            # pad/truncate room name to 8 characters
            room_name = (room_name + ("\x00" * (self.name_length - len(room_name)))
                if len(room_name) < self.name_length
                else room_name[:self.name_length])
            resource.write(util.crypt(room_name, self.crypt_value ^ 0xFF if self.crypt_value else 0xFF))
        resource.write(util.int2str(0, 1, crypt_val=self.crypt_value))
