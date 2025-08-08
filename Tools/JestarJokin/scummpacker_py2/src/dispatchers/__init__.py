#! /usr/bin/python
import scummpacker_util as util
import blocks
from v3 import *
from v4 import *
from v5 import *
from v6 import *

class DispatcherFactory(object):
    # SCUMM engine version : index dispatcher (combined block & file), resource block dispatcher, resource file dispatcher, iterable list of names of globally indexed blocks
    grammars = {
        "3fm" : (IndexBlockContainerV3, BlockDispatcherV3FMTowns, FileDispatcherV3FMTowns, INDEXED_BLOCKS_V3),
        "3" : (IndexBlockContainerV3, BlockDispatcherV3, FileDispatcherV3, INDEXED_BLOCKS_V3),
        "4" : (IndexBlockContainerV4, BlockDispatcherV4, FileDispatcherV4, INDEXED_BLOCKS_V4),
        "5" : (IndexBlockContainerV5, BlockDispatcherV5, FileDispatcherV5, INDEXED_BLOCKS_V5),
        "6" : (IndexBlockContainerV6, BlockDispatcherV6, FileDispatcherV6, INDEXED_BLOCKS_V6),
    }

    def __new__(cls, scumm_version, *args, **kwds):
        assert type(scumm_version) == str
        if not scumm_version in DispatcherFactory.grammars:
            raise util.ScummPackerException("Unsupported SCUMM version: %s" % scumm_version)
        index_dispatcher, block_dispatcher, file_dispatcher, indexed_blocks = DispatcherFactory.grammars[scumm_version]
        return (index_dispatcher(), block_dispatcher(), file_dispatcher(), indexed_blocks)
