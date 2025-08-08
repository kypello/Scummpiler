from blocks.v5_base import BlockDefaultV5, BlockContainerV5
from blocks.shared import BlockOBCDShared
from Block_CDHD_V5 import BlockCDHDV5
from Block_OBNA_V5 import BlockOBNAV5

class BlockOBCDV5(BlockOBCDShared, BlockContainerV5):
    name = "OBCD"
    cdhd_class = BlockCDHDV5
    verb_class = BlockDefaultV5
    obna_class = BlockOBNAV5
