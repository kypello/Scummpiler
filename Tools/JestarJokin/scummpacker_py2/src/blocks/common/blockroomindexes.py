from collections import defaultdict
import scummpacker_control as control
from abstractblock import AbstractBlock

class BlockRoomIndexes(AbstractBlock):
    """Directory of offsets to ROOM blocks. Also maps disk spanning.

    Don't really seem to be used much for V5 and LOOM CD. It is used in Monkey Island EGA/VGA.

    Each game seems to have a different padding length."""
    name = NotImplementedError("This property must be overridden by inheriting classes.")
    DEFAULT_PADDING_LENGTHS = NotImplementedError("This property must be overridden by inheriting classes.")
    default_disk_or_room_number = 0
    default_offset = 0

    def __init__(self, *args, **kwds):
        # Store a mapping of disk numbers to room numbers.
        self.disk_spanning = defaultdict(list)
        self.padding_length = kwds.get('padding_length',
                                       self.DEFAULT_PADDING_LENGTHS[control.global_args.game])
        super(BlockRoomIndexes, self).__init__(*args, **kwds)

    def _read_data(self, resource, start, decrypt, room_start=0):
        raise NotImplementedError("This method must be overridden by inheriting classes.")

    def save_to_file(self, path):
        """This block is generated when saving to a resource."""
        pass

    def save_to_resource(self, resource, room_start=0):
        raise NotImplementedError("This method must be overridden by inheriting classes.")

