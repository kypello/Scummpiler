import os
from blockcontainer import BlockContainer

class BlockLucasartsEntertainmentContainer(BlockContainer):
    def __init__(self, *args, **kwds):
        super(BlockLucasartsEntertainmentContainer, self).__init__(*args, **kwds)
        self._init_class_data()

    def _init_class_data(self):
        self.name = NotImplementedError("This property must be overridden by inheriting classes.")
        self.OFFSET_CLASS = NotImplementedError("This property must be overridden by inheriting classes.")

    def load_from_file(self, path):
        # assume input path is actually the directory containing the LECF dir
        super(BlockLucasartsEntertainmentContainer, self).load_from_file(os.path.join(path, self.name))

    def save_to_resource(self, resource, room_start=0):
        start = resource.tell()

        # write dummy header
        self._write_dummy_header(resource, True)

        # write dummy LOFF
        loff_start = resource.tell()
        loff_block = self.OFFSET_CLASS(self.block_name_length, self.crypt_value)
        num_rooms = len(self.children)
        loff_block.write_dummy_block(resource, num_rooms)

        # process children
        for c in self.children:
            c.save_to_resource(resource, room_start)

        # go back and write size of LECF block (i.e. the whole ".001" file)
        self.size = resource.tell() - start
        resource.flush()
        end = resource.tell()
        resource.seek(start, os.SEEK_SET)
        self._write_header(resource, True)

        # go back and write the LOFF block
        loff_block.save_to_resource(resource, room_start)
        resource.seek(end, os.SEEK_SET)

    def __repr__(self):
        childstr = [str(c) for c in self.children]
        return "[" + self.name + ", " + ", \n".join(childstr) + "]"

