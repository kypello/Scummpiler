import logging
from blocks.v4_base import BlockGloballyIndexedV4

class JunkDataV4(BlockGloballyIndexedV4):
    """LOOM CD contains some odd blocks with no block name in the
    block header, just the value "\x00\x00". These blocks are 
    referenced in the 0N index, so presumeably the blocks are sounds.
    We will treat them like sound blocks, but without any child blocks.
    """

    def generate_file_name(self):
        return ("00"
                + "_"
                + ("unk_" if self.is_unknown else "")
                + str(self.index).zfill(3) + ".dmp")

    @property
    def lookup_name(self):
        """ This method returns the name to be used when looking up/storing values in the global index map."""
        return "SO"