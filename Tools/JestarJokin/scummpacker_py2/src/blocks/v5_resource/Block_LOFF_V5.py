from blocks.common import BlockRoomOffsets
from blocks.v5_base import BlockDefaultV5

class BlockLOFFV5(BlockRoomOffsets, BlockDefaultV5):
    name = "LOFF"
    LFLF_NAME = "LFLF"
    ROOM_OFFSET_NAME = "ROOM"
    OFFSET_POINTS_TO_ROOM = True
    disk_lookup_name = "Disk"
