#!/usr/bin/env python
"""
Scummbler v2

    Use, distribution, and modification of the Scummbler binaries, source code,
    or documentation, is subject to the terms of the MIT license, as below.

    Copyright (c) 2011 Laurence Dougal Myers

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

Laurence Dougal Myers
www.jestarjokin.net

December 2008 - July 2009

TODO: proper clamping of bytes & words, signed & unsigned
TODO: merge "if" and "loop" blocks into generic program-flow block objects
"""

from pyparsing import ParseFatalException, ParseResults, Suppress, Literal, Group, Optional, Empty
import scummbler_vars
import string

# SCUMM limitations
#  these are set for each game, so these should be moved
#  to an external file.
#  (are these even correct?)
maxlocals = 0x10
maxglobals = 0x31F
maxbits = 0xFF

# Enums etc
RP_WORD = True
RP_BYTE = False

# Used to determine if elements should be present in Legacy/New descumm scripts
ELEMENT_OMITTED = 0
ELEMENT_OPTIONAL = 1
ELEMENT_REQUIRED = 2

def escape_string_legacy(in_str):
    """# descumm uses the karat char ("^") to escape characters.
    # Unfortunately, SCUMM scripts use the "^" char to represent three ellipses...
    #  and descumm does not escape it!
    # So, I've tried to work around it with this parse action.
    # NOTE: this means strings will NOT WORK if they have an escape character followed
    #  by a digit! We can make it work for 3-digit escape codes, but any less and
    #  we don't know where the escape code ends and the digit in the text begins.
    #  Actually, descumm only outputs escape codes if (i <= 31 && i >= 128), so
    #  we could check if:
    #  code is > 1000 (one too many digits)
    #  code is > 31 and < 128 (not output by descumm, so assume it's invalid)
    """
    esc = False
    esc_val = ""
    out_string = ""
    for c in in_str:
        if esc: # we're currently escaping
            if c in string.digits: # digit following ^
                esc_val += c
                continue
            else: # not a digit following ^, either stop escaping or print "^"
                esc = False
                if esc_val == "": # no digits following "^", assume it's the karat char
                    out_string += "^"
                elif int(esc_val) > 255 or int(esc_val) < 0: #or \
                    #(int(esc_val) > 31 and int(esc_val) < 128): # check if escape code is valid
                    raise ScummblerException("Invalid escape character code: ^" + esc_val)
                else: # add escape code to output string
                    out_string += chr(int(esc_val))
        
        if c == "^": # start escaping
            esc = True
            esc_val = ""
        else: # not escaping at all, just add the char
            out_string += c
    return out_string
                
def escape_string(in_str):
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

def gen_label(blockType, lineNum, branchNum=0):
    """ blockType = string, "i" for if, "w" for while, "d" for do/while, "f" for for.
    lineNum = int, the line number of the start of the block (used as a unique ID)
    branchNum = int, current branch (only relevant for if blocks)"""
    return "$" + blockType + str(lineNum) + "b" + str(branchNum)

def resolve_parameter(arg, op, pbits, is_word):
    """ Returns either string bytes of arg, and the opcode modified with parameter bits"""
    global parambits
    # this is a crap hack for known variables
    if 'vartype' in arg or 'knownvar' in arg:
        arg = resolve_var(arg)
        op = op | pbits
    else:
        if is_word:
            arg = to_word_LE(arg.value)
        else:
            arg = to_byte(arg.value)
        
    return arg, op

