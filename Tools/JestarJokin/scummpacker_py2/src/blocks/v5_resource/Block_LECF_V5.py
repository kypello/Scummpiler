from blocks.common import BlockLucasartsEntertainmentContainer
from blocks.v5_base import BlockContainerV5
from Block_LOFF_V5 import BlockLOFFV5

class BlockLECFV5(BlockLucasartsEntertainmentContainer, BlockContainerV5):
    def _init_class_data(self):
        self.name = "LECF"
        self.OFFSET_CLASS = BlockLOFFV5
