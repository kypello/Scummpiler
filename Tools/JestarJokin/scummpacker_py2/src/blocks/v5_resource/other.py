from blocks.common import ObjectBlockContainer, ScriptBlockContainer
from Block_OBCD_V5 import BlockOBCDV5
from Block_OBIM_V5 import BlockOBIMV5

# Meta containers
class ObjectBlockContainerV5(ObjectBlockContainer):
    def _init_class_data(self):
        self.obcd_name = "OBCD"
        self.obim_name = "OBIM"
        self.obcd_class = BlockOBCDV5
        self.obim_class = BlockOBIMV5

class ScriptBlockContainerV5(ScriptBlockContainer):
    local_scripts_name = "LSCR"
    entry_script_name = "ENCD"
    exit_script_name = "EXCD"
    lf_name = "LFLF"
    num_local_name = "NLSC"
