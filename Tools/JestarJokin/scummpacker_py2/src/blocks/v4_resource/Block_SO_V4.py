import logging
import os
import scummpacker_control as control
from blocks.v4_base import BlockContainerV4, BlockGloballyIndexedV4

class BlockSOV4(BlockContainerV4, BlockGloballyIndexedV4):
    name = "SO"
    lf_name = "LF"
    room_offset_name = "FO"
    # These blocks have nested SO blocks, but the size of the containing
    #  SO block is incorrect. For some reason it's off by 256 bytes!
    dodgy_offsets = frozenset([
        # Game | location | size as read
        ("MI1EGA", 0x0000A0B2, 0x8215),
        ("MI1VGA", 0x00010DCE, 0x8215),
    ])

    def _read_size(self, resource, decrypt):
        location = resource.tell()
        size = super(BlockSOV4, self)._read_size(resource, decrypt)
        dodgy_offset_lookup = (control.global_args.game, location, size)
        if dodgy_offset_lookup in self.dodgy_offsets:
            logging.debug("dodgy SO offset found: %s, %s, %s" % dodgy_offset_lookup)
            size += 256
        return size

    def save_to_resource(self, resource, room_start=0):
        location = resource.tell()
        self._map_index(location, room_start)
        super(BlockSOV4, self).save_to_resource(resource, room_start)

    def load_from_file(self, path):
        name = os.path.split(path)[1]
        #self.is_cd_track = False
        self.name = name.split('_')[0]
        self.index = int(name.split('_')[1])
        self.children = []

        file_list = os.listdir(path)
        if "order.xml" in file_list:
            file_list.remove("order.xml")
            self._load_order_from_xml(os.path.join(path, "order.xml"))

        for f in file_list:
            b = control.file_dispatcher.dispatch_next_block(f)
            if b != None:
                b.load_from_file(os.path.join(path, f))
                self.append(b)

    def generate_file_name(self):
        name = (self.name
                + "_"
                + ("unk_" if self.is_unknown else "")
                + str(self.index).zfill(3))
        return name
