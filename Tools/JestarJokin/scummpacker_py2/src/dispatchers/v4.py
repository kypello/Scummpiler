#! /usr/bin/python
import os
import re
import blocks
from common import *

INDEXED_BLOCKS_V4 = (
    "FO", # room offsets, for use in "FO" blocks.
    "RO", # rooms
    "LF", # lf
    "SC", # scripts
    "CO", # cosutmes
    "SO", # sounds
    "RN", # room names
    "Disk" # for disk spanning info. Could use "LE".
)

class BlockDispatcherV4(AbstractBlockDispatcher):

    CRYPT_VALUE = 0x69
    BLOCK_NAME_LENGTH = 2
    BLOCK_MAP = {
       # Container blocks
        "LE" : blocks.BlockLEV4, # main container (Lucasarts Entertainment)
        "LF" : blocks.BlockLFV4, # contains rooms and global resources
        "RO" : blocks.BlockROV4, # room
#
#        # Sound blocks
        "SO" : blocks.BlockSOV4, # sound, also container
#        "WA" : None, # VOC (wave)
#        "AD" : None, # adlib
#
        # Globally indexed blocks
        "SC" : blocks.BlockGloballyIndexedV4, # scripts
        "CO" : blocks.BlockGloballyIndexedV4, # costumes


        # Other blocks that should not use default block functionality
        "FO" : blocks.BlockFOV4, # file (room) offsets
        "HD" : blocks.BlockHDV4, # room header
        "LS" : blocks.BlockLSV4, # local scripts
        "OI" : blocks.BlockOIV4, # object image
        "OC" : blocks.BlockOCV4, # object code
#        "HD" : None, # room header

        # Odd sound block in Loom CD
        "\x00\x00" : blocks.JunkDataV4

    }
    REGEX_BLOCKS = [
        #(re.compile(r"IM[0-9]{2}"), blocks.BlockContainerV4)
    ]
    DEFAULT_BLOCK = blocks.BlockDefaultV4
    ROOT_BLOCK = blocks.BlockLEV4

    def _read_block_name(self, resource):
        """ SCUMM v3 and v4 stores block size before the block name."""
        resource.seek(4, os.SEEK_CUR)
        bname = resource.read(self.BLOCK_NAME_LENGTH)
        resource.seek(-self.BLOCK_NAME_LENGTH, os.SEEK_CUR)
        resource.seek(-4, os.SEEK_CUR)
        return bname

class FileDispatcherV4(AbstractFileDispatcher):
    CRYPT_VALUE = 0x69
    BLOCK_NAME_LENGTH = 2
    BLOCK_MAP = {
        # Root
        r"LE" : blocks.BlockLEV4,
        # LECF
        # -LFLF
        r"RO" : blocks.BlockROV4,
        # --ROOM
        r"BM.dmp" : blocks.BlockDefaultV4,
        r"BX.dmp" : blocks.BlockDefaultV4,
        r"CC.dmp" : blocks.BlockDefaultV4,
        r"HD.xml" : blocks.BlockHDV4,
        #r"LC.dmp" : blocks.BlockDefaultV4, # ignored since it's generated
        r"PA.dmp" : blocks.BlockDefaultV4,
        r"SA.dmp" : blocks.BlockDefaultV4,
        r"NL.dmp" : blocks.BlockDefaultV4, # appears between OC and OI blocks
        r"SL.dmp" : blocks.BlockDefaultV4, # appears between OC and OI blocks
        r"SP.dmp" : blocks.BlockDefaultV4,
        r"objects" : blocks.ObjectBlockContainerV4,
        r"scripts" : blocks.ScriptBlockContainerV4,
        # ---objects (incl. subdirs)
        r"OC.dmp" : blocks.BlockDefaultV4,
        r"OI.dmp" : blocks.BlockDefaultV4,
        # ---scripts
        r"EN.dmp" : blocks.BlockDefaultV4,
        r"EX.dmp" : blocks.BlockDefaultV4,
        # - Sound blocks
        r"AD.dmp" : blocks.BlockDefaultV4,
        r"WA.dmp" : blocks.BlockDefaultV4,
    }
    REGEX_BLOCKS = [
        # LECF
        (re.compile(r"LF_[0-9]{3}.*"), blocks.BlockLFV4),
        # -LFLF
        (re.compile(r"SO_[0-9]{3}"), blocks.BlockSOV4),
        #(re.compile(r"CHAR_[0-9]{3}"), blocks.BlockGloballyIndexedV4),
        (re.compile(r"CO_[0-9]{3}"), blocks.BlockGloballyIndexedV4),
        (re.compile(r"SC_[0-9]{3}"), blocks.BlockGloballyIndexedV4),
        # --ROOM
        # --scripts
        (re.compile(r"LS_[0-9]{3}\.dmp"), blocks.BlockLSV4),
        # Odd sound data (appears between SO sounds and CO costumes in Loom CD)
        (re.compile(r"00_[0-9]{3}\.dmp"), blocks.JunkDataV4),
    ]
    IGNORED_BLOCKS = frozenset([
        r"OBHD.xml",
        r"LC.dmp",
        r"order.xml"
    ])
    DEFAULT_BLOCK = blocks.BlockDefaultV4
    ROOT_BLOCK = blocks.BlockLEV4    
    
class IndexBlockContainerV4(AbstractIndexDispatcher):
    CRYPT_VALUE = None # V3-4 indexes aren't encrypted
    BLOCK_NAME_LENGTH = 2
    BLOCK_MAP = {
        "RN" : blocks.BlockRNV4, # room names
        "0R" : blocks.Block0RV4, # rooms
        "0S" : blocks.BlockIndexDirectoryV4, # scripts
        "0N" : blocks.BlockIndexDirectoryV4, # sounds (noises)
        "0C" : blocks.BlockIndexDirectoryV4, # costumes
        "0O" : blocks.Block0OV4 # objects
    }
    REGEX_BLOCKS = []
    DEFAULT_BLOCK = blocks.BlockDefaultV4
    USE_ROOMNAMES = False # SCUMM V3 doesn't use room names.
    
    def _read_block_name(self, resource):
        """ SCUMM v3 and v4 stores block size before the block name."""
        resource.seek(4, os.SEEK_CUR)
        bname = resource.read(self.BLOCK_NAME_LENGTH)
        resource.seek(-self.BLOCK_NAME_LENGTH, os.SEEK_CUR)
        resource.seek(-4, os.SEEK_CUR)
        return bname
    
    def load_from_file(self, path):
        self.children = []

        # Crappy crappy crap
        # It's like this because blocks need to be in a specific order
        if self.USE_ROOMNAMES:
            rnam_block = blocks.BlockRNV4(self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
            rnam_block.load_from_file(os.path.join(path, "roomnames.xml"))
            self.children.append(rnam_block)

        d_block = blocks.Block0RV4(self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        self.children.append(d_block)
        d_block = blocks.BlockIndexDirectoryV4(self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        d_block.name = "0S"
        self.children.append(d_block)
        d_block = blocks.BlockIndexDirectoryV4(self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        d_block.name = "0N"
        self.children.append(d_block)
        d_block = blocks.BlockIndexDirectoryV4(self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        d_block.name = "0C"
        self.children.append(d_block)

        dobj_block = blocks.Block0OV4(self.BLOCK_NAME_LENGTH, self.CRYPT_VALUE)
        dobj_block.load_from_file(os.path.join(path, "dobj.xml"))
        self.children.append(dobj_block)
