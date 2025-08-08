import os
import re
import blocks
from dispatchers.v5 import *

INDEXED_BLOCKS_V6 = (
    "ROOM",
    "COST",
    "CHAR",
    "SCRP",
    "SOUN",
    "LFLF",
    "RNAM",
    "Disk" # for disk spanning info. Could use "LECF"
)

class BlockDispatcherV6(BlockDispatcherV5):
    BLOCK_MAP = dict(BlockDispatcherV5.BLOCK_MAP)
    BLOCK_MAP.update({
        "OBIM" : blocks.BlockOBIMV6,
        "OBCD" : blocks.BlockOBCDV6,
        "LFLF" : blocks.BlockLFLFV6,
        "ROOM" : blocks.BlockROOMV6,
        "PALS" : blocks.BlockContainerV6,
        "WRAP" : blocks.BlockWRAPV6,
        "APAL" : blocks.BlockAPALV6,
        "MIDI" : blocks.BlockMIDIV6,
        "SOUN" : blocks.BlockSOUNV6,
        "GMD " : blocks.BlockMIDISoundV5, # DOTT CD
        "SOU " : blocks.BlockSOUV6,
    })

class FileDispatcherV6(FileDispatcherV5):
    BLOCK_MAP = dict(FileDispatcherV5.BLOCK_MAP)
    BLOCK_MAP.update({
        r"PALS" : blocks.BlockContainerV6,
        r"WRAP" : blocks.BlockWRAPV6,
        #"OBIM" : blocks.BlockOBIMV6,
        #"OBCD" : blocks.BlockOBCDV6,
        #"LFLF" : blocks.BlockLFLFV6,
        r"objects" : blocks.ObjectBlockContainerV6,
        r"ROOM" : blocks.BlockROOMV6,
        r"APAL.dmp" : blocks.BlockAPALV6,
        r"OFFS.dmp" : blocks.BlockDefaultV6,
        r"MIDI.mid" : blocks.BlockMIDIV6, # Sam n Max floppy
        r"GMD.mid" : blocks.BlockMIDISoundV5, # DOTT CD
        r"SOU" : blocks.BlockSOUV6,
    })

    # Unfortunately I can't think of a neat way to override the inherited list,
    #  without duplicating the whole list.
    REGEX_BLOCKS = [
        # LECF
        (re.compile(r"LFLF_[0-9]{3}.*"), blocks.BlockLFLFV6), # new
        # -LFLF
        (re.compile(r"SOUN_[0-9]{3}(?:\.dmp)?"), blocks.BlockSOUNV6),
        (re.compile(r"CHAR_[0-9]{3}"), blocks.BlockGloballyIndexedV5),
        (re.compile(r"COST_[0-9]{3}"), blocks.BlockGloballyIndexedV5),
        (re.compile(r"SCRP_[0-9]{3}"), blocks.BlockGloballyIndexedV5),
        # --ROOM
        # ---objects
        (re.compile(r"IM[0-9a-fA-F]{2}"), blocks.BlockContainerV5), # also RMIM
        (re.compile(r"ZP[0-9a-fA-F]{2}\.dmp"), blocks.BlockDefaultV5), # also RMIM
        # --scripts
        (re.compile(r"LSCR_[0-9]{3}\.dmp"), blocks.BlockLSCRV5),
        # images
        (re.compile(r"APAL_[0-9]{3}.*"), blocks.BlockAPALV6) # new
    ]

    IGNORED_BLOCKS = frozenset([
        r"ROL.mdhd",
        r"SPK.mdhd",
        r"ADL.mdhd",
        r"SBL.mdhd",
        r"GMD.mdhd",
        r"order.xml"
    ])

class IndexBlockContainerV6(IndexBlockContainerV5):
    debug = True
    BLOCK_MAP = dict(IndexBlockContainerV5.BLOCK_MAP)
    BLOCK_MAP.update({
        "MAXS" : blocks.BlockMAXSV6,
        "AARY" : blocks.BlockAARYV6
    })

    def load_from_file(self, path):
        IndexBlockContainerV5.load_from_file(self, path)

        aary_block = self.BLOCK_MAP["AARY"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        aary_block.load_from_file(os.path.join(path, "aary.xml"))
        self.children.append(aary_block)
