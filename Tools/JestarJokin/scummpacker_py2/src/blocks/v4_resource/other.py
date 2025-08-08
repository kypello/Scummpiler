import scummpacker_util as util
from blocks.common import ObjectBlockContainer, ScriptBlockContainer
from Block_OC_V4 import BlockOCV4
from Block_OI_V4 import BlockOIV4

#--------------------
# Meta or container blocks.
class ObjectBlockContainerV4(ObjectBlockContainer):
    def _init_class_data(self):
        self.obcd_name = "OC"
        self.obim_name = "OI"
        self.obcd_class = BlockOCV4
        self.obim_class = BlockOIV4

class ScriptBlockContainerV4(ScriptBlockContainer):
    local_scripts_name = "LS"
    entry_script_name = "EN"
    exit_script_name = "EX"
    lf_name = "LF"
    num_local_name = "LC"

    def _write_number_of_local_scripts(self, resource):
        # Determine the number of local scripts
        num_local_scripts = len(self.local_scripts)
        resource.write(util.int2str(8, 4, util.LE, self.crypt_value)) # size of this block is always 8
        resource.write(util.crypt(self.num_local_name, self.crypt_value)) # write the block header's name
        resource.write(util.int2str(num_local_scripts, 2, util.LE, self.crypt_value))

