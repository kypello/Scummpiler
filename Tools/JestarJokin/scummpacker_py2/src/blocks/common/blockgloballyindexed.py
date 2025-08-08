import logging
import os
import scummpacker_control as control
import scummpacker_util as util
from abstractblock import AbstractBlock

class BlockGloballyIndexed(AbstractBlock):
    lf_name = None # override in concrete class
    room_offset_name = None # override in concrete class
    #lookup_name = override in concrete class if necessary, via property method

    def __init__(self, *args, **kwds):
        super(BlockGloballyIndexed, self).__init__(*args, **kwds)
        self.index = None
        self.is_unknown = False

    def load_from_resource(self, resource, room_start=0):
        location = resource.tell()
        super(BlockGloballyIndexed, self).load_from_resource(resource, room_start)
        try:
            self._lookup_index(location, room_start)
        except util.ScummPackerUnrecognisedIndexException, suie:
            logging.debug("name: %s" % self.name)
            self._handle_unknown_index(location, room_start)

    def _lookup_index(self, location, room_start):
        room_num = control.global_index_map.get_index(self.lf_name, (control.disk_spanning_counter, room_start))
        room_offset = control.global_index_map.get_index(self.room_offset_name, room_num)
        self.index = control.global_index_map.get_index(self.lookup_name,
                                                         (room_num, location - room_offset))

    def _handle_unknown_index(self, location, room_start):
        room_num = control.global_index_map.get_index(self.lf_name, (control.disk_spanning_counter, room_start))
        logging.debug("Unknown block at room num: %s" % room_num)
        room_offset = control.global_index_map.get_index(self.room_offset_name, room_num)
        logging.debug("Unknown block at room offset: %s" % str(location - room_offset))
        logging.error(("Block \"%s\" at offset %s has no entry in the index file (.000). " +
                      "It can not be re-packed or used in the game.") % (self.name, location))
        self.is_unknown = True
        self.index = control.unknown_blocks_counter.get_next_index(self.lookup_name)

    def save_to_resource(self, resource, room_start=0):
        # Look up the start of the current ROOM block, store
        # a mapping of this block's index and room #/offset.
        # Later on, our directories will just treat global_index_map as a list of
        # tables and go through all of the values.
        location = resource.tell()
        self._map_index(location, room_start)
        super(BlockGloballyIndexed, self).save_to_resource(resource, room_start)

    def _map_index(self, location, room_start):
        room_num = control.global_index_map.get_index(self.lf_name, (control.disk_spanning_counter, room_start))
        room_offset = control.global_index_map.get_index(self.room_offset_name, room_num)
        control.global_index_map.map_index(self.lookup_name,
                                           (room_num, location - room_offset),
                                           self.index)

    def load_from_file(self, path):
        """ Assumes we won't get any 'unknown' blocks, based on the regex in the file walker."""
        if os.path.isdir(path):
            index = os.path.split(path)[1][-3:]
        else:
            fname = os.path.split(path)[1]
            index = os.path.splitext(fname)[0][-3:]
        try:
            self.index = int(index)
        except ValueError, ve:
            raise util.ScummPackerException(str(self.index) + " is an invalid index for resource " + path)
        super(BlockGloballyIndexed, self).load_from_file(path)

    def generate_file_name(self):
        return (self.name
                + "_"
                + ("unk_" if self.is_unknown else "")
                + str(self.index).zfill(3) + ".dmp")

    def __repr__(self):
        return "[" + self.name + ":" + ("unk_" if self.is_unknown else "") + str(self.index).zfill(3) + "]"

    @property
    def lookup_name(self):
        """ This method returns the name to be used when looking up/storing values in the global index map.

        This allows inheriting classes to specify a lookup name different to the block name."""
        return self.name

