#! /usr/bin/python
from __future__ import with_statement
import logging
import os
import scummpacker_control as control
from common import *
from v4_resource import *
from v4_index import *

def __test_unpack():
    import dispatchers
    control.global_args.set_args(unpack=True, pack=False, scumm_version="4",
        game="LOOMCD", input_file_name="DISK01.LEC", output_file_name="D:\\TEMP")
    outpath = "D:\\TEMP"

#    dirfile = file("000.LFL", "rb")
#    dir_block = dispatchers.IndexBlockContainerV5()
#    dir_block.load_from_resource(dirfile)
#    dirfile.close()
#
#    dir_block.save_to_file(outpath)
    #print dispatchers.INDEXED_BLOCKS_V4
    control.unknown_blocks_counter = control.IndexCounter(*dispatchers.INDEXED_BLOCKS_V4)
    control.global_index_map = control.IndexMappingContainer(*dispatchers.INDEXED_BLOCKS_V4)

    logging.debug("Reading from indexes...")
    dirfile = file(os.path.join("..", "000.LFL"), "rb")
    dir_block = dispatchers.IndexBlockContainerV4()
    dir_block.load_from_resource(dirfile)
    dirfile.close()

    dir_block.save_to_file(outpath)
    
    
    logging.debug("Reading from resources...")
    control.block_dispatcher = dispatchers.BlockDispatcherV4()
    resfile = file(os.path.join("..", "DISK01.LEC"), "rb")
    block = BlockContainerV4(2, 0x69)
    block.load_from_resource(resfile)
    resfile.close()

    logging.debug("Saving to files...")
    block.save_to_file(outpath)
    
    logging.debug("Finished saving to files.")

def __test_pack():
    import dispatchers
    control.global_args.set_args(unpack=False, pack=True, scumm_version="4",
        game="LOOMCD", input_file_name="D:\\TEMP", output_file_name="D:\\TEMP\outres4.000")
    control.file_dispatcher = dispatchers.FileDispatcherV4()
    control.unknown_blocks_counter = control.IndexCounter(*dispatchers.INDEXED_BLOCKS_V4)
    control.global_index_map = control.IndexMappingContainer(*dispatchers.INDEXED_BLOCKS_V4)
    startpath = "D:\\TEMP"
    block = BlockLEV4(2, 0x69)
    block.load_from_file(startpath)
    index_block = dispatchers.IndexBlockContainerV4()
    index_block.load_from_file(startpath)
    
    logging.info("read from file, now saving to resource")
    
    outpath_res = os.path.join(startpath, "outres.001")
    with file(outpath_res, 'wb') as outres:
        block.save_to_resource(outres)
    outpath_index = os.path.join(startpath, "outres.000")
    with file(outpath_index, 'wb') as outindres:
        index_block.save_to_resource(outindres)
        
    logging.debug("Finished saving to resources.")
    
def __test():
    #__test_unpack()
    #__test_unpack_from_file()
    __test_pack()

# TODO: better integration test dispatching
test_blocks_v4 = __test

if __name__ == "__main__": __test()
