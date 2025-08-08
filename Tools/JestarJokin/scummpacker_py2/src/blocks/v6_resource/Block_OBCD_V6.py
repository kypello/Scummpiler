from blocks.v6_base import BlockDefaultV6, BlockContainerV6
from blocks.shared import BlockOBCDShared
from Block_CDHD_V6 import BlockCDHDV6
from blocks.v5_resource import BlockOBNAV5

class BlockOBCDV6(BlockOBCDShared, BlockContainerV6):
    name = "OBCD"
    cdhd_class = BlockCDHDV6
    verb_class = BlockDefaultV6
    obna_class = BlockOBNAV5
