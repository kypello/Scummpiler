#! /usr/bin/python
# Stores globals
import os.path
import logging
from optparse import OptionParser
import scummpacker_util as util

class IndexCounter(object):
    def __init__(self, *args):
        self.index_map = {}
        for s in args:
            self.index_map[s] = 0

    def reset_counts(self):
        for k in self.index_map:
            self.index_map[k] = 0
    
    def get_next_index(self, index_name):
        if not index_name in self.index_map:
            raise util.ScummPackerException("Unrecognised block \"" 
                                            + str(index_name) 
                                            + "\" tried to retrieve a counted index.")
        self.index_map[index_name] = self.index_map[index_name] + 1
        return self.index_map[index_name]


class IndexMappingContainer(object):
    def __init__(self, *args):
        self.index_map = {}
        for s in args:
            self.index_map[s] = {}
    
    def reset_maps(self):
        for k in self.index_map:
            self.index_map[k].clear()
            
    def map_index(self, map_name, key, index):
        self.__setitem__(map_name, key, index)
        
    def __setitem__(self, map_name, key, index):
        #if map_name == 'LFLF':
        #    raise util.ScummPackerException("test. %s %s" % (key, index))
        if not map_name in self.index_map:
            raise util.ScummPackerException("Unrecognised block \"" 
                                            + str(map_name) 
                                            + "\" tried to store a global index.")
        #logging.debug("Setting %s index : %s / %s" % (map_name, key, index))
        self.index_map[map_name][key] = index
        
    def get_index(self, map_name, key):
        return self.__getitem__(map_name, key)
    
    def __getitem__(self, map_name, key):
        #logging.debug(map_name)
        #logging.debug(self.index_map[map_name])
        if not map_name in self.index_map:
            raise util.ScummPackerException("Unrecognised block \"" 
                                            + str(map_name) 
                                            + "\" tried to retrieve a global index.")
        if not key in self.index_map[map_name]:
            raise util.ScummPackerUnrecognisedIndexException("Block \"" 
                                            + str(map_name) 
                                            + "\" tried to retrieve an unrecognised global index \""
                                            + str(key)
                                            + "\".")
        return self.index_map[map_name][key]

    def items(self, map_name):
        """Returns key/value pairs for the desired block table."""
        if not map_name in self.index_map:
            raise util.ScummPackerException("Unrecognised block \""
                                            + str(map_name)
                                            + "\" tried to retrieve a global index.")
        return self.index_map[map_name].items()
    
