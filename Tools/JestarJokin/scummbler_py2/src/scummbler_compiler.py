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

December 2008 - July 2011
"""
import scummbler_grammar
from pyparsing import oneOf, col, line, lineno, lastParseLoc
from scummbler_lexicon import leDefinedValue
from scummbler_misc import *
from scummbler_misc import resolve_parameter
import scummbler_opcodes



class CompilerBase(object):  
    # Not sure about these limits, but you can't jump more than a word.
    maxJump = 0x7FFF
    minJump = -0x7FFF
    
    scriptTypes = ["SCRP", "LSCR", "VERB", "ENCD", "EXCD"] # different for each SCUMM version
    scriptTypeMap = {
            "global" : 0,
            "local" : 1,
            "object" : 2,
            "verb" : 2,
            "entry" : 3,
            "exit" : 4, 
            }
    
    def __init__(self, grammar=None):
        # Some globals for resolving jumps
        # Jumps will be resolved like so:
        #  - When we find a jump, note the destination label and the current line number
        #     (there may be multiple jumps to the same label, so store a list of jumps
        #       for each label)
        #  - When we find a label, note the label name and the current line number
        #  - After parsing, we resolve each jump, first checking each destination label.
        #  - If the label does not exist in self.labelTable, we didn't see it in parsing
        #     (error in the script).
        #  - For each jump of that label, we get the line number containing the label,
        #     and resolve the difference in bytes between the lines.
        self.jumpTable = {} # key = label, item = line num containing jumping instruction
        self.labelTable = {} # key = label, item = line num containing the label
        self.ifStack = [] # used for resolving nested if statements
        self.loopStack = [] # used for resolving loops (TODO: replace self.ifStack)
        self.currIfBlock = None
        
        self.currScriptType = None
        self.lineNum = 0
        
        self.definedValues = {} # syntactic sugar
        self.anomalies = {} # Parse actions that aren't named 'do_grNameOfGrammar' or are shared... not actually used      
        self.eventTable = {} # Stores entry points for VERB/OC blocks
        self.objectData = {} # Stores object metadata for V3-4 OC blocks
        self.scriptNum = None # For local scripts
        
        self.rootExpression = None # This is determined during mapParseActions
        
        self.opFunctionTable = {}
        self._create_function_table()
        self._override_opcodes()
        
        if grammar != None:
            self.mapParseActions(grammar)

    def compileFile(self, filename):
        if self.rootExpression == None:
            raise ScummblerException("Compiler has not mapped any parse actions.")
        results = self.rootExpression.parseFile(filename)
        self.resolveJumps(results)
        return ''.join(results)
        
    def compileString(self, instring):
        if self.rootExpression == None:
            raise ScummblerException("Compiler has not mapped any parse actions.")
        results = self.rootExpression.parseString(instring)
        self.resolveJumps(results)    
        return results
            
    def mapParseActions(self, grammar):
        self.grammar = grammar
        for gname, gram in grammar:
            try:
                if gname in self.anomalies:
                    pact = getattr(self, self.anomalies[gname])
                else:
                    pact = getattr(self, 'do_' + gname)
                gram.setParseAction(pact)
            except AttributeError, ae:
                #print ae
                continue
        self.rootExpression = getattr(grammar, grammar.rootExpression)

    def enableTesting(self): # crap
        self.rootExpression = getattr(self.grammar, self.grammar.testExpression)
        
    def disableTesting(self): # crap
        self.rootExpression = getattr(self.grammar, self.grammar.rootExpression)
        
    def resolveJumps(self, results):
        """ Accepts a ParseResults object or other list of strings, modifies each string in place to store
        jump offsets. Also, calls resolveEventMap if this is an object/verb script."""
        # For each label being jumped to, resolve each jump to that label.
        # (labels without jumps to them are ignored)
        # l = the line number containing the label
        # j = the line number containing the jump
        for label, jlist in self.jumpTable.items():
            if not self.labelTable.has_key(label):
                raise ScummblerException("Label does not exist: " + str(label) + "  (affected meaningful lines: " + str(jlist) + ")")
            
            l = self.labelTable[label] # line number of the label
            
            for j in jlist:    
                if l <= j:
                    offset = -sum( [ len(results[i]) for i in xrange(l, j + 1) ] )
                else:
                    # Also handles jump to next line (offset of 0)
                    # I'm not going to optimize 0-offset jumps.
                    offset = sum( [ len(results[i]) for i in xrange(j + 1, l) ] )
                    
                if offset < self.minJump or offset > self.maxJump:
                    raise ScummblerException("Jump is too large: " + str(offset) + " (meaningful line: " + str(j) + ")")
                
                results[j] = results[j][:-2] + to_word_LE(offset)
                
        if self.currScriptType == self.scriptTypeMap["verb"]:
            self.resolveEventMap(results)

    def resolveEventMap(self, results):
        """ For each entry in the event table, converts the label (value) into the position in the code.
        Does not include the size of the header (which will be added in generateHeader)."""
        if len(self.eventTable) == 0:
            raise ScummblerParseException("An object/verb script must have an event table.")
        for k, v in self.eventTable.items():
            if not v in self.labelTable:
                raise ScummblerParseException("Verb action \"" + str(k) + "\" cannot be mapped; label \"" + str(v) + "\" not found.")
            offset = self.labelTable[v]
            if offset == 0:
                self.eventTable[k] = 0
            else:
                self.eventTable[k] = sum( [ len(results[i]) for i in xrange(0, offset) ] )
                
    def generateHeader(self, size):
        """ Once you have compiled the script, pass the length of the output to this function.
        
        This function should be overridden."""
        raise NotImplementedError("generateHeader needs to be overriden in " + str(self.__class__))

    def getScriptType(self):
        """ Returns the engine-specific block name for the script type"""
        return self.scriptTypes[self.currScriptType]
    
    def setScriptType(self, scrptype):
        """ If the script type has already been set and doesn't match the new value, raises an error."""
        if self.currScriptType != None and self.currScriptType != scrptype:
            raise ScummblerParseException("Conflicting script type info: old type = " + self.scriptTypes[self.currScriptType] + 
                                                                       ", new type = " + self.scriptTypes[scrptype])
        self.currScriptType = scrptype
    
    # These are compiler directives, and independent of engine version.
    def do_grPragmaScriptNum(self, s, loc, toks):
        self.setScriptType(self.scriptTypeMap["local"]) # for now we just assume if this script is numbered, it's local
        if int(toks.scriptnum) < 200: # will throw exception if scriptnum can't be cast to int.
            raise ScummblerParseException("Local script number must be greater than 200.")
        self.scriptNum = to_byte(toks.scriptnum)
        return []
    
    def do_grPragmaScriptType(self, s, loc, toks):
        self.setScriptType(self.scriptTypeMap[toks.stype])
        return []
    
    def do_grPragmaEventTable(self, s, loc, toks):
        """ Parse mapping of verb events to labels."""
        self.setScriptType(self.scriptTypeMap["verb"])
        for e in toks.entries:
            self.eventTable[int(e.key, 16)] = e.value
        return []
    
    def do_grPragmaDefine(self, s, loc, toks):
        global leDefinedValue
        self.definedValues[toks[0]] = toks[1]
        # TODO: only redefine this when we've gotten all of the defined values.
        # (would probably require two-pass parsing, 1st-pass looking at compiler directives)
        leDefinedValue << oneOf(" ".join( (dv for dv in self.definedValues.keys()) )) # rewrite our grammar at runtime
        return []

    def do_grPragmaOldObjectData(self, s, loc, toks):
        """ V3-4 object blocks also store object metadata. This metadata can be defined at the start of a script.
        
        This parse action just stores the raw strings; conversion to bytes etc will have to be done in
        generateHeader."""
        self.setScriptType(self.scriptTypeMap["verb"])
        for i in toks.objdata:
            if i.key in self.objectData:
                raise ScummblerParseException("Duplicate object data definition for " + str(i.key) + "; " +
                                              str(self.objectData[i.key]) + " vs. " + str(i.val))
            self.objectData[i.key] = i.val
        # Check that all items are included by cheating a bit; we know we can't have any duplicates, so
        #  we can't have more than 12 items. As "unknown" is unnecessary, we only need a minimum of 11 items.
        #  So, if we have 11 items and one of them is "unknown", we must be missing one of the mandatory items!
        #  (If we have 12 items we're fine)
        if len(self.objectData) < 11 or (len(self.objectData) == 11 and "unknown" in self.objectData):
            raise ScummblerParseException("Insufficient arguments in #object-data directive. All items except \"unknown\" are mandatory.")
        return []
    
    # These are lexicon particles and common to all engine versions.
    def do_leStringText(self, s, loc, toks):
        global global_options
        the_string = toks[0][1:-1] # trim surrounding quote marks
        if global_options.legacy_descumm:
            return escape_string_legacy(the_string)
        else:
            return escape_string(the_string)

    # This method is not required as the other string parsing methods handle it.
    def do_leString(self, s, loc, toks):
        return ''.join(toks)

    def do_leStringFuncNewline(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        return to_byte(op) + to_byte(subop)

    def do_leStringFuncKeepText(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        return to_byte(op) + to_byte(subop)

    def do_leStringFuncWait(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        return to_byte(op) + to_byte(subop)

    def do_leStringFuncGetInt(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        arg1 = resolve_var(toks.arg1)
        return to_byte(op) + to_byte(subop) + arg1

    def do_leStringFuncGetVerb(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        arg1 = resolve_var(toks.arg1)
        return to_byte(op) + to_byte(subop) + arg1

    def do_leStringFuncGetName(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        arg1 = resolve_var(toks.arg1)
        return to_byte(op) + to_byte(subop) + arg1

    def do_leStringFuncGetString(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        arg1 = resolve_var(toks.arg1)
        return to_byte(op) + to_byte(subop) + arg1

    def do_leStringFuncStartAnim(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        arg1 = to_word_LE(toks.arg1)
        return to_byte(op) + to_byte(subop) + arg1

    def do_leStringFuncSound(self, s, loc, toks):
        """
        "sound()" is a bit tricky, since it uses two 32-bit values,
        split across two calls to the function each! e.g.
        sound(0x12345678, 0x9ABCDEF0)
        will look like
        0xFF 0x0A 0x78 0x56
        0xFF 0x0A 0x34 0x12
        0xFF 0x0A 0xF0 0xDE
        0xFF 0x0A 0xBC 0x9A
        """
        op = to_byte(scummbler_opcodes.opStringFunctionStart)
        subop = to_byte(scummbler_opcodes.opStringFunctions[toks.function])

        arg1 = toks.arg1
        if arg1.startswith('0x'):
            arg1 = int(arg1, 16)
        else:
            arg1 = int(arg1)
        sound_offset = op + subop + \
            chr(arg1 & 0xFF) + \
            chr((arg1 & 0xFF00) >> 8) + \
            op + subop + \
            chr((arg1 & 0xFF0000) >> 8) + \
            chr((arg1 & 0xFF000000) >> 8)

        arg2 = toks.arg2
        if arg2.startswith('0x'):
            arg2 = int(arg2, 16)
        else:
            arg2 = int(arg2)
        vctl_size = op + subop + \
            chr(arg2 & 0xFF) + \
            chr((arg2 & 0xFF00) >> 8) + \
            op + subop + \
            chr((arg2 & 0xFF0000) >> 8) + \
            chr((arg2 & 0xFF000000) >> 8)

        return sound_offset + vctl_size

    def do_leStringFuncSetColor(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        arg1 = to_word_LE(toks.arg1)
        return to_byte(op) + to_byte(subop) + arg1

    def do_leStringFuncSetFont(self, s, loc, toks):
        op = scummbler_opcodes.opStringFunctionStart
        subop = scummbler_opcodes.opStringFunctions[toks.function]
        arg1 = to_word_LE(toks.arg1)
        return to_byte(op) + to_byte(subop) + arg1

    def do_leDefinedValue(self, s, loc, toks):
        name = toks[0]
        if not name in self.definedValues:
            raise ScummblerParseException("Unknown variable name: " + name)
        return self.definedValues[name]
        
    def _override_opcodes(self):
        pass

    def _create_function_table(self):
        pass
   
class CompilerV345Common(CompilerBase):
    scriptTypes = ["SC", "LS", "OC", "EN", "EX"] # V3-4
    
    def _create_function_table(self):
        self.opFunctionTable.update(scummbler_opcodes.opFunctionTable)
    
    def generateHeader(self, size):
        """ V3-4 share same header."""
        # Default to global script if no script-type identifying constructs parsed within the script.
        if self.currScriptType is None: 
            self.setScriptType(self.scriptTypeMap["global"])
        
        blockType = self.getScriptType()
        
        objdata = ''
        if self.currScriptType == self.scriptTypeMap["verb"]:
            if len(self.objectData) == 0:
                raise ScummblerParseException("Object/Verb scripts for SCUMM V3 or V4 requires the #object-data information.")
            # Object metadata
            objdata += to_word_LE(self.objectData["id"])
            if "unknown" in self.objectData:
                objdata += to_byte(self.objectData["unknown"])
            else:
                objdata += "\x00"
            objdata += to_byte(self.objectData["x-pos"])
            # High bit of y-pos stores the parent state
            objdata += to_byte((int(self.objectData["y-pos"]) & 0x7F) |
                               (int(self.objectData["parent-state"]) << 7))
            objdata += to_byte(self.objectData["width"])
            objdata += to_byte(self.objectData["parent"])
            objdata += to_word_LE(self.objectData["walk-x"])
            objdata += to_word_LE(self.objectData["walk-y"])
            # Height stores actor-dir in the lower three bits
            # (minimum height is 8... or 0?)
            # TODO: validate these values
            objdata += to_byte((int(self.objectData["height"]) & 0xF8) |
                               (int(self.objectData["actor-dir"]) & 0x07))
            
            objname = self.objectData["name"]
            # name offset/end of event table.
            # 4 = size, 2 = block name, 12 = object data, 1 = this offset,
            # variable * 3 = event table, 1 = end of table
            nameOffset = 19 + (len(self.eventTable) * 3) + 1
            objdata += to_byte(nameOffset) # offset of end of event table
            
            codeOffset = nameOffset + len(objname) + 1 # name is null-terminated
            # Event mapping
            events = self.eventTable.keys()
            events.sort() # Make sure events are recorded in ascending order
            for k in events:
                v = self.eventTable[k]
                pos = v + codeOffset # event mapping offsets are absolute
                objdata += to_byte(k) # action
                objdata += to_word_LE(pos) # offset
            
            objdata += "\x00" # end of table
            objdata += objname + "\x00" # the object's name
            size += codeOffset
        elif self.currScriptType == self.scriptTypeMap["local"]:
            objdata += self.scriptNum # assumes it's already a string for writing
            size += 4 + len(blockType) + 1 # four bytes for size, two bytes for block name, one byte for the script number
        else:
            size += 4 + len(blockType) # size is quad, block name is 2 chars
            
        # Add length of the file to the header (Little Endian)
        header = (chr((size & 0xFF)) +
                  chr((size & 0xFF00) >> 8) +
                  chr((size & 0xFF0000) >> 16) +
                  chr((size & 0xFF000000) >> 24))
        header += blockType
        header += objdata
        return header
    
    # ~~~~~~~~~~~~ Mostly Auto-Generated Functions ~~~~~~~~~~~~~
    
    def do_grFunc_actorFollowCamera(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_actorFromPos(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    # --- Start sub-opcodes ---
    def do_grFunc_ActorOps_Unknown(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Costume(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_WalkSpeed(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Sound(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_WalkAnimNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_TalkAnimNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_StandAnimNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Nothing(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_BYTE)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Init(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Elevation(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_DefaultAnims(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Palette(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_TalkColor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Name(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1 = toks.arg1 + "\x00"
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_InitAnimNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Width(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Scale(self, s, loc, toks):
        """ V3-4 only. V5 should override this."""
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        #arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3

    def do_grFunc_ActorOps_IgnoreBoxes(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    # --- End sub-opcodes ---
    
    def do_grFunc_ActorOps(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        if "arg2" in toks:
            arg2 = ''.join(toks.arg2)
        arg3 = "\xFF"
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_setClass(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        for a in toks.arg2:
            aux = 0x01
            a, aux = resolve_parameter(a, aux, 0x80, RP_WORD)
            arg2 += to_byte(aux) + a
        arg2 += "\xFF"
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_animateCostume(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_breakHere(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_chainScript(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        for a in toks.arg2:
            aux = 0x01
            a, aux = resolve_parameter(a, aux, 0x80, RP_WORD)
            arg2 += to_byte(aux) + a
        arg2 += "\xFF"
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    # --- Start sub-opcodes ---
    def do_grFunc_cursorCommand_CursorShow(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_CursorHide(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_UserputOn(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_UserputOff(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_CursorSoftOn(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_CursorSoftOff(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_UserputSoftOn(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_UserputSoftOff(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_SetCursorImg(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_setCursorHotspot(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_BYTE)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_InitCursor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_InitCharset(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_CursorCommandLoadCharset(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        for a in toks.arg1:
            aux = 0x01
            a, aux = resolve_parameter(a, aux, 0x80, RP_WORD)
            arg1 += to_byte(aux) + a
        arg1 += "\xFF"
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_cursorCommand_SO(self, s, loc, toks):
        return to_byte(self.opFunctionTable['cursorCommand']) + ''.join(toks)
    # --- End sub-opcodes ---

    
    def do_grFunc_cutscene(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        for a in toks.arg1:
            aux = 0x01
            a, aux = resolve_parameter(a, aux, 0x80, RP_WORD)
            arg1 += to_byte(aux) + a
        arg1 += "\xFF"
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_debug(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_delayVariable(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1 = resolve_var(toks.arg1)
        #op = op | 0x80 # don't do this, since it's implied that it's a variable
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_dummyA7(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_endCutscene(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_faceActor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_findInventory(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_findObject(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_freezeScripts(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorCostume(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorElevation(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorFacing(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorMoving(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorRoom(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorScale(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorWalkBox(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorWidth(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorX(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getActorY(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getAnimCounter(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getClosestObjActor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getDist(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getInventoryCount(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getObjectOwner(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getObjectState(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getRandomNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getStringWidth(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_getVerbEntryPoint(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_isScriptRunning(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_isSoundRunning(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_lights(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2 = to_byte(toks.arg2.value)
        arg3 = to_byte(toks.arg3.value)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_loadRoom(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    # --- Start sub-opcodes ---
    def do_grFunc_matrixOp_setBoxFlags(self, s, loc, toks):
        """ V4-5"""
        arg1 = arg2 = ""
        op = self.opFunctionTable[toks.function]
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        return to_byte(op) + arg1 + arg2
    
    def do_grFunc_matrixOp_setBoxScale(self, s, loc, toks):
        """ V4-5"""
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_matrixOp_SetBoxSlot(self, s, loc, toks):
        """ V4-5"""
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_matrixOp_createBoxMatrix(self, s, loc, toks):
        """ V4-5"""
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_matrixOp_SO(self, s, loc, toks):
        """ V4-5"""
        return to_byte(self.opFunctionTable['matrixOp']) + ''.join(toks)
    # --- End sub-opcodes ---
    
    
    def do_grFunc_panCameraTo(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    # --- Start sub-opcodes ---
    def do_grFunc_print_Pos(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['PO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_print_Color(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['PO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_print_Clipped(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['PO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_print_RestoreBG(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['PO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_print_Center(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['PO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_print_LeftHeight(self, s, loc, toks):
        """ V4-5: Left"""
        op = self.opFunctionTable['PO_' + toks.function]
        return to_byte(op)
    
    def do_grFunc_print_Overhead(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['PO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_print_PlayCDTrack(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['PO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_print_Text(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['PO_' + toks.function]
        # No target
        arg1 = toks.arg1 + "\x00"
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    # --- End sub-opcodes ---
    
    
    def do_grFunc_putActor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_WORD)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_putActorAtObject(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_putActorInRoom(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    # --- Start sub-opcodes ---
    def do_grFunc_Resource_ResourceloadScript(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceloadSound(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceloadCostume(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceloadRoom(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcenukeScript(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcenukeSound(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcenukeCostume(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcenukeRoom(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcelockScript(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcelockSound(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcelockCostume(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcelockRoom(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceunlockScript(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceunlockSound(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceunlockCostume(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceunlockRoom(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceclearHeap(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceloadCharset(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourcenukeCharset(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_ResourceloadFlObject(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_Resource_SO(self, s, loc, toks):
        return to_byte(self.opFunctionTable['Resource']) + ''.join(toks)
    
    # --- End sub-opcodes ---
    
    def do_grFunc_saveLoadGame(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_setCameraAt(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_setObjectName(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2 = toks.arg2 + "\x00"
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_setOwnerOf(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_setState(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_soundKludge(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        for a in toks.arg1:
            aux = 0x01
            a, aux = resolve_parameter(a, aux, 0x80, RP_WORD)
            arg1 += to_byte(aux) + a
        arg1 += "\xFF"
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_startMusic(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_startObject(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        for a in toks.arg3:
            aux = 0x01
            a, aux = resolve_parameter(a, aux, 0x80, RP_WORD)
            arg3 += to_byte(aux) + a
        arg3 += "\xFF"
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_startSound(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    # --- Start sub-opcodes ---
    def do_grFunc_stringOps_PutCodeInString(self, s, loc, toks):
        """Has support for descumm's odd output when there's an empty string."""
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2 = toks.arg2 + "\x00"
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_stringOps_CopyString(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_stringOps_SetStringChar(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_BYTE)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_stringOps_GetStringChar(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_stringOps_CreateString(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_stringOps_SO(self, s, loc, toks):
        return to_byte(self.opFunctionTable['stringOps']) + ''.join(toks)
    # --- End sub-opcodes ---
    
    
    def do_grFunc_stopMusic(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_stopObjectScript(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_stopScript(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_stopSound(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    # --- Start sub-opcodes (these are modified to prepend 'VO_') ---
    def do_grFunc_VerbOps_Image(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_Text(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1 = toks.arg1 + "\x00"
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_Color(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_HiColor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_SetXY(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_On(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_Off(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_Delete(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_New(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_DimColor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_Dim(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_Key(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_Center(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_SetToString(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_SetToObject(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_VerbOps_BackColor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['VO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    # --- End sub-opcodes ---
    
    def do_grFunc_VerbOps(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        if "arg2" in toks:
            arg2 = ''.join(toks.arg2)
        arg3 = "\xFF"
        return to_byte(op) + target + arg1 + arg2 + arg3

    # --- Start sub-opcodes ---
    def do_grFunc_wait_WaitForActor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_wait_WaitForMessage(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_wait_WaitForCamera(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_wait_WaitForSentence(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_wait_SO(self, s, loc, toks):
        return to_byte(self.opFunctionTable['wait']) + ''.join(toks)
    # --- End sub-opcodes ---

    def do_grFunc_walkActorTo(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_WORD)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_walkActorToActor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        arg3 = to_byte(toks.arg3.value)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    
    def do_grFunc_walkActorToObject(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3

    # ~~~~~~~~~~~~ End Mostly Auto-Generated Functions ~~~~~~~~~~~~~
    
    # ~~~~~~~~~~~~ Start hand-carved parse actions ~~~~~~~~~~~~~~~~
    def do_grInlineOperation(self, s, loc, toks):
        op = scummbler_opcodes.opInlineOperation[toks.operation]
        val, op = resolve_parameter(toks.value, op, 0x80, RP_WORD)
        targ = resolve_var(toks.target)
        
        return to_byte(op) + targ + val
    
    def do_grIncDec(self, s, loc, toks):
        op = scummbler_opcodes.opInlineOperation[toks.operation]
        targ = resolve_var(toks.target)
        
        return to_byte(op) + targ
    
    def do_grExpressionMode(self, s, loc, toks):
        op = scummbler_opcodes.opExpressionOpcode
        targ = resolve_var(toks.target)
        # Workaround for expressions that only call an opcode or only store a value
        #  (must be some overly eager compiler optimization in the original SCUMM)
        
        if 'expop' in toks.subexp:
            subexp = to_byte(scummbler_opcodes.opExpressionSubOpcode) + toks.subexp[0]
        elif not 'vartype' in toks.subexp and not 'knownvar' in toks.subexp:
            if not 'value' in toks.arg1:
                subexp = toks.subexp[0]
            else:
                subexp = to_byte(scummbler_opcodes.opExpressionValue) + to_word_LE(toks.subexp.value)
        else:
            subexp = to_byte(scummbler_opcodes.opExpressionValue | 0x80) + resolve_var(toks.arg1)
    
        return to_byte(op) + targ + subexp + to_byte(scummbler_opcodes.opExpressionEnd)
    
    def do_grSubExpression(self, s, loc, toks):
        argop1 = scummbler_opcodes.opExpressionValue # these come from scummbler_opcodes
        argop2 = scummbler_opcodes.opExpressionValue
        stackop = scummbler_opcodes.opExpressionOperation[toks.operation]
    
        omitfirst = False
        omitsecond = False
        
        # These are some really crappy workarounds here, I probably need to revise my grammar
        if 'expop' in toks.arg1: # sub-instruction
            val1 = toks.arg1[0]
            argop1 = scummbler_opcodes.opExpressionSubOpcode
        elif not 'vartype' in toks.arg1 and not 'knownvar' in toks.arg1: # assume it's a constant or subexpression
            if not 'value' in toks.arg1: # subexpression
                val1 = toks.arg1[0]
                # Need to omit first argop as subexpr already has it
                omitfirst = True
            else: # constant
                val1 = to_word_LE(toks.arg1.value)
        else:
            val1 = resolve_var(toks.arg1)
            argop1 = argop1 | 0x80 # inline operations only take one parameter
        
        if 'expop' in toks.arg2: # sub-instruction
            val2 = toks.arg2[0]
            argop2 = scummbler_opcodes.opExpressionSubOpcode
        elif not 'vartype' in toks.arg2 and not 'knownvar' in toks.arg2: # assume it's a constant or subexpression
            if not 'value' in toks.arg2: # subexpression
                val2 = toks.arg2[0]
                # Need to omit first argop as subexpr already has it
                omitsecond = True
            else: # constant
                val2 = to_word_LE(toks.arg2.value)
        else:
            val2 = resolve_var(toks.arg2)
            argop2 = argop2 | 0x80 # inline operations only take one parameter
            
        return ("" if omitfirst else to_byte(argop1)) + val1 + \
                ("" if omitsecond else to_byte(argop2)) + val2 + \
                to_byte(stackop)
    
    def do_grConstruct(self, s, loc, toks):
        # This stores the line numbers for meaningful constructs. Avoids problems
        #  with blank lines, comments, etc. Does not affect tokens at all.
        self.lineNum += 1
    
    def do_grJumpGoto(self, s, loc, toks):
        if not self.jumpTable.has_key(toks.target):
            self.jumpTable[toks.target] = []
        self.jumpTable[toks.target].append(self.lineNum)
        return to_byte(scummbler_opcodes.opJump) + "\x00\x00" # placeholder, will modify this in Phase 2
    
    def do_grJumpLabel(self, s, loc, toks):
        # Labels are only used by the compiler; returns nothing.
        if self.labelTable.has_key(toks.label):
            if self.labelTable[toks.label] == self.lineNum:
                # If we're parsing a label we've already tried parsing (could occur with back-tracking),
                #  just ignore the label
                return []
            if loc + len(toks.label) + 2 != lastParseLoc():
                # Hacky workaround for backtracking. Seems like Scummbler is backtracking back to the 
                #  last line with a valid label whenever it encounter a line with a syntax error.
                print loc, lastParseLoc()
                raise ScummblerParseException("Syntax error on line " + str(lineno(lastParseLoc(), s)) + ": \n\n" + 
                                                line(lastParseLoc(), s) + "\n" +
                                                " " * (col(lastParseLoc(), s) - 1) + "^")
            raise ScummblerParseException("Duplicate label declaration on line " + str(lineno(loc, s)) + ": " + toks.label)
        self.labelTable[toks.label] = self.lineNum
        return []
    
    def do_grIfZeroEquality(self, s, loc, toks):
        if not '!' in toks:
            op = scummbler_opcodes.opComparisonsNoParameters["notEqualZero"]
        else:
            op = scummbler_opcodes.opComparisonsNoParameters["equalZero"]
    
        if not 'vartype' in toks and not 'knownvar' in toks: # should never happen
            raise ScummblerParseException("The parameter in a \"equalZero\" or \"notEqualZero\" test must be a variable: " + line(loc, s))
        else:
            val1 = resolve_var(toks)
        
        return to_byte(op) + val1
    
    def do_grIfComparison(self, s, loc, toks):
        op = scummbler_opcodes.opComparisons[toks.comparator]
        
        val1 = resolve_var(toks.arg1)
        
        # Because arg1 is always a variable, parameter bits tell what arg2 is
        val2, op = resolve_parameter(toks.arg2, op, 0x80, RP_WORD)
        
        return to_byte(op) + val1 + val2
    
    def do_grIfClassOfIs(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        testobject, op = resolve_parameter(toks.testobject, op, 0x80, RP_WORD)
        classes = ""
        for c in toks.classes:
            aux = 0x01
            c, aux = resolve_parameter(c, aux, 0x80, RP_WORD)
            classes += to_byte(aux) + c
        classes += "\xFF"
        return to_byte(op) + testobject + classes
    
    def do_grIfActorInBox(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        actor, op = resolve_parameter(toks.actor, op, 0x80, RP_BYTE)
        box, op = resolve_parameter(toks.box, op, 0x40, RP_BYTE)
        return to_byte + actor + box
    
    def do_grIfState(self, s, loc, toks):
        if toks.comparator == "==":
            op = self.opFunctionTable["ifState"]
        else: # toks.comparator == "!="
            op = self.opFunctionTable["ifNotState"]
        testobject, op = resolve_parameter(toks.testobject, op, 0x80, RP_WORD)
        state, op = resolve_parameter(toks.state, op, 0x40, RP_BYTE)
        return to_byte(op) + testobject + state
    
    def do_grJumpUnless(self, s, loc, toks):
        """ Similar to do_grIfLineStart, but without keeping track of "if" blocks etc.
        Also similar to do_grJumpGoto, but we use the already parsed operator etc."""
        if not self.jumpTable.has_key(toks.target):
            self.jumpTable[toks.target] = []
        self.jumpTable[toks.target].append(self.lineNum)
        return toks[0] + "\x00\x00"
        
    def do_grIfLineStart(self, s, loc, toks):
        """ Seperate parsing of "if" statements & lines; "if" could be either a new "if" block
          or part of an "else if" statement. This method allows us to create a stack for
          nested if blocks."""
    
        # Push current "if" block data onto the stack so we can come back to it if
        #  necessary. This means the first entry will always be a dummy value of our
        #  initial settings.
        self.ifStack.append( self.currIfBlock )
        self.currIfBlock = IfBlockInfo(self.lineNum)
        
        self.lineNum += 1
        return toks[0] + "\x00\x00" # most parsing was already done in grIfStart, we just add the jump
        
    def do_grIfElse(self, s, loc, toks):       
        # Push this onto the branch stack to be resolved when we find the "if" end.
        # This is a goto at the end of the block we just finished parsing.
        self.currIfBlock.pushBranch(self.lineNum)
        
        self.lineNum += 1
        return to_byte(scummbler_opcodes.opJump) + "\x00\x00"
        
    def do_grIfLineElse(self, s, loc, toks):
        """Similar to do_grIfLineStart, but without manipulating the self.ifStack."""
        
        # self.lineNum has already been adjusted to be after the goto inserted by the "else".
        # (pop -2 because we just added a goto and pushed its details)
        lastLine, lastLabel = self.currIfBlock.popElseBranch()
    
        self.jumpTable[lastLabel] = [lastLine]
        self.labelTable[lastLabel] = self.lineNum
    
        if toks.elseif != "":
            self.currIfBlock.pushBranch(self.lineNum)
            self.lineNum += 1
            toks[1] = toks[1] + "\x00\x00" # add placeholder for jump
        
        return toks
        
    def do_grIfEnd(self, s, loc, toks):
        # Map all remaining branch jumps to this end position.
        for lastLine, lastLabel in self.currIfBlock:
            self.jumpTable[lastLabel] = [lastLine]
            self.labelTable[lastLabel] = self.lineNum
        
        self.currIfBlock = self.ifStack.pop()
        
        # Note that the original SCUMM compiler emits dummy jumps at the end
        #  of every "else if" block. Scummbler does not, as it works on a
        #  lower level, handles "if" blocks differently, and relies on
        #  output from descumm, which outputs dummy jumps as comments.
        
        return []
    
    def do_grWhileStart(self, s, loc, toks):
        self.loopStack.append(LoopBlockInfo(self.lineNum))
        self.lineNum += 1
        return toks[0] + "\x00\x00"
    
    def do_grWhileEnd(self, s, loc, toks):
        loopinfo = self.loopStack.pop()
        loopStart = loopinfo.startLine
        
        # Generate loop back to start
        label = gen_label('w', loopStart, 0) # 0 marks the beginning of loops
        self.labelTable[label] = loopStart
        if not self.jumpTable.has_key(label):
            self.jumpTable[label] = []
        self.jumpTable[label].append(self.lineNum)
        
        # Generate jump from start to end of block
        label = gen_label('w', loopStart, 1) # 1 marks the end of loops
        self.labelTable[label] = self.lineNum
        if not self.jumpTable.has_key(label):
            self.jumpTable[label] = []
        self.jumpTable[label].append(loopStart)
        
        self.lineNum += 1
        
        return to_byte(scummbler_opcodes.opJump) + "\x00\x00"    
    
    def do_grDoWhileStart(self, s, loc, toks):
        # Just mark the beginning of the loop
        self.loopStack.append(LoopBlockInfo(self.lineNum))
        
        return []
    
    def do_grDoWhileEnd(self, s, loc, toks):
        # Generate loop back to start
        loopStart = self.loopStack.pop().startLine
        label = gen_label('d', loopStart, 0) # 0 marks the beginning of loops
        self.labelTable[label] = loopStart
        if not self.jumpTable.has_key(label):
            self.jumpTable[label] = []
        self.jumpTable[label].append(self.lineNum)
        
        self.lineNum += 1
        return toks[0] + "\x00\x00"
    
    def do_grForLoopStart(self, s, loc, toks):
        output = []
        
        if 'init' in toks:
            output.append(toks.init[0])    
            self.lineNum += 1
        
        output.append(toks.test[0] + '\x00\x00')
    
        increm = None
        if 'increm' in toks:
            increm = toks.increm
            
        self.loopStack.append(LoopBlockInfo(self.lineNum, increm))
            
        self.lineNum += 1
        
        return output
    
    def do_grForLoopEnd(self, s, loc, toks):
        # Similar to do_grWhileEnd, but adds the increment instruction
        output = []
        
        loopinfo = self.loopStack.pop()
        loopStart = loopinfo.startLine
        
        # Add "increment" instruction if present
        if loopinfo.incremOp != None:
            output.append(loopinfo.incremOp)
            self.lineNum += 1
        
        # Generate loop back to start
        label = gen_label('f', loopStart, 0) # 0 marks the beginning of loops
        self.labelTable[label] = loopStart
        if not self.jumpTable.has_key(label):
            self.jumpTable[label] = []
        self.jumpTable[label].append(self.lineNum)
        
        self.lineNum += 1
        
        # Generate jump from start to end of block
        label = gen_label('f', loopStart, 1) # 1 marks the end of loops
        self.labelTable[label] = self.lineNum
        if not self.jumpTable.has_key(label):
            self.jumpTable[label] = []
        self.jumpTable[label].append(loopStart)
    
        output.append(to_byte(scummbler_opcodes.opJump) + "\x00\x00")
        
        return output
        
    
    # --- Function parse actions ---
    def do_grFunc_delay(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        val = int(toks.arg1[0])
        return to_byte(op) + chr(val & 0xFF) + chr((val & 0xFF00) >> 8) + chr((val & 0xFF0000) >> 16) 
    
    def do_grFunc_doSentence(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        if (toks.arg1 == "STOP"):
            return to_byte(op) + to_byte(0xFE)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_WORD)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_drawBox(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        
        left, op = resolve_parameter(toks.left, op, 0x80, RP_WORD)
        top, op = resolve_parameter(toks.top, op, 0x40, RP_WORD)
        
        auxop = 0x05 # not sure if this auxop is meant to be 0x05, but it's not 0x01!
        
        right, auxop = resolve_parameter(toks.right, auxop, 0x80, RP_WORD)
        bottom, auxop = resolve_parameter(toks.bottom, auxop, 0x40, RP_WORD)
        colour, auxop = resolve_parameter(toks.colour, auxop, 0x20, RP_BYTE)
        
        return to_byte(op) + left + top + to_byte(auxop) + right + bottom + colour
    
    def do_grFunc_drawObject(self, s, loc, toks):
        """V3-4: drawObject takes three word params"""
        arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_WORD)
        return to_byte(op) + arg1 + arg2 + arg3
    
    def do_grFunc_loadRoomWithEgo(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        objecttok, op = resolve_parameter(toks.object, op, 0x80, RP_WORD)
        room, op = resolve_parameter(toks.room, op, 0x40, RP_BYTE)
        x = to_word_LE(toks.x)
        y = to_word_LE(toks.y)
        return to_byte(op) + objecttok + room + x + y
    
    def do_grFunc_oldRoomEffect(self, s, loc, toks):
        op = self.opFunctionTable["oldRoomEffect"]
        subop = self.opFunctionTable[toks.function]
        effect, op = resolve_parameter(toks.effect, op, 0x80, RP_WORD)
        return to_byte(op) + to_byte(subop) + effect
    
    def do_grFunc_override(self, s, loc, toks):
        return to_byte(self.opFunctionTable['override']) + to_byte(self.opFunctionTable[toks.function])
    
    def do_grFunc_pickupObject(self, s, loc, toks):
        """ V3-4: pickupObject takes one argument."""
        arg1 = ""
        op = self.opFunctionTable[toks.function] # TODO: handle opcodes better
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        return to_byte(op) + arg1
    
    def do_grFunc_print(self, s, loc, toks):
        arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        if not 'arg2' in toks: # workaround for no sub-opcodes
            arg2 = ''
            arg3 = '\xFF'
        else:
            arg2 = ''.join(toks.arg2)
            # print will end with 0x00 if it displays text (sub-op 0x0F),
            # otherwise it terminates with 0xFF.
            if toks.arg2[-1][0] != "\x0F":
                arg3 = "\xFF"
        return to_byte(op) + arg1 + arg2 + arg3
    
    def do_grFunc_printEgo(self, s, loc, toks):
        arg1 = arg2 = ""
        op = self.opFunctionTable[toks.function]
        if not 'arg1' in toks: # workaround for no sub-opcodes
            arg1 = ''
            arg2 = '\xFF'
        else:
            arg1 = ''.join(toks.arg1)
            # print will end with 0x00 if it displays text (sub-op 0x0F),
            # otherwise it terminates with 0xFF.
            if toks.arg1[-1][0] != "\x0F":
                arg2 = "\xFF"
        return to_byte(op) + arg1 + arg2
    
    def do_grFunc_PseudoRoom(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        val = to_byte(toks.val)
        resvals = ""
        for r in toks.reslist:
            if r == "IG":
                r = "0"
            resvals += to_byte(r, 0x80)
        resvals += "\x00"
        return to_byte(op) + val + resvals
    
    def do_grFunc_saveLoadVars_VarRange(self, s, loc, toks):
        op = self.opFunctionTable["SLV_" + toks.function]
        val1 = resolve_var(toks.arg1)
        val2 = resolve_var(toks.arg2)
        return to_byte(op) + val1 + val2
    
    def do_grFunc_saveLoadVars_StringRange(self, s, loc, toks):
        op = self.opFunctionTable["SLV_" + toks.function]
        val1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        val2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        return to_byte(op) + val1 + val2
    
    def do_grFunc_saveLoadVars_Open(self, s, loc, toks):
        op = self.opFunctionTable["SLV_" + toks.function]
        val1 = toks.arg1 + "\x00"
        return to_byte(op) + val1
    
    def do_grFunc_saveLoadVars_Append(self, s, loc, toks):
        op = self.opFunctionTable["SLV_" + toks.function]
        return to_byte(op)
    
    def do_grFunc_saveLoadVars_Close(self, s, loc, toks):
        op = self.opFunctionTable["SLV_" + toks.function]
        return to_byte(op)
    
    def do_grFunc_saveLoadVars(self, s, loc, toks):
        """V3-4: can take a few sub-ops. Sub-op list ends with either the Append
        or Close sub-ops, or \x00. All sub-ops are optional."""
        subops = lastop = ''
        op = self.opFunctionTable[toks.function]
        operation = self.opFunctionTable["SLV_" + toks.operation]
        if "subops" in toks:
            subops = ''.join(toks.subops)
        if "lastop" in toks:
            lastop = ''.join(toks.lastop)
        else:
            lastop = "\x00"
        return to_byte(op) + to_byte(operation) + subops + lastop
    
    def do_grFunc_saveRestoreVerbs(self, s, loc, toks):
        op = self.opFunctionTable["saveRestoreVerbs"]
        subop = self.opFunctionTable[toks.function]

        start, subop = resolve_parameter(toks.start, subop, 0x80, RP_BYTE)
        end, subop = resolve_parameter(toks.end, subop, 0x40, RP_BYTE)
        mode, subop = resolve_parameter(toks.mode, subop, 0x20, RP_BYTE)
        
        return to_byte(op) + to_byte(subop) + start + end + mode
    
    def do_grFunc_setVarRange(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        startvar = resolve_var(toks.startvar)
        if "numitems" in toks:
            numitems = int(toks.numitems)
        else:
            numitems = None
        vals = []
        use_words = False
        # If highest (or lowest negative) value can't fit in a byte,
        #  we'll use words!
        # We could potentially check for negatives, set a boolean if found,
        #  and then check between -128 and 127.
        for v in toks.listvals:
            v = int(v)
            if v < -128 or v > 255:
                use_words = True
                op = op | 0x80
            vals.append(v)
            
        if numitems is None:
            numitems = len(vals)
        elif numitems != len(vals):
            raise ScummblerParseException("setVarRange: the given number of values does not match the actual number of values.")
            
        if use_words:
            vals = ''.join(to_word_LE(v) for v in vals)
        else:
            vals = ''.join(to_byte(v) for v in vals)
        
        return to_byte(op) + startvar + to_byte(numitems) + vals
    
    def do_grFunc_startScript(self, s, loc, toks):
        arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        for a in toks.arg2:
            aux = 0x01
            a, aux = resolve_parameter(a, aux, 0x80, RP_WORD)
            arg2 += to_byte(aux) + a
        arg2 += "\xFF"
        
        # Explicit flag decleration (can be overriden by existing input opcde)
        if "recursive" in toks:
            op |= 0x40
        if "freezeres" in toks:
            op |= 0x20
        
        self.lineNum += 1
        return to_byte(op) + arg1 + arg2 + arg3
    
    def do_grStartScriptLine(self, s, loc, toks):
        # NOTE: this could screw up explicit flag declaration
        if "descummop" in toks:
            flags = int("0x" + toks[0], 16) & 0x60
            #toks[1][0] = to_byte(ord(toks[1][0]) | flags)
            return to_byte(ord(toks[1][0]) | flags) + toks[1][1:]
        return toks
    
    def do_grFunc_stopObjectCode(self, s, loc, toks):
        if (self.currScriptType == self.scriptTypeMap["verb"] or 
            self.currScriptType == self.scriptTypeMap["entry"] or
            self.currScriptType == self.scriptTypeMap["exit"]):
            op = self.opFunctionTable[toks.function + "-alt"]
        else:
            op = self.opFunctionTable[toks.function]
        return to_byte(op)
    
    def do_grFunc_systemOps(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        subop = toks.subop
        if toks.subop == "1" or toks.subop == "RESTART":
            subop = 0x01
        elif toks.subop == "2" or toks.subop == "PAUSE":
            subop = 0x02
        elif toks.subop == "3" or toks.subop == "QUIT":
            subop = 0x03
        else: # will never happen
            raise ScummblerParseException("What the blooming heck have you done, my lad? " + str(toks.function) + " is not systemOps-ish!")
        
        return to_byte(op) + to_byte(subop)
    
    # ~~~~~~~~~~~~ End hand-carved parse actions ~~~~~~~~~~~~~~~~
    
    
class CompilerV3(CompilerV345Common):
    def _override_opcodes(self):
        self.opFunctionTable.update(scummbler_opcodes.opFunctionTableV3)
    
    def do_grFunc_cursorCommand_CursorCommandLoadCharset(self, s, loc, toks):
        """V3: cursorCommand sub-opcode acts as LoadCharset, takes two byte params."""
        arg1 = arg2 = ""
        op = self.opFunctionTable[toks.function]
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        return to_byte(op) + arg1 + arg2
    
    def do_grFunc_matrixOp_setBoxFlags(self, s, loc, toks):
        """ V3: no matrixOps, only setBoxFlags"""
        arg1 = arg2 = ""
        op = self.opFunctionTable[toks.function]
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2 = to_byte(toks.arg2)
        return to_byte(op) + arg1 + arg2
    
    def do_grFunc_print_LeftHeight(self, s, loc, toks):
        """ V3: Height, one word param."""
        op = self.opFunctionTable['PO_' + toks.function]
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        return to_byte(op) + arg1
    
    def do_grFunc_roomOps_SO(self, s, loc, toks):
        """ V3: args come before sub-opcode.
        
        All roomOps sub-opcodes remain uncompiled until they reach this parse action."""
        op = self.opFunctionTable["roomOps"]
        func = toks.function
        if func == "ShakeOn" or func == "ShakeOff":
            # These take no arguments so we insert dummy values.
            arg1 = "\x00\x00"
            arg2 = "\x00\x00"
        else:
            arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
            arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        subop = self.opFunctionTable[func]
        return to_byte(op) + arg1 + arg2 + to_byte(subop)
    
    def do_grFunc_wait_WaitForSentence(self, s, loc, toks):
        """V3: wait for sentence has its own sub-opcode.
        
        Question: is there also the WaitForSentence sub-opcode for wait?"""
        op = self.opFunctionTable[toks.function]
        return ["standalone", to_byte(op)] # another hack
    
    def do_grFunc_wait_SO(self, s, loc, toks):
        if toks[0] == "standalone": # hack
            return toks[1]
        return to_byte(self.opFunctionTable['wait']) + ''.join(toks)

    
class CompilerV3Old(CompilerV3):
    def _override_opcodes(self):
        self.opFunctionTable.update(scummbler_opcodes.opFunctionTableV3Old)
    
    def do_grFunc_getActorScale(self, s, loc, toks):
        raise ScummblerParseException("getActorScale not supported in Scumm V3Old (Indy3)")        
    
    def do_grFunc_getActorX(self, s, loc, toks):
        target = arg1 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        return to_byte(op) + target + arg1
    
    def do_grFunc_getActorY(self, s, loc, toks):
        target = arg1 = ""
        op = self.opFunctionTable[toks.function]
        target = resolve_var(toks.target)
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        return to_byte(op) + target + arg1
    
    def do_grFunc_wait_WaitForActor(self, s, loc, toks):
        arg1 = ""
        op = self.opFunctionTable[toks.function]
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        return ["standalone", to_byte(op) + arg1]
    
    def do_grFunc_wait_WaitForCamera(self, s, loc, toks):
        raise ScummblerParseException("WaitForCamera not supported in Scumm V3Old (Indy3)")    
    
    def do_grFunc_wait_WaitForMessage(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        return ["standalone", to_byte(op)]
    

class CompilerV4(CompilerV345Common):
    def _override_opcodes(self):
        #self.opFunctionTable.update(scummbler_opcodes.opFunctionTableV4)
        pass
    
    def do_grFunc_roomOps_SO(self, s, loc, toks):
        """ V4: only up to sub-opcde 0x06.
        
        All roomOps sub-opcodes remain uncompiled until they reach this parse action."""
        op = self.opFunctionTable["roomOps"]
        func = toks.function
        if func == "ShakeOn" or func == "ShakeOff":
            # These take no arguments so we insert dummy values.
            arg1 = ''
            arg2 = ''
        else:
            arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
            arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        subop = self.opFunctionTable[func]
        return to_byte(op) + to_byte(subop) + arg1 + arg2
    
class CompilerV5(CompilerV345Common):
    scriptTypes = ["SCRP", "LSCR", "VERB", "ENCD", "EXCD"]
    
    def _override_opcodes(self):
        self.opFunctionTable.update(scummbler_opcodes.opFunctionTableV5)
    
    def generateHeader(self, size):
        if self.currScriptType is None:
            self.setScriptType(self.scriptTypeMap["global"])
        
        blockType = self.getScriptType()
        
        objdata = ''
        if self.currScriptType == self.scriptTypeMap["verb"]:
            # name offset/end of event table.
            # 4 = size, 4 = block name,
            # variable * 3 = event table, 1 = end of table
            codeOffset = 8 + (len(self.eventTable) * 3) + 1 # offset of end of event table
            # Event mapping
            events = self.eventTable.keys()
            events.sort() # Make sure events are recorded in ascending order
            for k in events:
                v = self.eventTable[k]
                pos = v + codeOffset # event mapping offsets are absolute
                objdata += to_byte(k) # action
                objdata += to_word_LE(pos) # offset
            
            objdata += "\x00" # end of table
            size += codeOffset
        elif self.currScriptType == self.scriptTypeMap["local"]:
            objdata += self.scriptNum
            size += 4 + len(blockType) + 1 # four bytes for size, four bytes for block name, one byte for the script number
        else:
            size += 4 + len(blockType) # size is quad, block name is 2 chars

        # Add length of the file to the header (Little Endian)
        header = blockType
        header += (chr((size & 0xFF000000) >> 24) + 
                   chr((size & 0xFF0000) >> 16) +
                   chr((size & 0xFF00) >> 8) +
                   chr((size & 0xFF)))
        header += objdata
        return header
    
    def do_grPragmaOldObjectData(self, s, loc, toks):
        raise ScummblerParseException("Object data is not necessary in V5 scripts.")
    # --- Start sub-opcodes ---
    def do_grFunc_ActorOps_Unknown(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Costume(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_WalkSpeed(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Sound(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_WalkAnimNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_TalkAnimNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_StandAnimNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Nothing(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_BYTE)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Init(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Elevation(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_DefaultAnims(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Palette(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_TalkColor(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Name(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1 = toks.arg1 + "\x00"
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_InitAnimNr(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Width(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_Scale(self, s, loc, toks):
        """V5: ActorOps.Scale() takes two byte params."""
        arg1 = arg2 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        return to_byte(op) + arg1 + arg2
    
    def do_grFunc_ActorOps_NeverZClip(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_SetZClip(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_IgnoreBoxes(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_FollowBoxes(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_AnimSpeed(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_ActorOps_ShadowMode(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable['AO_' + toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    # --- End sub-opcodes ---
    
    def do_grFunc_pickupObject(self, s, loc, toks):
        """V5: pickupObject takes two arguments, different opcode."""
        arg1 = arg2 = ""
        op = self.opFunctionTable[toks.function] # TODO: handle opcodes better
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        return to_byte(op) + arg1 + arg2
    
    def do_grFunc_drawObject_setXY(self, s, loc, toks):
        """V5: drawObject has sub-opcodes (this is one of them)"""
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_drawObject_setImage(self, s, loc, toks):
        """V5: drawObject has sub-opcodes (this is one of them)"""
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_drawObject(self, s, loc, toks):
        """V5: drawObject has sub-opcodes, different opcode"""
        arg1 = arg2 = ""
        op = self.opFunctionTable[toks.function]
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        if not 'arg2' in toks:
            arg2 = to_byte(self.opFunctionTable[toks.function + "()"]) # compensate for "empty" sub-opcode
        else:
            arg2 = ''.join(toks.arg2) # setImage or setXY which is already compiled
        return to_byte(op) + arg1 + arg2
    
    # Auto-generated roomOps sub-opcodes
    def do_grFunc_roomOps_RoomScroll(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_roomOps_SetScreen(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_WORD)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_roomOps_ShakeOn(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_roomOps_ShakeOff(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        # No arg1
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_roomOps_RoomIntensity(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        arg3, op = resolve_parameter(toks.arg3, op, 0x20, RP_BYTE)
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_roomOps_saveLoad(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_roomOps_screenEffect(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_WORD)
        # No arg2
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    def do_grFunc_roomOps_colorCycleDelay(self, s, loc, toks):
        target = arg1 = arg2 = arg3 = ""
        op = self.opFunctionTable[toks.function]
        # No target
        arg1, op = resolve_parameter(toks.arg1, op, 0x80, RP_BYTE)
        arg2, op = resolve_parameter(toks.arg2, op, 0x40, RP_BYTE)
        # No arg3
        return to_byte(op) + target + arg1 + arg2 + arg3
    
    # Manual roomOps sub-opcodes
    def do_grFunc_roomOps_SetPalColor(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        red, op = resolve_parameter(toks.red, op, 0x80, RP_WORD)
        green, op = resolve_parameter(toks.green, op, 0x40, RP_WORD)
        blue, op = resolve_parameter(toks.blue, op, 0x20, RP_WORD)
        auxop = 0x04 # based on what I've seen
        index, auxop = resolve_parameter(toks.index, auxop, 0x80, RP_BYTE)
        return to_byte(op) + red + green + blue + to_byte(auxop) + index
    
    def do_grFunc_roomOps_SetRoomScale(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        scale1, op = resolve_parameter(toks.scale1, op, 0x80, RP_BYTE)
        y1, op = resolve_parameter(toks.y1, op, 0x40, RP_BYTE)
        auxop1 = 0x01
        scale2, auxop1 = resolve_parameter(toks.scale2, auxop1, 0x80, RP_BYTE)
        y2, auxop1 = resolve_parameter(toks.y2, auxop1, 0x40, RP_BYTE)
        auxop2 = 0x01
        slot, auxop2 = resolve_parameter(toks.slot, auxop2, 0x80, RP_BYTE)
        return to_byte(op) + scale1 + y1 + to_byte(auxop1) + scale2 + y2 + to_byte(auxop2) + slot
    
    def do_grFunc_roomOps_setRGBRoomIntensity(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        redscale, op = resolve_parameter(toks.redscale, op, 0x80, RP_WORD)
        greenscale, op = resolve_parameter(toks.greenscale, op, 0x40, RP_WORD)
        bluescale, op = resolve_parameter(toks.bluescale, op, 0x20, RP_WORD)
        auxop = 0x0B # based on what I've seen
        start, auxop = resolve_parameter(toks.start, auxop, 0x80, RP_BYTE)
        end, auxop = resolve_parameter(toks.end, auxop, 0x40, RP_BYTE)
        return to_byte(op) + redscale + greenscale + bluescale + to_byte(auxop) + start + end
    
    def do_grFunc_roomOps_saveLoadString(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        slot, op = resolve_parameter(toks.slot, op, 0x80, RP_BYTE)
        stringy = toks.stringy + "\x00"
        return to_byte(op) + slot + stringy
    
    def do_grFunc_roomOps_palManipulate(self, s, loc, toks):
        op = self.opFunctionTable[toks.function]
        slot, op = resolve_parameter(toks.slot, op, 0x80, RP_BYTE)
        auxop1 = 0x01
        start, auxop1 = resolve_parameter(toks.start, auxop1, 0x80, RP_BYTE)
        end, auxop1 = resolve_parameter(toks.end, auxop1, 0x40, RP_BYTE)
        auxop2 = 0x01
        time, auxop2 = resolve_parameter(toks.time, auxop2, 0x80, RP_BYTE)
        return to_byte(op) + slot + to_byte(auxop1) + start + end + to_byte(auxop2) + time
    
    def do_grFunc_roomOps_SO(self, s, loc, toks):
        return to_byte(self.opFunctionTable["roomOps"]) + ''.join(toks) # bit dodgy


class CompilerFactory(object):
    # SCUMM engine versions
    compilers = { "3old" : CompilerV3Old,
                  "3": CompilerV3,
                  "4": CompilerV4,
                  "5": CompilerV5 }
    
    def __new__(cls, scummver, *args, **kwds):
        assert type(scummver) == str
        if not scummver in CompilerFactory.compilers:
            raise ScummblerException("Unsupported SCUMM version: " + str(scummver))
        return CompilerFactory.compilers[scummver](scummbler_grammar.GrammarFactory(scummver), *args, **kwds)

def __unit_test():
    global global_options
    print "Start scummbler_compiler unit test."
    
    teststr = """
    [0000] (48) if (Local[1] == 1) {
[0007] (14)   print(255,[Text(" ")]);
[000C] (60)   freezeScripts(127)
[000E] (33)   saveLoad?(1,26))
[0012] (80)   breakHere()
[0013] (48)   if (VAR_GAME_LOADED == 203) {
[001A] (1A)     VAR_MAINMENU_KEY = 319;
[001F] (1A)     Var[107] = 1;
[0024] (60)     freezeScripts(0)
[0026] (62)     stopScript(0)
[0028] (18)   } else {
[002B] (1A)     VAR_MAINMENU_KEY = 0;
[0030] (1A)     Var[107] = 0;
[0035] (F2)     loadRoom(Local[0])
[0038] (**)   }
[0038] (18) } else {
[003B] (2C)   CursorHide()
[003D] (33)   saveLoad?(2,26))
[0041] (80)   breakHere()
[0042] (**) }
[0042] (A0) stopObjectCode()
    """
    global_options.legacy_descumm = True
    comp = CompilerFactory("5")
    print comp.compileString(teststr)
    
    # Test V3-4 verb/object scripts
    teststr = """
    #object-data [id 10, unknown 11, x-pos 12, y-pos 13, width 14, height 15, parent 16, parent-state 1, walk-x 17,
                  walk-y 18, actor-dir 19, name "test object"]
    Events:
      8 - 0024
    [0024] VAR_RESULT= getActorX(Local[0])
    Exprmode Local[3] = (<VAR_RESULT = getActorX(Local[0])> - Local[1]);
Exprmode Local[3] = ((<VAR_RESULT = getActorX(Local[0])> - Local[1]) / 30);
    stopObjectCode();
    """
    global_options.legacy_descumm = True
    comp = CompilerFactory("4")
    print comp.compileString(teststr)
    
    # Test defining variable names
    teststr = """
    #define MEGApretzel Var[108]
    MEGApretzel = 12
    """
    global_options.legacy_descumm = True
    comp = CompilerFactory("5")
    print comp.compileString(teststr)
    
    # Test escape codes in non-legacy descumm scripts
    teststr = """
    print(255,[Text("Hello my friend!")]);
    print(255,[Text("I am \\xFF\\x037 years old.")]);
    print(255,[Text("So she said, \\"I haven't a clue!\\" \\\\ \\m\\e\\o\\w")]);
    """
    global_options.legacy_descumm = False
    comp = CompilerFactory("5")
    print comp.compileString(teststr)
    
    # Test other differences in legacy descumm scripts
    teststr = """
    drawObject(21);
    stopObjectCode();
    startScript(202,[],F);
[000E] (91)   animateCostume(VAR_EGO,11);
[0012] (80)   breakHere();
[0013] (80)   breakHere();
[0014] (80)   breakHere();
[0015] (80)   breakHere();
[0016] (80)   breakHere();
[0017] (80)   breakHere();
[0018] (B6)   walkActorToObject(VAR_EGO,119);
[001D] (AE)   WaitForActor(VAR_EGO);
[0021] (91)   animateCostume(VAR_EGO,245);
[0025] (AE)   WaitForActor(VAR_EGO);
[0029] (28)   if (!Bit[136]) {
[002E] (1A)     Bit[136] = 1;
[0033] (D8)     printEgo([Text("I'll just put it here.")]);
[004C] (AE)     WaitForMessage();
[004E] (**)   }
[004E] (91)   animateCostume(VAR_EGO,11);
[0052] (80)   breakHere();
[0053] (80)   breakHere();
[0054] (80)   breakHere();
[0055] (91)   animateCostume(VAR_EGO,3);
[0059] (AC)   Exprmode Local[0] = (116 + <VAR_RESULT = getRandomNr(2)>);
[0066] (85)   drawObject(Local[0]);
[006A] (5D)   setClass(116,[32]);
[00C0] (C0) endCutscene();
    """
    global_options.legacy_descumm = False
    comp = CompilerFactory("5")
    print comp.compileString(teststr)
    
    
    print "Finished scummbler_compiler unit test."
    

if __name__ == '__main__':
    __unit_test()
