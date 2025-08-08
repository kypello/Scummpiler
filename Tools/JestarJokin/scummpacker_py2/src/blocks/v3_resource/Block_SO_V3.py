import os
import scummpacker_control as control
import scummpacker_util as util
from blocks.v4 import BlockSOV4

class BlockSOV3(BlockSOV4):
    """
    V3 stores SO blocks with nested SO blocks; the outer block should be
    treated as globally indexed, while the nested block should not.
    """
    def _handle_unknown_index(self, location, room_start):
        try:
            # Try looking up index of a hypothetical parent block. If none
            #  found, this is an unknown outer SO block. If index is found,
            #  this is an inner SO block, which does not require an index.
            self._lookup_index(location - self.block_name_length - 4, room_start)
            self.index = None
            self.is_unknown = False
        except util.ScummPackerUnrecognisedIndexException, suie:
            super(BlockSOV3, self)._handle_unknown_index(location, room_start)

    def save_to_resource(self, resource, room_start=0):
        location = resource.tell()
        # Only keep track of index of outer SO blocks.
        if self.index is not None:
            self._map_index(location, room_start)
        super(BlockSOV4, self).save_to_resource(resource, room_start)

    def load_from_file(self, path):
        name = os.path.split(path)[1]
        #self.is_cd_track = False
        split_name = name.split('_')
        self.name = name.split('_')[0]
        if len(split_name) > 1:
            # Outer block with index
            self.index = int(name.split('_')[1])
        else:
            # Inner block without index
            self.index = None
        self.children = []

        file_list = os.listdir(path)
        if "order.xml" in file_list:
            file_list.remove("order.xml")
            # The below line of code is pointless, since outer SO blocks only
            #  store one inner SO block, and the inner block doesn't seem to
            #  write an order.xml file.
            self._load_order_from_xml(os.path.join(path, "order.xml"))

        for f in file_list:
            b = control.file_dispatcher.dispatch_next_block(f)
            if b != None:
                b.load_from_file(os.path.join(path, f))
                self.append(b)

    def generate_file_name(self):
        if self.is_unknown == False and self.index is None:
            # Inner block
            name = self.name
        else:
            # Outer block
            name = (self.name
                    + "_"
                    + ("unk_" if self.is_unknown else "")
                    + str(self.index).zfill(3))
        return name