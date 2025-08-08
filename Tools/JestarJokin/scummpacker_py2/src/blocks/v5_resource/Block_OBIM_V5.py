from blocks.v5_base import BlockContainerV5
from blocks.shared import BlockOBIMShared
from Block_IMHD_V5 import BlockIMHDV5

class BlockOBIMV5(BlockOBIMShared, BlockContainerV5):
    imhd_class = BlockIMHDV5
    container_class = BlockContainerV5
