#! /usr/bin/python
from __future__ import with_statement
import scummpacker_control as control
from v5_resource import *
from v5_index import *

def __test_unpack():
    import dispatchers
    control.global_args.set_args(unpack=True, pack=False, scumm_version="5",
        game="MI2", input_file_name="MONKEY2.000", output_file_name="D:\\TEMP")
    control.unknown_blocks_counter = control.IndexCounter(*dispatchers.INDEXED_BLOCKS_V5)
    control.global_index_map = control.IndexMappingContainer(*dispatchers.INDEXED_BLOCKS_V5)

    outpath = "D:\\TEMP"

    dirfile = file("MONKEY2.000", "rb")
    dir_block = dispatchers.IndexBlockContainerV5()
    dir_block.load_from_resource(dirfile)
    dirfile.close()

    dir_block.save_to_file(outpath)

    control.block_dispatcher = dispatchers.BlockDispatcherV5()
    resfile = file("MONKEY2.001", "rb")
    block = BlockLECFV5(4, 0x69)
    block.load_from_resource(resfile)
    resfile.close()

    block.save_to_file(outpath)

def __test_pack():
    import dispatchers
    control.global_args.set_args(unpack=False, pack=True, scumm_version="5",
        game="MI2", input_file_name="D:\\TEMP", output_file_name="D:\\TEMP\\outres.000")
    control.file_dispatcher = dispatchers.FileDispatcherV5()
    control.unknown_blocks_counter = control.IndexCounter(*dispatchers.INDEXED_BLOCKS_V5)
    control.global_index_map = control.IndexMappingContainer(*dispatchers.INDEXED_BLOCKS_V5)

    startpath = "D:\\TEMP"

    block = BlockLECFV5(4, 0x69)
    block.load_from_file(startpath)
    index_block = dispatchers.IndexBlockContainerV5()
    index_block.load_from_file(startpath)

    logging.info("read from file, now saving to resource")

    outpath_res = os.path.join(startpath, "outres.001")
    with file(outpath_res, 'wb') as outres:
        block.save_to_resource(outres)
    outpath_index = os.path.join(startpath, "outres.000")
    with file(outpath_index, 'wb') as outindres:
        index_block.save_to_resource(outindres)


def __test():
    #__test_unpack()
    __test_pack()

# TODO: better integration test dispatching
test_blocks_v5 = __test

if __name__ == "__main__": __test()
