import xml.etree.ElementTree as et
import scummpacker_control as control
import scummpacker_util as util
from blocks.v6_base import BlockDefaultV6

class BlockCDHDV6(BlockDefaultV6):
    name = "CDHD"
    xml_structure = (
        ("code", 'n', (
            ("x", 'i', 'x'),
            ("y", 'i', 'y'),
            ("width", 'i', 'width'),
            ("height", 'i', 'height'),
            ("flags", 'h', 'flags'),
            ("parent", 'i', 'parent'),
            ("walk_x", 'i', 'walk_x'),
            ("walk_y", 'i', 'walk_y'),
            ("actor_dir", 'i', 'actor_dir')
            )
        ),
    )
    struct_data = {
        'size' : 17,
        'format' : "<5H2B2hB",
        'attributes' :
            ('obj_id',
            'x',
            'y',
            'width',
            'height',
            'flags',
            'parent',
            'walk_x',
            'walk_y',
            'actor_dir')
    }

    def _read_data(self, resource, start, decrypt, room_start=0):
        """
          obj id    : 16le
          x         : 16le
          y         : 16le
          width     : 16le
          height    : 16le
          flags     : 8
          parent    : 8
          walk_x    : 16le signed
          walk_y    : 16le signed
          actor dir : 8 (direction the actor will look at when standing in front
                         of the object)
        """
        self.read_struct_data(self.struct_data, resource, decrypt)

        # HACK: Sam n Max has two OBCD entries for object ID 561, but none for
        #  object ID 560 (room 58). Both objects are "rushmore-dino-jaw".
        #  Work around it by manually re-assigning the ID based on the block's
        #  position in the file.
        #  The two OBCD blocks for 561 are actually different, but I'm
        #  not sure how to decide which is which, so I've just chosen the first one.
        if (control.global_args.game == "SAM" and
                self.obj_id == 561 and
                (start == 0x00A6CF8F or # floppy version
                 start == 0x00A7C4F2)): # talkie version
            self.obj_id = 560

    def load_from_file(self, path):
        self.name = "CDHD"
        self.size = self.struct_data['size'] + 8 # data + header
        self._load_header_from_xml(path)

    def _load_header_from_xml(self, path):
        tree = et.parse(path)
        root = tree.getroot()

        # Shared
        obj_id = util.xml2int(root.find("id").text)
        self.obj_id = obj_id

        self.read_xml_node(root)

    def _write_data(self, resource, encrypt):
        """ Assumes it's writing to a resource."""
        self.write_struct_data(self.struct_data, resource, encrypt)

