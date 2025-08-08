import os
from blocks.v6_base import BlockDefaultV6
import scummpacker_util as util

class BlockAPALV6(BlockDefaultV6):
    """ Assumes index is assigned externally (from WRAP block) when reading from resource."""

    def load_from_file(self, path):
        """ Assumes we won't get any 'unknown' blocks or dirs."""
        fname = os.path.split(path)[1]
        index = os.path.splitext(fname)[0][-3:]
        try:
            self.index = int(index)
        except ValueError, ve:
            raise util.ScummPackerException(str(self.index) + " is an invalid index for resource " + path)
        super(BlockDefaultV6, self).load_from_file(path)

    def generate_file_name(self):
        return (self.name
                + "_"
                + str(self.index).zfill(3) + ".dmp")