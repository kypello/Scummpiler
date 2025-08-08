import xml.etree.ElementTree as et
import logging
import os
import scummpacker_control as control
import scummpacker_util as util
from abstractblock import AbstractBlock

class BlockContainer(AbstractBlock):
    block_ordering = [
        # To be overridden in version-specific deriving classes.
    ]

    def __init__(self, *args, **kwds):
        super(BlockContainer, self).__init__(*args, **kwds)
        self.children = []
        self.order_map = {}

    def _read_data(self, resource, start, decrypt, room_start=0):
        end = start + self.size
        while resource.tell() < end:
            block = control.block_dispatcher.dispatch_next_block(resource)
            block.load_from_resource(resource, room_start)
            self.append(block)

    def _find_block_rank_lookup_name(self, block):
        rank_lookup_name = block.name
        # dumb crap here but I'm sick of working on this crappy piece of software
        if rank_lookup_name[:2] == "ZP" or rank_lookup_name[:2] == "IM":
            rank_lookup_name = rank_lookup_name[:2]
        if rank_lookup_name == "\x00\x00":
            rank_lookup_name = "00"
        return rank_lookup_name

    def _find_block_rank(self, block):
        rank_lookup_name = self._find_block_rank_lookup_name(block)
        try:
            block_rank = self.block_ordering.index(rank_lookup_name) # requires all block types are listed
        except ValueError:
            logging.error("Oops! The container block '%s' doesn't know how to order blocks of type '%s'! Get me a developer, STAT!" %
                        (self.name, rank_lookup_name))
            raise util.ScummPackerException("Unknown block wanted to be ranked/ordered: %s" % rank_lookup_name)
        return block_rank

    def append(self, block):
        """Maintains sorted order for children."""
        rank_lookup_name = self._find_block_rank_lookup_name(block)
        block_rank = self._find_block_rank(block)

        for i, c in enumerate(self.children):
            c_rank = self._find_block_rank(c)
            # Same block type, so look for a specified order for this block type.
            if c_rank == block_rank:
                if not rank_lookup_name in self.order_map:
                    continue # no order specified, continue iteration, appending after all existing blocks of this type
                order_list = self.order_map[rank_lookup_name]
                if not block.index in order_list:
                    continue # if the order of the added block is not known, append after existing blocks
                if not c.index in order_list:
                    self.children.insert(i, block)
                    return # if existing block has no order but new block done, insert new block before unordered block.
                block_order = order_list.index(block.index)
                c_order = order_list.index(c.index)
                if c_order > block_order:
                    self.children.insert(i, block)
                    return # existing block comes after block being added
            elif c_rank > block_rank:
                self.children.insert(i, block)
                return
        self.children.append(block)

    def save_to_file(self, path):
        newpath = self._create_directory(path)
        self._save_children(newpath)
        self._save_order_to_xml(newpath)

    def _create_directory(self, start_path):
        newpath = os.path.join(start_path, self.generate_file_name())
        if not os.path.isdir(newpath):
            os.mkdir(newpath) # throws an exception if can't create dir
        return newpath

    def _save_children(self, path):
        for child in self.children:
            child.save_to_file(path)

    def _save_order_to_xml(self, path):
        root = et.Element("order")

        curr_type = None
        ol_node = None
        for c in self.children:
            if not hasattr(c, "index") or c.index is None:
                continue
            block_type = self._find_block_rank_lookup_name(c)
            # if block type is new, create new list
            if block_type != curr_type:
                ol_node = et.SubElement(root, "order-list")
                ol_node.set("block-type", block_type)
                curr_type = block_type
            et.SubElement(ol_node, "order-entry").text = util.int2xml(c.index)

        if len(root.getchildren()) == 0:
            return

        util.indent_elementtree(root)
        et.ElementTree(root).write(os.path.join(path, "order.xml"))

    def load_from_file(self, path):
        self.name = os.path.split(path)[1]
        self.children = []
        self.order_map = {}

        file_list = os.listdir(path)
        if "order.xml" in file_list:
            file_list.remove("order.xml")
            self._load_order_from_xml(os.path.join(path, "order.xml"))

        for f in file_list:
            b = control.file_dispatcher.dispatch_next_block(f)
            if b != None:
                b.load_from_file(os.path.join(path, f))
                self.append(b)

    def _load_order_from_xml(self, path):
        if not os.path.isfile(path):
            # If order.xml does not exist, use whatever order we want.
            # Should not get here...
            return

        tree = et.parse(path)
        root = tree.getroot()

        order_map = {}

        for ol in root.findall("order-list"):
            block_type = ol.get("block-type")
            order_list = []
            for o in ol.findall("order-entry"):
                order_list.append(util.xml2int(o.text))
            order_map[block_type] = order_list

        self.order_map = order_map

    def save_to_resource(self, resource, room_start=0):
        start = resource.tell()

        # write dummy header
        self._write_dummy_header(resource, True)
        # process children
        for c in self.children:
            c.save_to_resource(resource, room_start)

        # go back and write size of block
        end = resource.tell()
        self.size = end - start
        resource.flush()
        resource.seek(start, os.SEEK_SET)
        self._write_header(resource, True)
        resource.seek(end, os.SEEK_SET)

    def generate_file_name(self):
        return self.name

    def __repr__(self):
        childstr = [str(c) for c in self.children]
        return "[" + self.name + ", " + ", ".join(childstr) + "]"


