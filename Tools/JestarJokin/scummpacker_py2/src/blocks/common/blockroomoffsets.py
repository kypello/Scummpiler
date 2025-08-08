import scummpacker_control as control
import scummpacker_util as util
from abstractblock import AbstractBlock

class BlockRoomOffsets(AbstractBlock):
    name = NotImplementedError("This property must be overridden by inheriting classes.") # string
    LFLF_NAME = NotImplementedError("This property must be overridden by inheriting classes.") # class name (string)
    ROOM_OFFSET_NAME = NotImplementedError("This property must be overridden by inheriting classes.") # class name (string)
    OFFSET_POINTS_TO_ROOM = NotImplementedError("This property must be overridden by inheriting classes.") # boolean
    disk_lookup_name = NotImplementedError("This property must be overridden by inheriting classes.") # string

    def _read_data(self, resource, start, decrypt, room_start=0):
        num_rooms = util.str2int(resource.read(1),
                                    crypt_val=(self.crypt_value if decrypt else None))

        for _ in xrange(num_rooms):
            room_no = util.str2int(resource.read(1),
                                      crypt_val=(self.crypt_value if decrypt else None))
            if self.OFFSET_POINTS_TO_ROOM:
                room_offset = util.str2int(resource.read(4),
                                              crypt_val=(self.crypt_value if decrypt else None))
                lf_offset = room_offset - self.block_name_length - 4
            else:
                lf_offset = util.str2int(resource.read(4),
                                            crypt_val=(self.crypt_value if decrypt else None))
                room_offset = lf_offset + 2 + self.block_name_length + 4 # add 2 bytes for the room number/index of LF block.
            control.global_index_map.map_index(self.LFLF_NAME, (control.disk_spanning_counter, lf_offset), room_no)
            control.global_index_map.map_index(self.ROOM_OFFSET_NAME, room_no, room_offset) # HACK

    def save_to_file(self, path):
        """Don't need to save offsets since they're calculated when packing."""
        return

    def save_to_resource(self, resource, room_start=0):
        """This method should only be called after write_dummy_block has been invoked,
        otherwise this block may have no size attribute initialised."""
        # Write name/size (probably again, since write_dummy_block also writes it)
        self._write_header(resource, True)
        # Write number of rooms, followed by offset table
        # Possible inconsistency, in that this uses the global index map for ROOM blocks,
        #  whereas the "write_dummy_block" just looks at the number passed in, which
        #  comes from the number of entries in the file system.
        if self.OFFSET_POINTS_TO_ROOM:
            room_table = []
            for room_item in \
            sorted(control.global_index_map.items(self.ROOM_OFFSET_NAME)):
                # Don't write rooms not on this disk
                room_num = room_item[0]
                room_disk = control.global_index_map.get_index(self.disk_lookup_name, room_num)
                if room_disk == control.disk_spanning_counter:
                    room_table.append(room_item)

            num_of_rooms = len(room_table)
            resource.write(util.int2str(num_of_rooms, 1, crypt_val=self.crypt_value))
            for room_num, room_offset in room_table:
                room_num = int(room_num)
                resource.write(util.int2str(room_num, 1, crypt_val=self.crypt_value))
                resource.write(util.int2str(room_offset, 4, util.LE, self.crypt_value))
        else:
            room_table = []
            for lflf_item in \
            sorted(control.global_index_map.items(self.LFLF_NAME)):
                # Don't write rooms not on this disk
                room_num = lflf_item[1]
                room_disk = control.global_index_map.get_index(self.disk_lookup_name, room_num)
                if room_disk == control.disk_spanning_counter:
                    room_table.append(lflf_item)

            num_of_rooms = len(room_table)
            resource.write(util.int2str(num_of_rooms, 1, crypt_val=self.crypt_value))
            for lflf_item, room_num in room_table:
                if isinstance(lflf_item, tuple):
                    lf_offset = lflf_item[1]
                else:
                    lf_offset = lflf_item
                room_num = int(room_num)
                resource.write(util.int2str(room_num, 1, crypt_val=self.crypt_value))
                resource.write(util.int2str(lf_offset, 4, util.LE, self.crypt_value))

    def write_dummy_block(self, resource, num_rooms):
        """This method should be called before save_to_resource. It just
        reserves space until the real block is written.

        The reason for doing this is that the block begins at the start of the
        resource file, but contains the offsets of all of the room blocks, which
        won't be known until after they've all been written."""
        block_start = resource.tell()
        self._write_dummy_header(resource, True)
        resource.write(util.int2str(num_rooms, 1, crypt_val=self.crypt_value))
        for _ in xrange(num_rooms):
            resource.write(util.int2str(0, 1, crypt_val=self.crypt_value) * 5)
        block_end = resource.tell()
        self.size = block_end - block_start

