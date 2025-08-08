import os
from blocks.v6_base import BlockContainerV6
import scummpacker_control as control
import scummpacker_util as util

class BlockWRAPV6(BlockContainerV6):
    offset_block_name = "OFFS"
    apal_block_name = "APAL"

    def _read_data(self, resource, start, decrypt, room_start=0):
        apal_counter = 0
        end = start + self.size
        while resource.tell() < end:
            block = control.block_dispatcher.dispatch_next_block(resource)
            block.load_from_resource(resource, room_start)
            if block.name == self.offset_block_name:
                # Read in, but ignore the offset block, since we can generate it.
                continue
            elif block.name == self.apal_block_name:
                apal_counter += 1
                block.index = apal_counter
            else:
                raise util.ScummPackerException("Unexpected block \"%s\" found in WRAP container (only expecting APAL or OFFS)." % block.name)
            self.append(block)

    def save_to_resource(self, resource, room_start=0):
        start = resource.tell()

        # write dummy header
        self._write_dummy_header(resource, True)
        # process children

        # First, write a dummy offsets block.
        start_contents = resource.tell()
        self._write_dummy_offsets(resource)

        offsets = []
        for c in self.children:
            if c.name == self.apal_block_name:
                offsets.append(resource.tell() - start_contents) # keep track of offsets of each APAL block
                c.save_to_resource(resource, room_start)

        # go back and write size of block
        end = resource.tell()
        self.size = end - start
        resource.flush()
        resource.seek(start, os.SEEK_SET)
        self._write_header(resource, True)
        self._write_offsets(resource, offsets, True) # go back and write the real APAL offsets
        resource.seek(end, os.SEEK_SET)

    def _write_dummy_offsets(self, resource):
        # Determine the number of APALs
        num_apals = len(self.children)

        resource.write(util.crypt(self.offset_block_name, self.crypt_value)) # write the block header's name
        resource.write(util.int2str(0, 4, util.BE, self.crypt_value))
        for _ in xrange(num_apals):
            resource.write(util.int2str(0, 4, util.LE, self.crypt_value))

    def _write_offsets(self, resource, offsets, encrypt):
        assert len(offsets) == len(self.children)

        resource.write(util.crypt(self.offset_block_name, (self.crypt_value if encrypt else None))) # write the block header's name
        resource.write(util.int2str(8 + len(offsets) * 4, 4, util.BE, crypt_val=(self.crypt_value if encrypt else None)))
        for offset in offsets:
            resource.write(util.int2str(offset, 4, util.LE, crypt_val=(self.crypt_value if encrypt else None)))
