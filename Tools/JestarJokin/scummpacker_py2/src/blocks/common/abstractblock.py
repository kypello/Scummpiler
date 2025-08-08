import array
import logging
import os
import struct
import scummpacker_util as util

class AbstractBlock(object):
    xml_structure = tuple() # placeholder
    struct_data = dict() # placeholder. Must have attributes "size", "format", and "attributes".

    def __init__(self, block_name_length, crypt_value, *args, **kwds):
        super(AbstractBlock, self).__init__(*args, **kwds)
        self.block_name_length = block_name_length
        self.crypt_value = crypt_value

    def load_from_resource(self, resource, room_start=0):
        start = resource.tell()
        self._read_header(resource, True)
        #logging.debug("%s loading from room start %s" % (self.name, room_start))
        self._read_data(resource, start, True, room_start)

    def skip_from_resource(self, resource, room_start=0):
        start = resource.tell()
        self._read_header(resource, True)
        end = start + self.size
        logging.warn('Skipping block "%s" at offset %d' % (self.name, start))
        resource.seek(end)

    def save_to_resource(self, resource, room_start=0):
        self._write_header(resource, True)
        self._write_data(resource, True)

    def _read_header(self, resource, decrypt):
        # Different in old format resources
        raise NotImplementedError("This method must be overriden by a concrete class.")

    def _read_data(self, resource, start, decrypt, room_start=0):
        data = self._read_raw_data(resource, self.size - (resource.tell() - start), decrypt)
        self.data = data

    def _read_name(self, resource, decrypt):
        name = resource.read(self.block_name_length)
        if decrypt:
            name = util.crypt(name, self.crypt_value)
        return name

    def _read_size(self, resource, decrypt):
        size = resource.read(4)
        if decrypt:
            size = util.crypt(size, self.crypt_value)
        return util.str2int(size, is_BE=util.BE)

    def _read_raw_data(self, resource, size, decrypt):
        data = array.array('B')
        data.fromfile(resource, size)
        if decrypt:
            data = util.crypt(data, self.crypt_value)
        return data

    def load_from_file(self, path):
        block_file = file(path, 'rb')
        start = block_file.tell()
        self._read_header(block_file, False)
        self._read_data(block_file, start, False)
        block_file.close()

    def save_to_file(self, path):
        outfile = file(os.path.join(path, self.generate_file_name()), 'wb')
        self._write_header(outfile, False)
        self._write_data(outfile, False)
        outfile.close()

    def _write_header(self, outfile, encrypt):
        # Different in old format resources
        raise NotImplementedError("This method must be overriden by a concrete class.")

    def _write_dummy_header(self, outfile, encrypt):
        """Writes placeholder information (block name, block size of 0)"""
        raise NotImplementedError("This method must be overriden by a concrete class.")

    def _write_data(self, outfile, encrypt):
        self._write_raw_data(outfile, self.data, encrypt)

    def _write_raw_data(self, outfile, data, encrypt):
        data_out = data
        if encrypt:
            data_out = util.crypt(data_out, self.crypt_value)
        data_out.tofile(outfile)

    def generate_file_name(self):
        return self.name + ".dmp"

    def __repr__(self):
        return "[" + self.name + "]"

    def generate_xml_node(self, parent_node):
        """ Adds a new XML node to the given parent node.

        Not used by every block. To use it, the "xml_structure" property
        should be populated, and this method must be specifically called,
        either from a containing block, or from the "save_to_file" method."""
        util.xml_helper.write(self, parent_node, self.xml_structure)

    def read_xml_node(self, parent_node):
        """ Reads data from the given root node.

        Not used by every block. To use it, the "xml_structure" property
        should be populated, and this method must be specifically called,
        either from a containing block, or from the "load_from_file" method."""
        util.xml_helper.read(self, parent_node, self.xml_structure)

    def write_struct_data(self, struct_data, resource, encrypt):
        """ Saves struct-packed data to the given resource.

        Not used by every block. To use it, the "struct_data" property
        should be populated, and this method must be specifically called,
        either from a containing block, or from the "save_to_resource" method."""
        s_size = struct_data['size']
        s_format = struct_data['format']
        s_attributes = struct_data['attributes']

        data = struct.pack(s_format, *[getattr(self, a) for a in s_attributes])
        if encrypt:
            data = util.crypt(data, self.crypt_value)
        assert len(data) == s_size
        resource.write(data)

    def read_struct_data(self, struct_data, resource, decrypt):
        """ Reads data from the given resource.

        Not used by every block. To use it, the "xml_structure" property
        should be populated, and this method must be specifically called,
        either from a containing block, or from the "load_from_resource" method."""
        s_size = struct_data['size']
        s_format = struct_data['format']
        s_attributes = struct_data['attributes']

        data = resource.read(s_size)
        if decrypt:
            data = util.crypt(data, self.crypt_value)
        values = struct.unpack(s_format, data)
        del data

        for a, v in zip(s_attributes, values):
            setattr(self, a, v)

