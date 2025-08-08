from blocks.shared import BlockSOUNShared
from blocks.v5_base import BlockContainerV5, BlockGloballyIndexedV5

class BlockSOUNV5(BlockSOUNShared, BlockContainerV5, BlockGloballyIndexedV5):
    """ SOUN blocks in V5 may contain CD track data. Unfortunately, these CD
    blocks have no nice header value to look for. Instead, we have to check
    the file size somehow."""

    pass