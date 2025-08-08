import os
import scummpacker_util as util
from blocks.v5_base import BlockSoundV5

class BlockSBLV5(BlockSoundV5):
    name = "SBL"
    AU_HEADER = "AUhd\x00\x00\x00\x03\x00\x00\x80AUdt"

    def _read_data(self, resource, start, decrypt, room_start=0):
        # SBL blocks have AUhd and AUdt headers instead of
        #  "Creative Voice File".
        # Skip AUhd/AUdt and just read the rest of the raw data,
        #  we can regenerate the header later.
        resource.seek(19, os.SEEK_CUR)
        super(BlockSBLV5, self)._read_data(resource, start, decrypt)

    def load_from_file(self, path):
        self.name = os.path.splitext(os.path.split(path)[1])[0]
        self.size = os.path.getsize(path) - 0x1A + 27 # ignore VOC header, add SBL block header (could just +1)
        voc_file = file(path, 'rb')
        voc_file.seek(0x1A, os.SEEK_CUR)
        self.data = self._read_raw_data(voc_file, self.size - 27, False)
        voc_file.close()

    def save_to_file(self, path):
        outfile = file(os.path.join(path, self.generate_file_name()), 'wb')
        self._write_voc_header(outfile, False)
        self._write_data(outfile, False)
        outfile.close()

    def save_to_resource(self, resource, room_start=0):
        self._write_header(resource, True)
        self._write_auhd_header(resource, True)
        self._write_data(resource, True)

    def _write_auhd_header(self, outfile, encrypt):
        voc_size = self.size - 27 # ignore all header info for size
        au_header = BlockSBLV5.AU_HEADER + util.int2str(voc_size, 4, util.BE, None)
        au_header = (util.crypt(au_header, self.crypt_value if encrypt else None))
        outfile.write(au_header)

    def _write_voc_header(self, outfile, encrypt):
        """
        SBL block strips the "Creative Voice File" header information, so we
        have to restore it. Thankfully there's not much there except for the
        start of the data and the version of the VOC format.
        00h     14h     Contains the string "Creative Voice File" plus an EOF byte.
        14h     2       The file offset to the sample data. This value usually is
                        001Ah.
        16h     2       Version number. The major version is in the high byte, the
                        minor version in the low byte.
        18h     2       Validity check. This word contains the complement (NOT
                        operation) value of offset 16h added to 1234h.
        1Ah     ...     Start of the sample data.
        """
        header_name = "Creative Voice File\x1A"
        data_offset = 0x1A
        voc_version = 0x010A
        voc_version_complement = (0x1234 + ~voc_version) & 0xFFFF
        header = (header_name
                  + util.int2str(data_offset, num_bytes=2)
                  + util.int2str(voc_version, num_bytes=2)
                  + util.int2str(voc_version_complement, num_bytes=2))
        header = (util.crypt(header, self.crypt_value) if encrypt else header)
        outfile.write(header)

    def generate_file_name(self):
        return self.name.rstrip() + ".voc"
