#! /usr/bin/python
# V3 is pretty much exactly the same as V4, so we do lots of weird stuff here.

#import os
#import re
import blocks
from common import *
#from v3 import *
from v4 import *

INDEXED_BLOCKS_V3 = INDEXED_BLOCKS_V4

class BlockDispatcherV3(BlockDispatcherV4):
    CRYPT_VALUE = None
    ROOT_BLOCK = blocks.LFLContainerV3
    BLOCK_MAP = dict(BlockDispatcherV4.BLOCK_MAP)
    BLOCK_MAP.update({
        "SO" : blocks.BlockSOV3
    })

class FileDispatcherV3(FileDispatcherV4):
    CRYPT_VALUE = None
    ROOT_BLOCK = blocks.LFLContainerV3
    BLOCK_MAP = dict(FileDispatcherV4.BLOCK_MAP)
    BLOCK_MAP.update({
        # NOTE: indexed blocks are still handled by BlockSOV4 regex block.
        # This just picks up the nested inner SO block.
        "SO" : blocks.BlockSOV3 
    })

class IndexBlockContainerV3(IndexBlockContainerV4):
    USE_ROOMNAMES = False

# Below classes are used by FM-Towns V3 games
class BlockDispatcherV3FMTowns(BlockDispatcherV3):
    BLOCK_MAP = dict(BlockDispatcherV3.BLOCK_MAP)
    BLOCK_MAP.update({
        "SO" : blocks.BlockGloballyIndexedV4
    })

class FileDispatcherV3FMTowns(FileDispatcherV3):
    REGEX_BLOCKS = list(FileDispatcherV3.REGEX_BLOCKS)
    # MEGA HACK - note to self - if I see you do anything like this in the
    #  future I will kill you.
    REGEX_BLOCKS[1] = (re.compile(r"SO_[0-9]{3}"), blocks.BlockGloballyIndexedV4)
