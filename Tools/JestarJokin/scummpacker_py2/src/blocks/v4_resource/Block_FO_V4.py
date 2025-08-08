from blocks.common import BlockRoomOffsets
from blocks.v4_base import BlockDefaultV4

class BlockFOV4(BlockRoomOffsets, BlockDefaultV4):
    name = "FO"
    LFLF_NAME = "LF"
    ROOM_OFFSET_NAME = "FO"
    OFFSET_POINTS_TO_ROOM = False
    disk_lookup_name = "Disk"