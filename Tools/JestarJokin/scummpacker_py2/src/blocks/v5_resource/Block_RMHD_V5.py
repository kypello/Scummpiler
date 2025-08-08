from blocks.common import BlockRoomHeader
from blocks.v5_base import BlockDefaultV5

class BlockRMHDV5(BlockRoomHeader, BlockDefaultV5):
    name = "RMHD"
