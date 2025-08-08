from __future__ import with_statement
import logging
import os
import scummpacker_util as util
import scummpacker_control as control
import dispatchers

dummy_set = frozenset(tuple())

def assign_dispatchers(index_dispatcher, block_dispatcher, file_dispatcher, indexed_blocks):
    """ This is pretty grotty."""
    control.index_dispatcher = index_dispatcher
    control.block_dispatcher = block_dispatcher
    control.file_dispatcher = file_dispatcher
    control.global_index_map = control.IndexMappingContainer(*indexed_blocks)
    control.unknown_blocks_counter = control.IndexCounter(*indexed_blocks)

class ResourceHandler(object):
    """Handles saving and loading from resource files, adjusting file names,
    spanning across multiple resource files ("disks"), etc."""
    
    SINGLE_ROOM_MULTI_FILE, MULTI_ROOM_MULTI_FILE, SINGLE_FILE = range(3)
    RESOURCE_FILE_TEMPLATES_PER_GAME = {
        "ZAKFM" : (SINGLE_ROOM_MULTI_FILE,
                  ("00", "LFL"),
                  ("%NN%", "LFL"),
                  frozenset(("98.LFL", "99.LFL"))
                  ),
        "INDY3VGA" : (SINGLE_ROOM_MULTI_FILE,
                     ("00", "LFL"),
                     ("%NN%", "LFL"),
                     frozenset(("98.LFL", "99.LFL"))
                     ),
        "MI1EGA" : (MULTI_ROOM_MULTI_FILE,
                    ("000", "LFL"),
                    ("DISK%NN%", "LEC"),
                    dummy_set
                    ),
        "MI1VGA" : (MULTI_ROOM_MULTI_FILE,
                   ("000", "LFL"),
                   ("DISK%NN%", "LEC"),
                   dummy_set
                   ),
        "LOOMCD" : (MULTI_ROOM_MULTI_FILE,
                   ("000", "LFL"),
                   ("DISK%NN%", "LEC"),
                   dummy_set
                   ),
        "MI1CDalt" : (SINGLE_FILE, # crap
                  ("MONKEY", "000"), # TODO: confirm if this is correct
                  ("MONKEY", "001"),
                  dummy_set
                  ),
        "MI1CD" : (SINGLE_FILE,
                  ("MONKEY1", "000"), # TODO: confirm if this is correct
                  ("MONKEY1", "001"),
                  dummy_set
                  ),
        "MI2" : (SINGLE_FILE,
                ("MONKEY2", "000"),
                ("MONKEY2", "001"),
                dummy_set
                ),
        "FOA" : (SINGLE_FILE, 
                ("ATLANTIS", "000"),
                ("ATLANTIS", "001"),
                dummy_set
                ),
        "DOTT" : (SINGLE_FILE,
                 ("TENTACLE", "000"),
                 ("TENTACLE", "001"),
                 dummy_set
                 ),
        "SAMalt" : (SINGLE_FILE, # floppy version
                ("SAMNMAX", "SM0"), # TODO: implement searching for alternate resource names
                ("SAMNMAX", "SM1"),
                dummy_set
                ),
        "SAM" : (SINGLE_FILE, # talkie version
                ("SAMNMAX", "000"), # TODO: implement searching for alternate resource names 
                ("SAMNMAX", "001"),
                dummy_set
                )

    }
    
    def unpack(self):       
        # Get our dispatchers that know about the version-specific stuff.
        assign_dispatchers(*dispatchers.DispatcherFactory(control.global_args.scumm_version))
        # Get resource names
        try:
            spanning, (index_name, index_ext), (resource_name, resource_ext), ignored_res = self.RESOURCE_FILE_TEMPLATES_PER_GAME[control.global_args.game]
        except KeyError:
            raise util.ScummPackerException("No resource file template defined for game: %s" % control.global_args.game)
        # HACK: support alternative resource names. TODO: do this better.
        if control.global_args.game.endswith('alt'):
            control.global_args.game = control.global_args.game[:-3]

        # Load from resources
        logging.normal("Loading from game resources...")
        base_path = control.global_args.input_file_name
        assert os.path.isdir(base_path)
        resources = []
        resource_counter = 1
        
        # read index
        with file(os.path.join(base_path, index_name + "." + index_ext), 'rb') as index_file:
            index_block = control.index_dispatcher.dispatch_and_load_from_resource(index_file)
            
        # read resources, which could be split across multiple disk files.
        while resource_counter < 100:
            # Look for 01.LFL, 02.LFL or DISK01.LEC, DISK02.LEC etc until no more found.
            rfn = resource_name.replace("%NN%", str(resource_counter).zfill(2)) + "." + resource_ext
            print rfn
            if rfn in ignored_res:
                resource_counter += 1
                continue
            res_name = os.path.join(base_path, rfn)
            # SCUMM v3 can have gaps in room numbering/file names.
            if not os.path.isfile(res_name):
                if spanning == self.SINGLE_ROOM_MULTI_FILE:
                    resource_counter += 1
                    continue
                else:
                    break
            logging.normal("Reading from %s" % res_name)
            control.disk_spanning_counter = resource_counter
            with file(res_name, 'rb') as res_file:
                resources.append(control.block_dispatcher.dispatch_and_load_from_resource(res_file))
            if spanning == self.SINGLE_FILE:
                break
            else:
                resource_counter += 1
            
        # Save to files
        logging.normal("Saving to files...")        
        base_path = control.global_args.output_file_name
        assert os.path.isdir(base_path)        
        for i, resource_block in enumerate(resources):
            # SCUMM V3 can have gaps in numbering, so LFL Container block
            #  handles creation of the output resource folders.
            if spanning == self.SINGLE_ROOM_MULTI_FILE:
                disk_path = base_path
            else:
                disk_path = os.path.join(base_path, resource_name.replace("%NN%", str(i + 1).zfill(2)))
            logging.normal("Saving resource %i to %s" % (i, disk_path))
            if not os.path.isdir(disk_path):
                os.mkdir(disk_path)
            resource_block.save_to_file(disk_path)
        index_block.save_to_file(base_path)
    
    def pack(self):
        # Get our dispatchers that know about the version-specific stuff.
        assign_dispatchers(*dispatchers.DispatcherFactory(control.global_args.scumm_version))
        # Get resource names
        try:
            spanning, (index_name, index_ext), (resource_name, resource_ext), ignored_res = self.RESOURCE_FILE_TEMPLATES_PER_GAME[control.global_args.game]
        except KeyError:
            raise util.ScummPackerException("No resource file template defined for game: %s" % control.global_args.game)
        # Load from files
        logging.normal("Loading from files...")
        assert os.path.isdir(control.global_args.input_file_name)
        base_path = control.global_args.input_file_name
        resources = []
        resource_counter = 1
        # load folders, which represents disk spanning.
        while resource_counter < 100:
            # Look for DISK01, DISK02 etc until no more found.
            res_name = os.path.join(base_path, resource_name.replace("%NN%", str(resource_counter).zfill(2)))
            if not os.path.isdir(res_name):
                # SCUMM V3 names files by room number, which can have gaps.
                if spanning == self.SINGLE_ROOM_MULTI_FILE:
                    resource_counter += 1
                    continue
                else:
                    break
            logging.normal("Reading from %s" % res_name)
            control.disk_spanning_counter = resource_counter
            resources.append(control.file_dispatcher.dispatch_and_load_from_file(res_name))
            if spanning == self.SINGLE_FILE:
                break
            else:
                resource_counter += 1
        index_block = control.index_dispatcher.dispatch_and_load_from_file(control.global_args.input_file_name)
        
        # Save to resources
        logging.normal("Saving to game resources...")        
        base_path = control.global_args.output_file_name
        assert os.path.isdir(base_path)
        for i, resource_block in enumerate(resources):
            if spanning == self.SINGLE_ROOM_MULTI_FILE:
                res_num = int(resource_block.name)
            else:
                res_num = i + 1
            disk_file_name = os.path.join(base_path, (resource_name + "." + resource_ext).replace("%NN%", str(res_num).zfill(2)))
            logging.normal("Saving to %s" % disk_file_name)
            control.disk_spanning_counter = i + 1
            with file(disk_file_name, 'wb') as disk_file:
                resource_block.save_to_resource(disk_file)

        with file(os.path.join(base_path, index_name + "." + index_ext), 'wb') as index_file:
            index_block.save_to_resource(index_file)

            
global_res_handler = ResourceHandler()