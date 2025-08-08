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

December 2008 - December 2010

Atomic parsing elements
"""
from pyparsing import *
import scummbler_vars

# le = lexicon entry, also gives the code a French feel

# Numbers
leUnsignedInt = Word(nums)
leInt = Word(nums + "-", nums)
leHexByte = Word(nums + srange("[a-fA-F]"), exact=2) # for descummed scripts
leHexWord = Word(nums + srange("[a-fA-F]"), exact=4) # for descummed scripts
leHexInt = Suppress(Literal("0x")) + Word(nums + srange("[a-fA-F]"), max=8) # 32-bit
leDefinedValueDef = Word(alphanums + "_") # prevents parsing definedValues on definition
#leDefinedValue = Word("$", alphanums + "_") # compiler define value (I hate using the $)
leDefinedValue = Forward() # the compiler has to fill this in
leByte = (leInt | leDefinedValue)("value")
leWord = (leInt | leDefinedValue)("value")
leDelay = leUnsignedInt
leLabel = Word(alphanums + "_")
leLocalIndex = leUnsignedInt
leBitIndex = leUnsignedInt # same for now
leGlobalIndex = leUnsignedInt # same for now
leLocalIndexOrPointer = Forward() # I'm not sure if this can be indirect
leBitIndexOrPointer = Forward() # I'm not sure if this can be indirect
leGlobalIndexOrPointer = Forward()

# Variables (these could probably be condensed)
leLocalVar = Literal("Local")("vartype") + Suppress(Literal("[")) + leLocalIndexOrPointer("value") + Suppress(Literal("]"))
leBitVar = Literal("Bit")("vartype") + Suppress(Literal("[")) + leBitIndexOrPointer("value") + Suppress(Literal("]"))
leGlobalVar = Literal("Var")("vartype") + Suppress(Literal("[")) + leGlobalIndexOrPointer("value") + Suppress(Literal("]"))
leKnownGlobalVar = Forward()

leVariable = leLocalVar | leBitVar | leGlobalVar | leKnownGlobalVar | leDefinedValue
leVarOrByte = leVariable | leByte
leVarOrWord = leVariable | leWord
leListItem = Group(leVariable | leWord) # group is a hack to work around nested vars etc

leIndexPointer = Group(leUnsignedInt("base") + Literal("+") + Group(leVarOrWord)("offset"))

# Numbers (Forwarded/Recursive)
leLocalIndexOrPointer << (leIndexPointer | leLocalIndex) # removed because only globals can be indirect
leBitIndexOrPointer << (leIndexPointer | leBitIndex) # removed because only globals can be indirect
leGlobalIndexOrPointer << (leIndexPointer | leGlobalIndex)

leArgList = Suppress(Literal("[")) + Optional(delimitedList(leListItem))("list") + Suppress(Literal("]"))

# Other
# These string functions probably shouldn't be in the lexicon... baaaahh!
leStringFuncNewline = Literal("newline")("function") + Suppress(Literal("(")) + Suppress(Literal(")"))
leStringFuncKeepText = Literal("keepText")("function") + Suppress(Literal("(")) + Suppress(Literal(")"))
leStringFuncWait = Literal("wait")("function") + Suppress(Literal("(")) + Suppress(Literal(")"))
leStringFuncGetInt = Literal("getInt")("function") + Suppress(Literal("(")) + Group(leVariable)("arg1") + Suppress(Literal(")"))
leStringFuncGetVerb = Literal("getVerb")("function") + Suppress(Literal("(")) + Group(leVariable)("arg1") + Suppress(Literal(")"))
leStringFuncGetName = Literal("getName")("function") + Suppress(Literal("(")) + Group(leVariable)("arg1") + Suppress(Literal(")"))
leStringFuncGetString = Literal("getString")("function") + Suppress(Literal("(")) + Group(leVariable)("arg1") + Suppress(Literal(")"))
leStringFuncStartAnim = Literal("startAnim")("function") + Suppress(Literal("(")) + leWord("arg1") + Suppress(Literal(")"))
leStringFuncSound = (
    Literal("sound")("function") + Suppress(Literal("(")) +
        (leHexInt | leInt)("arg1") + Suppress(Literal(",")) +
        (leHexInt | leInt)("arg2") +
    Suppress(Literal(")"))
)
leStringFuncSetColor = Literal("setColor")("function") + Suppress(Literal("(")) + leWord("arg1") + Suppress(Literal(")"))
leStringFuncSetFont = Literal("setFont")("function") + Suppress(Literal("(")) + leWord("arg1") + Suppress(Literal(")"))
# TODO: support "unknown" functions
leStringFunc = (leStringFuncNewline | leStringFuncKeepText | leStringFuncWait |
                leStringFuncGetInt | leStringFuncGetVerb | leStringFuncGetName | leStringFuncGetString |
                leStringFuncStartAnim | leStringFuncSound | leStringFuncSetColor | leStringFuncSetFont)
leStringText = quotedString

leStringParticle = leStringText | leStringFunc
leString = leStringParticle + Optional(OneOrMore(Suppress(Literal("+")) + leStringParticle))


leComment = cStyleComment # luckily, descumm uses C-style comments!
