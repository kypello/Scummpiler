#! /usr/bin/python
import logging
import os
import re
import blocks
from common import *

INDEXED_BLOCKS_V5 = (
    "ROOM",
    "COST",
    "CHAR",
    "SCRP",
    "SOUN",
    "LFLF",
    "RNAM",
    "Disk" # for disk spanning info. Could use "LECF"
)

class BlockDispatcherV5(AbstractBlockDispatcher):

    CRYPT_VALUE = 0x69
    BLOCK_NAME_LENGTH = 4
    BLOCK_MAP = {
        # Container blocks
        "LFLF" : blocks.BlockLFLFV5, # also indexed
        "ROOM" : blocks.BlockROOMV5, # also indexed (kind of)
        "RMIM" : blocks.BlockContainerV5,
        "SOUN" : blocks.BlockSOUNV5, # also sound (kind of)
        "OBIM" : blocks.BlockOBIMV5,
        "OBCD" : blocks.BlockOBCDV5,
        "LECF" : blocks.BlockLECFV5,

        # Sound blocks
        "SOU " : blocks.BlockSOUV5,
        "ROL " : blocks.BlockMIDISoundV5,
        "SPK " : blocks.BlockMIDISoundV5,
        "ADL " : blocks.BlockMIDISoundV5,
        "SBL " : blocks.BlockSBLV5,
        "GMD " : blocks.BlockMIDISoundV5,

        # Globally indexed blocks
        "COST" : blocks.BlockGloballyIndexedV5,
        "CHAR" : blocks.BlockGloballyIndexedV5,
        "SCRP" : blocks.BlockGloballyIndexedV5,
        "SOUN" : blocks.BlockSOUNV5,

        # Other blocks that should not use default block functionality
        "IMHD" : blocks.BlockIMHDV5,
        "LSCR" : blocks.BlockLSCRV5,
        "RMHD" : blocks.BlockRMHDV5,
        "RMIH" : blocks.BlockRMIHV5,
        "LOFF" : blocks.BlockLOFFV5

    }
    REGEX_BLOCKS = [
        (re.compile(r"IM[0-9]{2}"), blocks.BlockContainerV5)
    ]
    DEFAULT_BLOCK = blocks.BlockDefaultV5
    ROOT_BLOCK = blocks.BlockLECFV5

    def _read_block_name(self, resource):
        bname = resource.read(self.BLOCK_NAME_LENGTH)
        resource.seek(-self.BLOCK_NAME_LENGTH, os.SEEK_CUR)
        return bname

