from blocks.common import BlockLucasartsFile
from blocks.v5_base import BlockGloballyIndexedV5
from blocks.v6_base import BlockContainerV6

class BlockLFLFV6(BlockLucasartsFile, BlockContainerV6, BlockGloballyIndexedV5):
    name = "LFLF"
    disk_lookup_name = "Disk"