class GlobalArguments(object):
    SCUMM_VERSION_GAME_MAP = {
        "ZAKFM" : "3fm",
        "INDY3VGA" : "3",
        "MI1EGA" : "4",
        "MI1VGA" : "4",
        "LOOMCD" : "4",
        "MI1CD" : "5",
        "MI1CDalt" : "5",
        "MI2" : "5",
        "FOA" : "5",
        "DOTT" : "6",
        "SAM" : "6",
        "SAMalt" : "6"
    }
    DEFAULT_GAME_FOR_SCUMM_VERSION = {
        "3fm" : "ZAKFM",
        "3" : "INDY3VGA",
        "4" : "LOOMCD", # hm...
        "5" : "FOA",
        "6" : "SAM"
    }

    def __init__(self):
        self._scumm_version = None
        self._game = None
        self._input_file_name = None
        self._output_file_name = None
        self._unpack = None
        self._pack = None
        self.oparser = OptionParser(usage="%prog [options]",
                               version="ScummPacker v3",
                               description="Packs and unpacks resources used by LucasArts adventure games.")
        self.oparser.add_option("-v", "--scumm-version", action="store",
                           dest="scumm_version",
                           choices=sorted(self.DEFAULT_GAME_FOR_SCUMM_VERSION.keys()),
                           help="Specify the SCUMM version to target. " +
                           "Possible options are: " +
                           ", ".join(sorted(self.DEFAULT_GAME_FOR_SCUMM_VERSION.keys())) + ". ")
        self.oparser.add_option("-g", "--game", action="store",
                           dest="game",
                           choices=sorted(self.SCUMM_VERSION_GAME_MAP.keys()),
                           help="Specify the game to target. " +
                           "Possible options are: " +
                           ", ".join(sorted(self.SCUMM_VERSION_GAME_MAP.keys())) + ". ")
        self.oparser.add_option("-i", "--input", action="store",
                           dest="input_file_name",
                           help="Specify an input path, containing game resources.")
        self.oparser.add_option("-o", "--output", action="store",
                           dest="output_file_name",
                           help="Specify an output path.")
        self.oparser.add_option("-u", "--unpack", action="store_true",
                           dest="unpack", default=False,
                           help="Unpack resources.")
        self.oparser.add_option("-p", "--pack", action="store_true",
                           dest="pack", default=False,
                           help="Pack resources.")
        #self.oparser.set_defaults(scumm_version="5", game="MI2", output_file_name="outres")

    def set_scumm_version(self, scumm_version):
        self._scumm_version = scumm_version

    scumm_version = property((lambda self: self._scumm_version), set_scumm_version)
            
    def set_game(self, game):
        self._game = game

    game = property((lambda self: self._game), set_game)
            
    def set_input_file_name(self, input_file_name):
        self._input_file_name = input_file_name

    input_file_name = property((lambda self: self._input_file_name), set_input_file_name)
    
    def set_output_file_name(self, output_file_name):
        # @type output_file_name str
        self._output_file_name = output_file_name

    output_file_name = property((lambda self: self._output_file_name), set_output_file_name)

    def validate_scumm_version_and_game(self):
        # Must specify either game or SCUMM version.
        if self.scumm_version is None and self.game is None:
            return "You must specify either a game or a SCUMM version number."
        
        # If game is not specified, use the default game for that SCUMM version.
        if self.game is None:
            try:
                self._game = self.DEFAULT_GAME_FOR_SCUMM_VERSION[self._scumm_version]
            except KeyError:
                return "Unrecognised SCUMM version specified: %s." % self._scumm_version
            
        if self.scumm_version is None:
            try:
                self._scumm_version = self.SCUMM_VERSION_GAME_MAP[self._game]
            except KeyError:
                return "Unrecognised game specified: %s." % self._game
                
        # If both game and SCUMM version specified, verify that it's a valid combination.
        if self.SCUMM_VERSION_GAME_MAP[self.game] != self.scumm_version:
            return "A conflicting SCUMM version and game ID was specified. version: %s, game: %s." % (self.scumm_version, self.game)
        return None

    def validate_args(self):
        result = self.validate_scumm_version_and_game()
        if result != None:
            return result
        # validate that either pack or unpack is chosen
        if not self.pack and not self.unpack:
            return "Please specify whether to pack or unpack SCUMM resources."
        # Validate input and output paths
        if self.input_file_name is None or not os.path.isdir(self.input_file_name):
            return "Input path does not exist, or is not a directory: %s" % self.input_file_name
        if self.output_file_name is None or not os.path.isdir(self.output_file_name):
            try:
                os.mkdir(self.output_file_name)
            except OSError:
                return "Output path could not be created, or is not a directory: " + str(self.output_file_name)
        return None

    def parse_args(self):
        options, args = self.oparser.parse_args()
        # @type options Values
        if len(args) > 0:
            raise util.ScummPackerException("Invalid arguments specified, check your options.")
        self.unpack = options.unpack
        self.pack = options.pack
        self.scumm_version = options.scumm_version
        self.game = options.game
        self.input_file_name = options.input_file_name
        self.output_file_name = options.output_file_name
        

    def set_args(self, **kwds):
        """ Used for old 'unit' testing."""
        self._scumm_version = kwds["scumm_version"]
        self._game = kwds["game"]
        self.validate_scumm_version_and_game()
        self._input_file_name = kwds["input_file_name"]
        self._output_file_name = kwds["output_file_name"]
        self._unpack = kwds["unpack"]
        self._pack = kwds["pack"]
        

    def print_help(self):
        self.oparser.print_help()


global_args = GlobalArguments()

unknown_blocks_counter = IndexCounter()
disk_spanning_counter = 0 # stores which disk/resource file we're looking at.
global_index_map = IndexMappingContainer()
index_dispatcher = None
block_dispatcher = None
file_dispatcher = None