class FileDispatcherV5(AbstractFileDispatcher):
    CRYPT_VALUE = 0x69
    BLOCK_NAME_LENGTH = 4
    BLOCK_MAP = {
        # Root
        r"LECF" : blocks.BlockLECFV5,
        # LECF
        # -LFLF
        r"ROOM" : blocks.BlockROOMV5,
        # --ROOM
        r"BOXD.dmp" : blocks.BlockDefaultV5,
        r"BOXM.dmp" : blocks.BlockDefaultV5,
        r"CLUT.dmp" : blocks.BlockDefaultV5,
        r"CYCL.dmp" : blocks.BlockDefaultV5,
        r"EPAL.dmp" : blocks.BlockDefaultV5,
        r"SCAL.dmp" : blocks.BlockDefaultV5,
        r"TRNS.dmp" : blocks.BlockDefaultV5,
        r"RMHD.xml" : blocks.BlockRMHDV5,
        r"RMIM" : blocks.BlockContainerV5,
        r"objects" : blocks.ObjectBlockContainerV5,
        r"scripts" : blocks.ScriptBlockContainerV5,
        # ---RMIM
        r"RMIH.xml" : blocks.BlockRMIHV5,
        # ---objects (incl. subdirs)
        r"VERB.dmp" : blocks.BlockDefaultV5,
        r"SMAP.dmp" : blocks.BlockDefaultV5, # also RMIM
        r"BOMP.dmp" : blocks.BlockDefaultV5, # room 99, object 1045 in MI1 CD.
        # ---scripts
        r"ENCD.dmp" : blocks.BlockDefaultV5,
        r"EXCD.dmp" : blocks.BlockDefaultV5,
        # - Sound blocks
        r"SOU" : blocks.BlockSOUV5,
        r"ROL.mid" : blocks.BlockMIDISoundV5,
        r"SPK.mid" : blocks.BlockMIDISoundV5,
        r"ADL.mid" : blocks.BlockMIDISoundV5,
        r"SBL.voc" : blocks.BlockSBLV5,

    }
    REGEX_BLOCKS = [
        # LECF
        (re.compile(r"LFLF_[0-9]{3}.*"), blocks.BlockLFLFV5),
        # -LFLF
        (re.compile(r"SOUN_[0-9]{3}(?:\.dmp)?"), blocks.BlockSOUNV5),
        (re.compile(r"CHAR_[0-9]{3}"), blocks.BlockGloballyIndexedV5),
        (re.compile(r"COST_[0-9]{3}"), blocks.BlockGloballyIndexedV5),
        (re.compile(r"SCRP_[0-9]{3}"), blocks.BlockGloballyIndexedV5),
        # --ROOM
        # ---objects
        (re.compile(r"IM[0-9a-fA-F]{2}"), blocks.BlockContainerV5), # also RMIM
        (re.compile(r"ZP[0-9a-fA-F]{2}\.dmp"), blocks.BlockDefaultV5), # also RMIM
        # --scripts
        (re.compile(r"LSCR_[0-9]{3}\.dmp"), blocks.BlockLSCRV5)
    ]
    IGNORED_BLOCKS = frozenset([
        r"ROL.mdhd",
        r"SPK.mdhd",
        r"ADL.mdhd",
        r"SBL.mdhd",
        r"order.xml"
    ])
    DEFAULT_BLOCK = blocks.BlockDefaultV5
    ROOT_BLOCK = blocks.BlockLECFV5

class IndexBlockContainerV5(AbstractIndexDispatcher):
    """Resource.000 processor; just maps blocks to Python objects (POPOs?)."""
    CRYPT_VALUE = 0x69
    BLOCK_NAME_LENGTH = 4
    BLOCK_MAP = {
        "RNAM" : blocks.BlockRNAMV5,
        "MAXS" : blocks.BlockMAXSV5,
        "DROO" : blocks.BlockDROOV5,
        "DSCR" : blocks.BlockIndexDirectoryV5,
        "DSOU" : blocks.BlockIndexDirectoryV5,
        "DCOS" : blocks.BlockIndexDirectoryV5,
        "DCHR" : blocks.BlockIndexDirectoryV5,
        "DOBJ" : blocks.BlockDOBJV5
    }
    REGEX_BLOCKS = []
    DEFAULT_BLOCK = blocks.BlockDefaultV5

    def load_from_file(self, path):
        self.children = []

        # Crappy crappy crap
        # It's like this because blocks need to be in a specific order
        rnam_block = self.BLOCK_MAP["RNAM"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        rnam_block.load_from_file(os.path.join(path, "roomnames.xml"))
        self.children.append(rnam_block)

        maxs_block = self.BLOCK_MAP["MAXS"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        maxs_block.load_from_file(os.path.join(path, "maxs.xml"))
        self.children.append(maxs_block)

        d_block = self.BLOCK_MAP["DROO"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        self.children.append(d_block)
        d_block = self.BLOCK_MAP["DSCR"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        d_block.name = "DSCR"
        self.children.append(d_block)
        d_block = self.BLOCK_MAP["DSOU"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        d_block.name = "DSOU"
        self.children.append(d_block)
        d_block = self.BLOCK_MAP["DCOS"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        d_block.name = "DCOS"
        self.children.append(d_block)
        d_block = self.BLOCK_MAP["DCHR"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        d_block.name = "DCHR"
        self.children.append(d_block)

        dobj_block = self.BLOCK_MAP["DOBJ"](self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        dobj_block.load_from_file(os.path.join(path, "dobj.xml"))
        self.children.append(dobj_block)

