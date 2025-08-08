import os.path
import struct
from optparse import OptionParser

class VerbHelperException(Exception):
    pass

def read_char(ocfile):
    return struct.unpack("c", ocfile.read(1))[0]

def read_byte(ocfile):
    return struct.unpack("B", ocfile.read(1))[0]

def read_word_LE(ocfile):
    return struct.unpack("<H", ocfile.read(2))[0]
    
def read_quad_LE(ocfile):
    return struct.unpack("<I", ocfile.read(4))[0]

def parse_object_file(ocfile):
    size = read_quad_LE(ocfile)
    blockType = ocfile.read(2)
    if blockType != "OC":
        raise VerbHelperException("Unrecognised file type - expected block type OC, got " + str(blockType))
    objID = read_word_LE(ocfile)
    unknown = read_byte(ocfile)
    xPos = read_byte(ocfile)
    yPos = read_byte(ocfile)
    parentState = yPos & 0x80
    yPos &= 0x7F
    width = read_byte(ocfile)
    parent = read_byte(ocfile)
    walkX = read_word_LE(ocfile)
    walkY = read_word_LE(ocfile)
    height = read_byte(ocfile)
    actorDir = height & 0x07
    height &= 0xF8
    nameOffset = read_byte(ocfile)
    ocfile.seek(nameOffset, 0)
    objName = ""
    while True:
        c = read_char(ocfile)
        if c == "\x00":
            break
        objName += c
    print ("#object-data [id %s, unknown %s, x-pos %s, y-pos %s, parent-state %s, width %s, "
          "parent %s, walk-x %s, walk-y %s, height %s, actor-dir %s, name \"%s\"]" % 
          (objID, unknown, xPos, yPos, parentState, width, 
          parent, walkX, walkY, height, actorDir, objName))
    
def verb_helper_main():
    oparser = OptionParser(usage="%prog arg1 ",
                           version="Scummbler v2 - Verb Helper",
                           description="Supplies object metadata contained within SCUMM V3-4 OC blocks, "
                           "to be used in a Scummbler script.")
    
    options, args = oparser.parse_args()
    
    returnval = 1
    
    if len(args) == 0 or len(args) > 1:
        print "Please provide one file containing a binary SCUMM object script."
        oparser.print_help()
        return returnval
    
    fname = args[0]
        
    if not os.path.isfile(fname):
        print "Invalid file name: " + str(fname)
        return returnval
    
    try:
        ocfile = file(fname, 'rb')
        parse_object_file(ocfile)
    finally:
        ocfile.close()
    
    returnval = 0
    return returnval


if __name__ == "__main__": verb_helper_main()