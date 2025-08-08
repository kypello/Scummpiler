from blocks.common import BlockRoom
from blocks.v4_base import BlockContainerV4
from other import ScriptBlockContainerV4, ObjectBlockContainerV4

class BlockROV4(BlockRoom, BlockContainerV4): # also globally indexed
    def _init_class_data(self):
        self.name = "RO"
        self.lf_name = "LF"
        self.room_offset_name = "FO"
        self.script_types = frozenset(["EN",
                                  "EX",
                                  "LS"])
        self.object_types = frozenset(["OI",
                                  "OC"])
        self.object_between_types = frozenset(["NL",
                                  "SL"])
        self.object_image_type = "OI"
        self.object_code_type = "OC"
        self.num_scripts_type = "LC"
        self.script_container_class = ScriptBlockContainerV4
        self.object_container_class = ObjectBlockContainerV4
        self.dodgy_offsets = {
            "MI1VGA" : set([
                # These are ROs in the last LF block on disk 4.
                0xE26BD,
                0xE81F7,
                0xE9791,
                0xEB2BD,
                0xEE973,
                0xEF142,
                0xEF7FF,
                0xEFEBC,
                0xF0579,
                0xF0C36,
                0XF1A9A,
                0XF2B90,
                0XF3FAB,
                0XF6B17,
                0XF8C22,
                0XF9BF2,
                0XFA7CE,
                0XFC0B0,
                0XFDDFB
            ])
        } # workaround for junk room data in MI1EGA/MI1VGA
