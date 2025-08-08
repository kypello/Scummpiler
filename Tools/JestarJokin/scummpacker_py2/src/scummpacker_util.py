import array
import copy
import functools
import string
import xml.etree.ElementTree as et


__valid_file_chars = frozenset("-_.() %s%s" % (string.ascii_letters, string.digits)) # for filenames
__valid_text_chars = frozenset("!?@#$%s&*+\"';:,-_.() %s%s" % ("%", string.ascii_letters, string.digits)) # for XML files
    
def crypt(in_val, crypt_val):
    if crypt_val is None:
        return in_val
    if type(in_val) is str:
        out_string = ''
        for c in in_val:
            out_string += chr(ord(c) ^ crypt_val)
        return out_string
    elif type(in_val) is array.ArrayType:
        out_val = copy.deepcopy(in_val)
        for i, byte in enumerate(out_val):
            out_val[i] = byte ^ crypt_val
        return out_val
    raise ScummPackerException("Could not encrypt values of type: " + str(type(in_val)))

LE = False
BE = True
def str2int(in_val, is_BE=False, crypt_val=None):
    out_val = 0
    if crypt_val != None:
        in_val = crypt(in_val, crypt_val)
    if is_BE:
        in_val = reversed(in_val)
    for i, c in enumerate(in_val):
        out_val += ord(c) << (i * 8)
    return out_val

def int2str(in_val, num_bytes=4, is_BE=False, crypt_val=None):
    out_val = array.array('B')
    i = 0
    while i < num_bytes:
        b = (in_val >> (i * 8)) & 0xFF 
        out_val.append(b)
        i += 1
    if is_BE:
        out_val.reverse()
    if crypt_val != None:
        out_val = crypt(out_val, crypt_val)
    return out_val.tostring()

def xml2int(in_str):
    if in_str.startswith("0x"):
        return int(in_str, 16)
    else:
        return int(in_str)

def int2xml(in_val):
    return str(in_val)

def hex2xml(in_val):
    return hex(in_val).rstrip('L')

def discard_invalid_chars(in_str):
    return ''.join([c for c in in_str if c in __valid_file_chars])

def escape_invalid_chars(in_str):
    return ''.join([(c if c in __valid_text_chars else ('\\x' + hex(ord(c)).lstrip("0x").rstrip("L").zfill(2))) for c in in_str])

def unescape_invalid_chars(in_str):
    out_string = ""
    # Is there a more Pythonic way to do this?
    i = 0
    while i < len(in_str):
        c = in_str[i]
        if c == '\\':
            # Valid escape codes are:
            # "\xFF" for hex values
            # "\\" for backslashes
            # "\"" for quote marks
            # We treat any unknown escape codes as if the backslash did not exist.
            i += 1
            c = in_str[i]
            if c == 'x':
                # 'x' represents hex values, such as "\xFF"
                i += 1
                c2 = in_str[i]
                i += 1
                c3 = in_str[i]
                esc_val = int(c2 + c3, 16)
                c = chr(esc_val)
        out_string += c
        i+= 1
    return out_string

def indent_elementtree(elem, level=0):
    """ This function taken from http://effbot.org/zone/element-lib.htm#prettyprint.
    By Fredrik Lundh & Paul Du Bois."""
    i = "\n" + (level * "  ")
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent_elementtree(child, level+1)
        if not child.tail or not child.tail.strip():
            child.tail = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def ordered_sort(in_list, order):
    """ Takes a list of values and a list containing the order of those values. Wait,
    this is retarded. Don't use it."""
    # This is a bit silly; could probably just use keys from "order" instead of
    #  sorting at all.
    INFINITY = len(in_list) # append unrecognised values to end
    deco = [ ((order.index(v) if v in order else INFINITY), i, v) for i, v in enumerate(in_list) ]
    deco.sort()
    return [ v for _, _, v in deco ]

class XMLHelper(object):
    READ = 'r'
    WRITE = 'w'

    def __init__(self):
        self.read_actions = {
            'i' : functools.partial(self._read_value_from_xml_node, marshaller=xml2int), # int
            'h' : functools.partial(self._read_value_from_xml_node, marshaller=xml2int), # hex
            's' : functools.partial(self._read_value_from_xml_node, marshaller=escape_invalid_chars), # string
            'n' : self.read, # node
            'c' : self._do_callback # callback on another object, for complex actions
        }
        self.write_actions = {
            'i' : functools.partial(self._write_value_to_xml_node, marshaller=int2xml), # int
            'h' : functools.partial(self._write_value_to_xml_node, marshaller=hex2xml), # hex
            's' : functools.partial(self._write_value_to_xml_node, marshaller=unescape_invalid_chars), # string
            'n' : self.write, # node
            'c' : self._do_callback # callback on another object, for complex actions
        }

    def read(self, destination, parent_node, structure):
        for name, marshaller, attr in structure:
            node = parent_node.find(name)
            if marshaller == 'c':
                self._do_callback(destination, attr, node, XMLHelper.READ)
            else:
                self.read_actions[marshaller](destination, node, attr)

    def _read_value_from_xml_node(self, destination, node, attr, marshaller):
        value = marshaller(node.text) # doesn't support "attributes" of nodes, just values
        # Get nested attributes
        attr_split = attr.split(".")
        destination = reduce(lambda a1, a2: getattr(a1, a2), attr_split[:-1], destination)
        attr = attr_split[-1]
        setattr(destination, attr, value)

    def _write_value_to_xml_node(self, caller, node, attr, marshaller):
        # Get nested attributes
        attr = reduce(lambda a1, a2: getattr(a1, a2), attr.split("."), caller)
        node.text = marshaller(attr)

    def write(self, caller, parent_node, structure):
        for name, marshaller, attr in structure:
            node = et.SubElement(parent_node, name)
            if marshaller == 'c':
                self._do_callback(caller, attr, node, XMLHelper.WRITE)
            else:
                self.write_actions[marshaller](caller, node, attr)

    def _do_callback(self, destination, callback_name, node, mode):
        callback_func = getattr(destination, callback_name)
        callback_func(node, mode)
            
xml_helper = XMLHelper()

class ScummPackerException(Exception):
    pass

class ScummPackerUnrecognisedIndexException(ScummPackerException):
    pass

def __test():
    m = [101, 102, 103, 104, 107, 106, 105] # values
    o = [105, 104, 101, 102, 103] # sorted order
    assert ordered_sort(m, o) == [105, 104, 101, 102, 103, 107, 106]

if __name__ == '__main__': __test()