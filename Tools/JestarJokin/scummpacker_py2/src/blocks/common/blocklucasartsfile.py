import logging
import os
import scummpacker_control as control
import scummpacker_util as util
from blockcontainer import BlockContainer
from blockgloballyindexed import BlockGloballyIndexed

class BlockLucasartsFile(BlockContainer, BlockGloballyIndexed):
    """ Anything inheriting from this class should also inherit from the concrete versions
    of BlockContainer and BlockGloballyIndexed."""
    is_unknown = False
    disk_lookup_name = NotImplementedError("This property must be overridden by inheriting classes.")

    def load_from_resource(self, resource, room_start=0):
        location = resource.tell()
        self._read_header(resource, True)
        self._read_data(resource, location, True, location)
        try:
            # look up by location on disk
            self.index = control.global_index_map.get_index(self.name, (control.disk_spanning_counter, location))  # TODO: confirm if this is correct
        except util.ScummPackerUnrecognisedIndexException, suie:
            logging.error(("Block \"%s\" at offset %s has no entry in the index file (.000). " +
                          "It can not be re-packed or used in the game.") % (self.name, location))
            raise suie
            self.is_unknown = True
            self.index = control.unknown_blocks_counter.get_next_index(self.name)

    def save_to_resource(self, resource, room_start=0):
        location = resource.tell()
        room_start = location
        # Map the location of the LF block.
        control.global_index_map.map_index(self.name, (control.disk_spanning_counter, location), self.index)
        # Map the room number to the disk number, for later use in
        # 0R/DROO blocks in the index file.
        control.global_index_map.map_index(self.disk_lookup_name,
                                           self.index,
                                           control.disk_spanning_counter)
        super(BlockLucasartsFile, self).save_to_resource(resource, room_start)

    def save_to_file(self, path):
        logging.info("Saving block %s" % self.generate_file_name())
        super(BlockLucasartsFile, self).save_to_file(path)

    def load_from_file(self, path):
        name = os.path.split(path)[1]
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
        return (self.name
                + "_"
                + ("unk_" if self.is_unknown else "")
                + str(self.index).zfill(3))

    def __repr__(self):
        childstr = [str(c) for c in self.children]
        return ("["
                + self.name
                + ":"
                + ("unk_" if self.is_unknown else "")
                + str(self.index).zfill(3)
                + ", "
                + ", ".join(childstr)
                + "]")

