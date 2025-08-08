import os
import scummpacker_control as control
import scummpacker_util as util
from v4_base import BlockContainerV4

class LFLContainerV3(BlockContainerV4):
    """
    SCUMM V3 uses a separate LFL for each room. However, the files also store
    other blocks, like costumes, sounds, etc. This acts as a generic container.

    There is a lot of fudging of global index map data, to cram V3 support into
    the framework developed for V4/V5.
    
    However,
    Zak room 47 does not contain a room; it contains a "NL" block (with
    SL, EX, EN, and LC sub-blocks), and scripts and sounds.
    """
    def load_from_resource(self, resource, room_start=0):
        path = resource.name
        # Name is "01" component of "01.LFL"
        self.name = os.path.splitext(os.path.basename(path))[0]

        # HACK: LF blocks don't exist, but we use it to keep track of room numbers.
        # We don't need to track FO, since the room is always the first block in
        #  the resource file, and starts at offset 0.
        # Not sure what to do with the disk values. In original index files,
        #  disk numbers are 0x31, 0x32, 0x33, 0x34 etc.
        control.global_index_map.map_index('LF', (control.disk_spanning_counter, 0), int(self.name))
        control.global_index_map.map_index('FO', int(self.name), 0)
        control.global_index_map.map_index("Disk",
                                           int(self.name),
                                           int(self.name))
        start = resource.tell()
        resource.seek(0, os.SEEK_END)
        self.size = resource.tell()
        resource.seek(start, os.SEEK_SET)
        self._read_data(resource, start, True, room_start)

    def load_from_file(self, path):
        self.name = os.path.split(path)[1]
        self.children = []
        self.order_map = {}

        file_list = os.listdir(path)
        if "order.xml" in file_list:
            file_list.remove("order.xml")
            self._load_order_from_xml(os.path.join(path, "order.xml"))

        # HACK
        control.global_index_map.map_index('LF', (int(self.name), 0), int(self.name))

        for f in file_list:
            b = control.file_dispatcher.dispatch_next_block(f)
            if b != None:
                b.load_from_file(os.path.join(path, f))
                self.append(b)

    def save_to_resource(self, resource, room_start=0):
        """ 
        HACK:
        Use this container's name as the disk number.
        
        HACK:
        Try to look up the current room's offset. If it does not exist, we
        must not have encountered it when reading from files. So, just
        create a dummy entry.

        This supports Zak room 47 which has no room in the LFL file.
        """
        try:
            control.global_index_map.get_index('FO', int(self.name))
        except util.ScummPackerUnrecognisedIndexException, suie:
            control.global_index_map.map_index('FO', int(self.name), 0)
        
        # HACK
        control.disk_spanning_counter = int(self.name)
        # process children
        for c in self.children:
            c.save_to_resource(resource, room_start)

    def save_to_file(self, path):
        newpath = self._create_directory(path)
        self._save_children(newpath)
        self._save_order_to_xml(newpath)

    def _read_data(self, resource, start, decrypt, room_start=0):
        end = start + self.size
        while resource.tell() < end:
            block = control.block_dispatcher.dispatch_next_block(resource)
            block.load_from_resource(resource, room_start)
            self.append(block)

    def generate_file_name(self):
        return self.name