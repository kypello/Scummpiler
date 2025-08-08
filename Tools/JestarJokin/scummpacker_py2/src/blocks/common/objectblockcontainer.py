import xml.etree.ElementTree as et
import os
import re
import scummpacker_control as control
import scummpacker_util as util

class ObjectBlockContainer(object):
    """ Contains objects, which contain image and code blocks."""

    def __init__(self, block_name_length, crypt_value, *args, **kwds):
        self._init_class_data()
        self.objects = {}
        self.obj_id_name_length = 4 # should be increased depending on number of objects in the game
        self.block_name_length = block_name_length
        self.crypt_value = crypt_value
        self.name = "objects"
        self.order_map = { self.obcd_name : [], self.obim_name : [] }
        self.between_blocks = []

    def _init_class_data(self):
        self.obcd_name = None # string
        self.obim_name = None # string
        self.obcd_class = None # actual class to be instantiated when reading from file
        self.obim_class = None # ditto
        raise NotImplementedError("This method must be overriden by a concrete class.")

    def add_code_block(self, block):
        if not block.obj_id in self.objects:
            self.objects[block.obj_id] = [None, None] # pos1 = image, pos2 = code
        self.objects[block.obj_id][1] = block
        self.order_map[self.obcd_name].append(block.obj_id)

    def add_image_block(self, block):
        if not block.obj_id in self.objects:
            self.objects[block.obj_id] = [None, None] # pos1 = image, pos2 = code
        self.objects[block.obj_id][0] = block
        self.order_map[self.obim_name].append(block.obj_id)

    def add_between_block(self, block):
        """Workaround for SCUMM V4 which has "SL" and "NL" blocks
        in between the OI and OC blocks."""
        self.between_blocks.append(block)

    def save_to_file(self, path):
        objects_path = os.path.join(path, self.generate_file_name())
        if not os.path.isdir(objects_path):
            os.mkdir(objects_path) # throws an exception if can't create dir
        for objimage, objcode in self.objects.values():
            # New path name = Object ID + object name (removing trailing spaces)
            if objcode is None or objimage is None:
                raise util.ScummPackerException("Object is missing either the code block or the image block! Dump follows.\n%s" % (self.objects,))
            obj_id = objcode.obj_id
            obj_name = objcode.obj_name
            obj_path_name = str(obj_id).zfill(self.obj_id_name_length) + "_" + util.discard_invalid_chars(obj_name).rstrip()
            newpath = os.path.join(objects_path, obj_path_name)
            if not os.path.isdir(newpath):
                os.mkdir(newpath) # throws an exception if can't create dir
            objimage.save_to_file(newpath)
            objcode.save_to_file(newpath)
            self._save_header_to_xml(newpath, objimage, objcode)
        self._save_order_to_xml(objects_path)
        # Workaround for V4 "SL" and "NL" blocks.
        for b in self.between_blocks:
            b.save_to_file(objects_path)

    def save_to_resource(self, resource, room_start=0):
        self._save_object_images_to_resource(resource, room_start)
        self._save_between_blocks_to_resource(resource, room_start)
        self._save_object_codes_to_resource(resource, room_start)

    def _save_object_images_to_resource(self, resource, room_start):
        object_keys = self.objects.keys()
        # Write all image blocks first
        object_keys = util.ordered_sort(object_keys, self.order_map[self.obim_name])
        for obj_id in object_keys:
            self.objects[obj_id][0].save_to_resource(resource, room_start)

    def _save_between_blocks_to_resource(self, resource, room_start):
        for b in self.between_blocks:
            b.save_to_resource(resource, room_start)

    def _save_object_codes_to_resource(self, resource, room_start):
        object_keys = self.objects.keys()
        # Write all object code/names
        object_keys = util.ordered_sort(object_keys, self.order_map[self.obcd_name])
        for obj_id in object_keys:
            self.objects[obj_id][1].save_to_resource(resource, room_start)

    def _save_header_to_xml(self, path, objimage, objcode):
        # Save the joined header information as XML
        root = et.Element("object")

        et.SubElement(root, "name").text = util.escape_invalid_chars(objcode.obj_name)
        et.SubElement(root, "id").text = util.int2xml(objcode.obj_id)

        # OBIM
        objimage.generate_xml_node(root)

        # OBCD
        objcode.generate_xml_node(root)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "OBHD.xml"))

    def _save_order_to_xml(self, path):
        root = et.Element("order")

        for block_type, order_list in self.order_map.items():
            order_list_node = et.SubElement(root, "order-list")
            order_list_node.set("block-type", block_type)
            for o in order_list:
                et.SubElement(order_list_node, "order-entry").text = util.int2xml(o)

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "order.xml"))

    def load_from_file(self, path):
        file_list = os.listdir(path)

        re_pattern = re.compile(r"[0-9]{" + str(self.obj_id_name_length) + r"}_.*")
        object_dirs = [f for f in file_list if re_pattern.match(f) != None]
        self.order_map = { self.obcd_name : [], self.obim_name : [] }
        for od in object_dirs:
            new_path = os.path.join(path, od)

            objimage = self.obim_class(self.block_name_length, self.crypt_value)
            objimage.load_from_file(new_path)
            self.add_image_block(objimage)

            objcode = self.obcd_class(self.block_name_length, self.crypt_value)
            objcode.load_from_file(new_path)
            self.add_code_block(objcode)

        file_list = [f for f in file_list if not f in object_dirs]
        for f in file_list:
            b = control.file_dispatcher.dispatch_next_block(f)
            if b != None:
                b.load_from_file(os.path.join(path, f))
                self.between_blocks.append(b)

        self._load_order_from_xml(path)

    def _load_order_from_xml(self, path):
        order_fname = os.path.join(path, "order.xml")
        if not os.path.isfile(order_fname):
            # If order.xml does not exist, use whatever order we want.
            return

        tree = et.parse(order_fname)
        root = tree.getroot()

        loaded_order_map = self.order_map
        self.order_map = { self.obcd_name : [], self.obim_name : [] }

        for order_list in root.findall("order-list"):
            block_type = order_list.get("block-type")

            for o in order_list.findall("order-entry"):
                if not block_type in self.order_map:
                    self.order_map[block_type] = []
                self.order_map[block_type].append(util.xml2int(o.text))

            # Retain order of items loaded but not present in order.xml
            if block_type in loaded_order_map:
                extra_orders = [i for i in loaded_order_map[block_type] if not i in self.order_map[block_type]]
                self.order_map[block_type].extend(extra_orders)

    def generate_file_name(self):
        return "objects"

    def __repr__(self):
        childstr = ["obj_" + str(c) for c in self.objects.keys()]
        return "[" + self.obim_name + " & " + self.obcd_name + ", " + "[" + ", ".join(childstr) + "] " + "]"