def resolve_var(tok_in, indirect=False):
    if 'knownvar' in tok_in:
        vartype = "Var"
        varval = scummbler_vars.varNames5map[tok_in.knownvar]
    else:
        vartype = tok_in.vartype
        varval = tok_in.value
    
    # Handle indirect variables
    # Indirect vars are a bit nasty.
    if type(varval) is ParseResults:
        if not vartype is "Var":
            # I don't think this is correct, as I have a script example of
            # if (!Bit[5 + Var[1]]) {
            # but does that mean Var[1] is this original indirect thing?
            #raise ParseFatalException("Only Var variables can have indirect pointers as the index.")
            pass
        baseval = varval.base
        
        if "vartype" in varval.offset or "knownvar" in varval.offset:
            offval = resolve_var(varval.offset, True)
        else:
            offval = to_word_LE(varval.offset.value)
        
        # This is crap, I've just duplicated things
        if vartype is "Local":
            vv = (int(baseval) & 0xFF)
            vv = vv | 0x4000
        elif vartype is "Bit":
            vv = int(baseval) & 0x7FFF
            vv = vv | 0x8000
        elif vartype is "Var":
            vv = int(baseval) & 0x1FFF
        
        return to_word_LE(vv, 0x2000) + offval
    
    # NOTE: > may need to be >=, not sure if max value limits are inclusive
    # I've removed the max bounds checking for now because I'm not sure if the max vals are correct
    if vartype is "Local":
        #if int(varval) >= maxlocals:
        #    raise ParseFatalException("Local variable index is too high: " + varval + " (max: " + str(maxlocals) + ")")
        vv = (int(varval) & 0xFF)
        vv = vv | 0x4000
        if indirect:
            vv = vv | 0x2000
        return to_word_LE(vv)
    elif vartype is "Bit":
        #if int(varval) >= maxbits:
        #    raise ParseFatalException("Bit variable index is too high: " + varval + " (max: " + str(maxbits) + ")")
        if indirect:
            #raise ParseFatalException("Bit variables cannot be used in an indirect variable pointer.")
            vv = vv | 0x2000
        vv = int(varval) & 0x7FFF
        vv = vv | 0x8000
        return to_word_LE(vv)
    elif vartype is "Var":
        #if int(varval) >= maxglobals:
        #    raise ParseFatalException("Var variable index is too high: " + varval + " (max: " + str(maxglobals) + ")")
        vv = int(varval) & 0x1FFF
        if indirect:
            vv = vv | 0x2000
        return to_word_LE(vv)
    else:
        raise Exception("Unknown vartype: " + str(vartype) + ", val: " + str(varval))

def to_byte(inval, maskval=None, clamp=True):
    """ Accepts an int or a string representing the value ("123"),
    returns a 1-char string with actual value("\x7B").
    
    Optionally accepts a "mask" value which will be binary-ORed with the value.
    Also accepts a "clamp" boolean (defaults to True), which will make sure the
    input value is between -128 and 255 (doesn't know if value should be
    signed)."""
    if type(inval) is str:
        inval = int(inval)
    if clamp and inval < -128 or inval > 255:
        raise ParseFatalException("Byte value should be between -128 and 255.")
    if maskval != None:
        inval = inval | maskval
    return chr(inval & 0xFF)

def to_word_LE(inval, maskval=None, clamp=True):
    """ Accepts an int or a string representing the value ("123"),
    returns a 2-char string with actual value in BE format ("\x7B\x00").
    
    Optionally accepts a "mask" value which will be binary-ORed with the value.
    Also accepts a "clamp" boolean (defaults to True), which will make sure the
    input value is between -32,768 and 65535 (doesn't know if value should be
    signed)."""
    if type(inval) is str:
        inval = int(inval)
    if clamp and inval < -32768 or inval > 65535:
        raise ParseFatalException("Word value should be between -32768 and 65535.")
    if maskval != None:
        inval = inval | maskval
    return chr(inval & 0xFF) + \
          chr((inval & 0xFF00) >> 8)

def to_dword_LE(inval, maskval=None, clamp=True):
    """ Accepts an int or a string representing the value ("123"),
    returns a 4-char string with actual value in BE format ("\x7B\x00\x00\x00").

    Optionally accepts a "mask" value which will be binary-ORed with the value.
    Also accepts a "clamp" boolean (defaults to True), which will make sure the
    input value is between -2,147,483,648 and 4,294,967,295 (doesn't know if value
    should be signed)."""
    if type(inval) is str:
        inval = int(inval)
    if clamp and inval < -21474836488 or inval > 4294967295:
        raise ParseFatalException("DWord value should be between -2,147,483,648 and 4,294,967,295.")
    if maskval != None:
        inval = inval | maskval
    return chr(inval & 0xFF) + \
          chr((inval & 0xFF00) >> 8) + \
          chr((inval & 0xFF0000) >> 8) + \
          chr((inval & 0xFF000000) >> 8)

