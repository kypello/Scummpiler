import scummpacker_util as util
from abstractblock import AbstractBlock

class BlockLocalScript(AbstractBlock):
    name = None # override in concrete class

    def _read_data(self, resource, start, decrypt, room_start=0):
        script_id = resource.read(1)
        if decrypt:
            script_id = util.crypt(script_id, self.crypt_value)
        self.script_id = util.str2int(script_id)
        self.data = self._read_raw_data(resource, self.size - (resource.tell() - start), decrypt)

    def _write_data(self, outfile, encrypt):
        script_num = util.int2str(self.script_id, num_bytes=1)
        if encrypt:
            script_num = util.crypt(script_num, self.crypt_value)
        outfile.write(script_num)
        self._write_raw_data(outfile, self.data, encrypt)

    def generate_file_name(self):
        return self.name + "_" + str(self.script_id).zfill(3) + ".dmp"

