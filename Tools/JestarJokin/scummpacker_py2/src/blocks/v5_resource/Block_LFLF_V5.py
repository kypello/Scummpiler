from blocks.common import BlockLucasartsFile
from blocks.v5_base import BlockContainerV5, BlockGloballyIndexedV5

class BlockLFLFV5(BlockLucasartsFile, BlockContainerV5, BlockGloballyIndexedV5):
    name = "LFLF"
    disk_lookup_name = "Disk"