def SupLit(instr):
    """ Just tidies up the code a bit, alias for Suppress(Literal(instr))"""
    return Suppress(Literal(instr))

def NamedElement(element, name):
    """ Workaround deficiency in PyParsing, where setting the Results Name of an element
    returns a copy, which interferes with Parse Actions set after the use of that element
    in a compound statement.
    
    NOTE: Actually escapes from the group and returns the first item of element (to escape
    from the Parse Results object and return the actual token).
    I do this because only leString uses this wrapper, but it may cause problems with anything else.
    """
    return Group(element)(name).setParseAction(lambda s, loc, toks: toks[0][0]) # escape from group, then escape from parse results

def LegacyElement(element, legacyPresence, currentPresence):
    """Wraps around "legacy" elements, determining if they should be used in the grammar depending on whether
    legacy descumm syntax is used.
    
    NOTE: I think all legacy elements will be "optional", but you can choose its presence type anyway."""
    global global_options
    if global_options.legacy_descumm:
        if legacyPresence == ELEMENT_OMITTED:
            return Empty()
        elif legacyPresence == ELEMENT_OPTIONAL:
            return Optional(element)
        elif legacyPresence == ELEMENT_REQUIRED:
            return element
        else:
            raise ScummblerException("Unknown value for \"legacyPresence\": " + str(legacyPresence))
    else:
        if currentPresence == ELEMENT_OMITTED:
            return Empty()
        elif currentPresence == ELEMENT_OPTIONAL:
            return Optional(element)
        elif currentPresence == ELEMENT_REQUIRED:
            return element
        else:
            raise ScummblerException("Unknown value for \"currentPresence\": " + str(currentPresence))

class IfBlockInfo(object):
    def __init__(self, lineNum):
        """ Accepts the line number starting the "if" block, immediately calls self.pushBranch()"""
        self.ID = lineNum
        self.branchStack = []
        self.branchCounter = 0
        self.pushBranch(lineNum) # start of "if" block is implicitly a branch.
    
    def __iter__(self):
        return iter(self.branchStack)
    
    def __str__(self):
        return "[IfBlock ID: " + str(self.ID) + ",  branchCounter: " + str(self.branchCounter) + ", branchStack: " + str(self.branchStack) + "]"
        
    def pushBranch(self, srcLineNum):
        """ Accepts the line number containing the branch, stores the line number with a new, automatically
        generated label for the destination."""
        self.branchStack.append( (srcLineNum, gen_label('i', self.ID, self.branchCounter)) )
        self.branchCounter += 1
    
    def popElseBranch(self):
        """ Returns the second-last added branch."""
        return self.branchStack.pop(-2)
    
    def popBranch(self, i=-1):
        """ Not used, popElseBranch is more specific."""
        return self.branchStack.pop(i)

class LoopBlockInfo(object):
    def __init__(self, lineNum, incremOp=None):
        """ Accepts the line number starting the loop block, and an optional operation to perform at the end of a "for" block."""
        self.ID = lineNum
        self.startLine = lineNum #public
        self.incremOp = incremOp
        
    def __str__(self):
        return "[LoopBlock ID: " + str(self.ID) + ", endLine: " + str(self.endLine) + "]"
    
class ScummblerException(Exception):
    pass
    
class ScummblerAutogenException(ScummblerException):
    pass

# thrown whenever a parse action is being generated for a non-existing grammar.
class ScummblerAutogenSubopcodeException(ScummblerAutogenException):
    pass

class ScummblerParseException(ScummblerException):
    pass

# Global options (a bit crap)
class GlobalOptions(object):
    def __init__(self, *args, **kwds):
        if kwds is None:
            kwds = {}
        self.legacy_descumm = kwds.get('legacy_descumm', False)
       
global_options = GlobalOptions()