from blocks.common import BlockLucasartsEntertainmentContainer
from blocks.v4_base import BlockContainerV4
from Block_FO_V4 import BlockFOV4

class BlockLEV4(BlockLucasartsEntertainmentContainer, BlockContainerV4):
    def _init_class_data(self):
        self.name = "LE"
        self.OFFSET_CLASS = BlockFOV4
        