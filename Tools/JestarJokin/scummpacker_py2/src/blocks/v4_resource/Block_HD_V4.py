from blocks.common import BlockRoomHeader
from blocks.v4_base import BlockDefaultV4

class BlockHDV4(BlockRoomHeader, BlockDefaultV4):
    name = "HD"
