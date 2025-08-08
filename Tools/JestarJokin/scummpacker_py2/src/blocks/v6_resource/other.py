from blocks.common import ObjectBlockContainer
from Block_OBCD_V6 import BlockOBCDV6
from Block_OBIM_V6 import BlockOBIMV6

# Meta containers
class ObjectBlockContainerV6(ObjectBlockContainer):
    def _init_class_data(self):
        self.obcd_name = "OBCD"
        self.obim_name = "OBIM"
        self.obcd_class = BlockOBCDV6
        self.obim_class = BlockOBIMV6
