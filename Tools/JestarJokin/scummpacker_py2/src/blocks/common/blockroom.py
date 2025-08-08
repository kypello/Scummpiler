import logging
import scummpacker_control as control
from scriptblockcontainer import ScriptBlockContainer
from objectblockcontainer import ObjectBlockContainer
from blockcontainer import BlockContainer

class BlockRoom(BlockContainer): # also globally indexed
    def __init__(self, *args, **kwds):
        super(BlockRoom, self).__init__(*args, **kwds)
        self._init_class_data()

    def _init_class_data(self):
        self.name = None
        self.lf_name = None
        self.room_offset_name = None
        self.script_types = frozenset()
        self.object_types = frozenset()
        self.object_between_types = frozenset() # workaround for V4 "NL" and "SL"
        self.object_image_type = None
        self.object_code_type = None
        self.num_scripts_type = None
        self.script_container_class = ScriptBlockContainer
        self.object_container_class = ObjectBlockContainer
        self.dodgy_offsets = {} # workaround for junk room data in MI1EGA/MI1VGA
        raise NotImplementedError("This method must be overriden by a concrete class.")

    def _read_data(self, resource, start, decrypt, room_start=0):
        end = start + self.size
        object_container = self.object_container_class(self.block_name_length, self.crypt_value)
        script_container = self.script_container_class(self.block_name_length, self.crypt_value)
        while resource.tell() < end:
            if self._should_skip_room(resource):
                logging.warning("Skipping known dodgy room data at offset %s" % resource.tell())
                resource.seek(end)
                break
            block = control.block_dispatcher.dispatch_next_block(resource)
            block.load_from_resource(resource, room_start)
            if block.name in self.script_types:
                script_container.append(block)
            elif block.name == self.object_image_type:
                object_container.add_image_block(block)
            elif block.name == self.object_code_type:
                object_container.add_code_block(block)
            elif block.name in self.object_between_types:
                object_container.add_between_block(block)
            elif block.name == self.num_scripts_type: # ignore this since we can generate it
                del block
                continue
            else:
                self.append(block)
        self.append(object_container)
        self.append(script_container)

    def save_to_resource(self, resource, room_start=0):
        location = resource.tell()
        room_num = control.global_index_map.get_index(self.lf_name, (control.disk_spanning_counter, room_start))
        logging.debug("Saving room: %s" % room_num)
        control.global_index_map.map_index(self.room_offset_name, room_num, location)
        super(BlockRoom, self).save_to_resource(resource, room_start)

    def _should_skip_room(self, resource):
        if control.global_args.game in self.dodgy_offsets:
            doff_set = self.dodgy_offsets[control.global_args.game]
            if resource.tell() - 4 - self.block_name_length in doff_set:
                return True
        return False
