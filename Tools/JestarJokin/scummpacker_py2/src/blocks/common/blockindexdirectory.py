import logging
import scummpacker_control as control
import scummpacker_util as util
from abstractblock import AbstractBlock

class BlockIndexDirectory(AbstractBlock):
    """ Generic index directory """
    DIR_TYPES = NotImplementedError("This property must be overridden by inheriting classes.")
    MIN_ENTRIES = NotImplementedError("This property must be overridden by inheriting classes.")

    def _read_data(self, resource, start, decrypt, room_start=0):
        raise NotImplementedError("This method must be overridden by inheriting classes.")

    def save_to_file(self, path):
        """This block is generated when saving to a resource."""
        return

    def save_to_resource(self, resource, room_start=0):
        # is room_start required? nah, just there for interface compliance.
        #for i, key in enumerate()
        items = control.global_index_map.items(self.DIR_TYPES[self.name])
        item_map = {}
        if len(items) == 0:
            logging.info("No indexes found for block type \"" + self.name + "\" - are there any files of this block type?")
            num_items = self.MIN_ENTRIES[control.global_args.game][self.name]
        else:
            items.sort(cmp=lambda x, y: cmp(x[1], y[1])) # sort by resource number
            # Need to pad items out, so take last entry's number as the number of items
            num_items = items[-1][1]
            if self.name in self.MIN_ENTRIES[control.global_args.game] and \
               num_items < self.MIN_ENTRIES[control.global_args.game][self.name]:
                num_items = self.MIN_ENTRIES[control.global_args.game][self.name]
            # Create map with reversed key/value pairs
            for i, j in items:
                item_map[j] = i

        # Bleeech
        self.size = 5 * num_items + 2 + self.block_name_length + 4
        self._write_header(resource, True)

        resource.write(util.int2str(num_items, 2, crypt_val=self.crypt_value))
        self._save_table_data(resource, num_items, item_map)

    def _save_table_data(self, resource, num_items, item_map):
        for i in xrange(num_items):
            if not i in item_map:
                # write dummy values for unused item numbers.
                resource.write(util.int2str(0, 1, crypt_val=self.crypt_value))
            else:
                room_num, _ = item_map[i]
                resource.write(util.int2str(room_num, 1, crypt_val=self.crypt_value))
        for i in xrange(num_items):
            if not i in item_map:
                # write dummy values for unused item numbers.
                resource.write(util.int2str(0, 4, crypt_val=self.crypt_value))
            else:
                _, offset = item_map[i]
                resource.write(util.int2str(offset, 4, crypt_val=self.crypt_value))

