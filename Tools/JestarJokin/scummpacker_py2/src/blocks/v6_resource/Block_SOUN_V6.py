from blocks.shared import BlockSOUNShared
from blocks.v5_base import BlockGloballyIndexedV5
from blocks.v6_base import BlockContainerV6

class BlockSOUNV6(BlockSOUNShared, BlockContainerV6, BlockGloballyIndexedV5):
    """ SOUN blocks in V6 introduce the MIDI sub-block."""
    pass