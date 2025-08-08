import os
import scummpacker_control as control
import scummpacker_util as util

class ScriptBlockContainer(object):
    local_scripts_name = None
    entry_script_name = None
    exit_script_name = None
    lf_name = None
    num_local_name = None

    def __init__(self, block_name_length, crypt_value, *args, **kwds):
        self.local_scripts = []
        self.encd_script = None
        self.excd_script = None
        self.block_name_length = block_name_length
        self.crypt_value = crypt_value
        self.name = "scripts"

    def append(self, block):
        if block.name == self.local_scripts_name:
            self.local_scripts.append(block)
        elif block.name == self.entry_script_name:
            self.encd_script = block
        elif block.name == self.exit_script_name:
            self.excd_script = block
        else:
            raise util.ScummPackerException("Unrecognised script type: " + str(block.name))

    def save_to_file(self, path):
        newpath = os.path.join(path, self.generate_file_name())
        if not os.path.isdir(newpath):
            os.mkdir(newpath) # throws an exception if can't create dir
        if self.encd_script:
            self.encd_script.save_to_file(newpath)
        if self.excd_script:
            self.excd_script.save_to_file(newpath)
        for s in self.local_scripts:
            s.save_to_file(newpath)

    def save_to_resource(self, resource, room_start=0):
        # Write entry and exit scripts (seperate from local scripts)
        if not self.encd_script or not self.excd_script:
            room_num = control.global_index_map.get_index(self.lf_name, (control.disk_spanning_counter, room_start))
            raise util.ScummPackerException(
                "Room #" + str(room_num) + " appears to be missing either a room entry or exit script (or both).")
        self.excd_script.save_to_resource(resource, room_start)
        self.encd_script.save_to_resource(resource, room_start)

        # Generate and write "number of local scripts" block
        self._write_number_of_local_scripts(resource)

        # Write all local scripts sorted by script number
        self.local_scripts.sort(cmp=lambda x,y: cmp(x.script_id, y.script_id))
        for s in self.local_scripts:
            s.save_to_resource(resource, room_start)

    def _write_number_of_local_scripts(self, resource):
        # Determine the number of local scripts
        num_local_scripts = len(self.local_scripts)
        resource.write(util.crypt(self.num_local_name, self.crypt_value)) # write the block header's name
        resource.write(util.int2str(10, 4, util.BE, self.crypt_value)) # size of this block is always 10
        resource.write(util.int2str(num_local_scripts, 2, util.LE, self.crypt_value))

    def load_from_file(self, path):
        file_list = os.listdir(path)

        for f in file_list:
            b = control.file_dispatcher.dispatch_next_block(f)
            if b != None: #and self.script_types: # TODO?: only load recognised scripts
                b.load_from_file(os.path.join(path, f))
                self.append(b)

    def generate_file_name(self):
        return "scripts"

    def __repr__(self):
        childstr = [str(self.encd_script), str(self.excd_script)]
        childstr.extend([str(c) for c in self.local_scripts])
        return "[Scripts, " + ", ".join(childstr) + "]"
