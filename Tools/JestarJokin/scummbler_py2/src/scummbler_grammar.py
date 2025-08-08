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

December 2008 - August 2010

TODO: add support for FM-Towns
      make V5-specific actorOps sub-opcodes Forward()

Differences in older engines:
V3old (indy): Very limited number of local variables?
FM-Towns: ResourceRoutines adds some sub-ops
Zak256: startMusic returns a result?

Implemented:
v3, v4: actorOps - Scale(p8)
v3: cursorCommand - LoadCharset(p8, p8) is $0E
v3, v4: drawObject(p16, p16, p16), is $25 (overrides pickupObject)
v3, v4: ifState is new, $0F (overrides getObjectState), ifNotState is new, $2F
v3old (indy3): getActorX and getActorY take p8
v3?, v4: oldRoomEffect-set and oldRoomEffect-fadein is new, $5C
v3, v4: pickupObject(p16) (old) is $50
v3: print and printEgo subop $06 is Height(p16)
v4 (LoomCD): print and printEgo adds subop $08 PlayCDTrack(p16, p16) (currently implemented for V3-5 engines)
v3: roomOps stores arguments before sub-op
v3, v4: roomOps only goes up to opcode 0x06
v3, v4: roomOps adds sub-op $02 ("RoomColor")
v3, v4: roomOps $04 SetPalColor only takes the two arguments
v3, v4: saveLoadGame is $22 (overrides getAnimCounter)
v3, v4: saveLoadVars is $A7 (overrides dummy)
v3: setBoxFlags(p8, b) is $30 (overrides matrixOps)
v3old (indy3): waitForActor is $3B (overrides getActorScale)
v3old (indy3): WaitForMessage is $AE (overrides wait with sub-ops)
v3 (small header?): WaitForSentence is $4C (overrides soundKludge),
"""
from pyparsing import *
from scummbler_lexicon import *
from scummbler_opcodes import *
from scummbler_misc import SupLit, NamedElement, ELEMENT_OMITTED, ELEMENT_OPTIONAL, ELEMENT_REQUIRED, LegacyElement, ScummblerException

class GrammarBase(object):
    # These need parse actions assigned, so we re-add them as elements of this class,
    #  to join (and be assigned like) the rest of the grammar.
    leString = leString
    leDefinedValue = leDefinedValue
    leStringFuncNewline = leStringFuncNewline
    leStringFuncKeepText = leStringFuncKeepText
    leStringFuncWait = leStringFuncWait
    leStringFuncGetInt = leStringFuncGetInt
    leStringFuncGetVerb = leStringFuncGetVerb
    leStringFuncGetName = leStringFuncGetName
    leStringFuncGetString = leStringFuncGetString
    leStringFuncStartAnim = leStringFuncStartAnim
    leStringFuncSound = leStringFuncSound
    leStringFuncSetColor = leStringFuncSetColor
    leStringFuncSetFont = leStringFuncSetFont
    leStringText = leStringText
    
    
    # This is the expression that compiler will call to parse strings.
    # It's a string so that our iterator doesn't return it as part of the grammar.
    # It needs to be overridden by any inheriting grammar.
    rootExpression = 'ParserElement()'
    testExpression = 'ParserElement()' # used for testing, similar to above
    
    def __init__(self):
        self.constructGrammar()
        self.overrideGrammar()
    
    def __iter__(self):
        """ Iterating a grammar returns a tuple containing the name of the grammar element and the actual object."""
        return ((g, getattr(self, g)) for g in dir(self) if issubclass(getattr(self, g).__class__, ParserElement))
        
    def overrideGrammar(self):
        """ This function is where you should override any grammar defined by parent grammars.
        
        e.g. V3 and V4 expect self.grFunc_ActorOps_Scale to have one argument, while V5 expects two.
        We define self.grFunc_ActorOps_Scale in GrammarV345Common as "Forward()".
        Then, for V3, we do something like this:
          self.grFunc_ActorOps_Scale << Literal("Scale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        V4 is similar, while V5 is like this: 
          self.grFunc_ActorOps_Scale << Literal("Scale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        This method allows us to construct placeholders that can be overridden, while creating 
        constructs that make use of the placeholders in the parent class (such as self.grFunc_ActorOps_SO).
        
        However, because it's still using the same object, it means we can only have the grammar
        for one SCUMM version in operation at any time (each grammar will replace the object).
        
        ?? Also, you must define all possible options in the common grammar ??
        
        Anything that is NOT shared or used in a shared construct can just be defined in the sub-class.
        
        
        NOTE: since I've changed grammars to be instanced-based instead of class based, this is silly and
        should probably be replaced by just overriding "constructGrammar" and calling super. Oh well!
        """
        pass
    
    def constructGrammar(self):
        pass
    

class GrammarV345Common(GrammarBase):
    def constructGrammar(self):
        # ~~~~~~~~~~~~ Mostly Auto-Generated Functions ~~~~~~~~~~~~~
        self.grFunc_actorFollowCamera = Literal("actorFollowCamera")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_actorFromPos = Group(leVariable)("target") + SupLit("=") + Literal("actorFromPos")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        
        # --- Start sub-opcodes ---
        self.grFunc_ActorOps_Unknown = Literal("Unknown")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_Costume = Literal("Costume")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_WalkSpeed = Literal("WalkSpeed")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_ActorOps_Sound = Literal("Sound")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_WalkAnimNr = Literal("WalkAnimNr")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_TalkAnimNr = Literal("TalkAnimNr")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_ActorOps_StandAnimNr = Literal("StandAnimNr")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_Nothing = Literal("Nothing")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(",") + Group(leVarOrByte)("arg3") + SupLit(")")
        self.grFunc_ActorOps_Init = Literal("Init")("function") + SupLit("(") + SupLit(")")
        self.grFunc_ActorOps_Elevation = Literal("Elevation")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_ActorOps_DefaultAnims = Literal("DefaultAnims")("function") + SupLit("(") + SupLit(")")
        self.grFunc_ActorOps_Palette = Literal("Palette")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_ActorOps_TalkColor = Literal("TalkColor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_Name = Literal("Name")("function") + SupLit("(") + NamedElement(leString, "arg1") + SupLit(")")
        self.grFunc_ActorOps_InitAnimNr = Literal("InitAnimNr")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_Width = Literal("Width")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        #self.grFunc_ActorOps_Scale = Literal("Scale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_ActorOps_Scale = Forward()
        #self.grFunc_ActorOps_NeverZClip = Literal("NeverZClip")("function") + SupLit("(") + SupLit(")")
        self.grFunc_ActorOps_NeverZClip = Forward()
        #self.grFunc_ActorOps_SetZClip = Literal("SetZClip")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_SetZClip = Forward()
        self.grFunc_ActorOps_IgnoreBoxes = Literal("IgnoreBoxes")("function") + SupLit("(") + SupLit(")")
        #self.grFunc_ActorOps_FollowBoxes = Literal("FollowBoxes")("function") + SupLit("(") + SupLit(")")
        self.grFunc_ActorOps_FollowBoxes = Forward()
        #self.grFunc_ActorOps_AnimSpeed = Literal("AnimSpeed")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_AnimSpeed = Forward()
        #self.grFunc_ActorOps_ShadowMode = Literal("ShadowMode")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_ShadowMode = Forward()
        self.grFunc_ActorOps_SO = self.grFunc_ActorOps_Unknown | self.grFunc_ActorOps_Costume | self.grFunc_ActorOps_WalkSpeed | self.grFunc_ActorOps_Sound | self.grFunc_ActorOps_WalkAnimNr | self.grFunc_ActorOps_TalkAnimNr | self.grFunc_ActorOps_StandAnimNr | self.grFunc_ActorOps_Nothing | self.grFunc_ActorOps_Init | self.grFunc_ActorOps_Elevation | self.grFunc_ActorOps_DefaultAnims | self.grFunc_ActorOps_Palette | self.grFunc_ActorOps_TalkColor | self.grFunc_ActorOps_Name | self.grFunc_ActorOps_InitAnimNr | self.grFunc_ActorOps_Width | self.grFunc_ActorOps_Scale | self.grFunc_ActorOps_NeverZClip | self.grFunc_ActorOps_SetZClip | self.grFunc_ActorOps_IgnoreBoxes | self.grFunc_ActorOps_FollowBoxes | self.grFunc_ActorOps_AnimSpeed | self.grFunc_ActorOps_ShadowMode
        # --- End sub-opcodes ---
        self.grFunc_ActorOps = Literal("ActorOps")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + SupLit("[") + Optional(delimitedList(self.grFunc_ActorOps_SO))("arg2") + SupLit("]")  + SupLit(")")

        self.grFunc_setClass = Literal("setClass")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + leArgList("arg2") + SupLit(")")
        self.grFunc_animateCostume = Literal("animateCostume")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_breakHere = Literal("breakHere")("function") + SupLit("(") + SupLit(")")
        self.grFunc_chainScript = Literal("chainScript")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + leArgList("arg2") + SupLit(")")
        
        # --- Start sub-opcodes ---
        self.grFunc_cursorCommand_CursorShow = Literal("CursorShow")("function") + SupLit("(") + SupLit(")")
        self.grFunc_cursorCommand_CursorHide = Literal("CursorHide")("function") + SupLit("(") + SupLit(")")
        self.grFunc_cursorCommand_UserputOn = Literal("UserputOn")("function") + SupLit("(") + SupLit(")")
        self.grFunc_cursorCommand_UserputOff = Literal("UserputOff")("function") + SupLit("(") + SupLit(")")
        self.grFunc_cursorCommand_CursorSoftOn = Literal("CursorSoftOn")("function") + SupLit("(") + SupLit(")")
        self.grFunc_cursorCommand_CursorSoftOff = Literal("CursorSoftOff")("function") + SupLit("(") + SupLit(")")
        self.grFunc_cursorCommand_UserputSoftOn = Literal("UserputSoftOn")("function") + SupLit("(") + SupLit(")")
        self.grFunc_cursorCommand_UserputSoftOff = Literal("UserputSoftOff")("function") + SupLit("(") + SupLit(")")
        self.grFunc_cursorCommand_SetCursorImg = Literal("SetCursorImg")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_cursorCommand_setCursorHotspot = Literal("setCursorHotspot")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(",") + Group(leVarOrByte)("arg3") + SupLit(")")
        self.grFunc_cursorCommand_InitCursor = Literal("InitCursor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_cursorCommand_InitCharset = Literal("InitCharset")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        # LoadCharset is V3 only, others support CursorCommand
        #self.grFunc_cursorCommand_CursorCommandLoadCharset = Literal("CursorCommand")("function") + SupLit("(") + leArgList("arg1") + SupLit(")")
        self.grFunc_cursorCommand_CursorCommandLoadCharset = Forward()
        self.grFunc_cursorCommand_SO = self.grFunc_cursorCommand_CursorShow | self.grFunc_cursorCommand_CursorHide | self.grFunc_cursorCommand_UserputOn | self.grFunc_cursorCommand_UserputOff | self.grFunc_cursorCommand_CursorSoftOn | self.grFunc_cursorCommand_CursorSoftOff | self.grFunc_cursorCommand_UserputSoftOn | self.grFunc_cursorCommand_UserputSoftOff | self.grFunc_cursorCommand_SetCursorImg | self.grFunc_cursorCommand_setCursorHotspot | self.grFunc_cursorCommand_InitCursor | self.grFunc_cursorCommand_InitCharset | self.grFunc_cursorCommand_CursorCommandLoadCharset
        # --- End sub-opcodes ---
        
        self.grFunc_cutscene = Literal("cutscene")("function") + SupLit("(") + leArgList("arg1") + SupLit(")")
        self.grFunc_debug = Literal("debug")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_delayVariable = Literal("delayVariable")("function") + SupLit("(") + Group(leVariable)("arg1") + SupLit(")")
        self.grFunc_dummyA7 = Literal("dummy(A7)")("function") + SupLit("(") + SupLit(")")
        self.grFunc_endCutscene = Literal("endCutscene")("function") + SupLit("(") + SupLit(")")
        self.grFunc_faceActor = Literal("faceActor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_findInventory = Group(leVariable)("target") + SupLit("=") + Literal("findInventory")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_findObject = Group(leVariable)("target") + SupLit("=") + Literal("findObject")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_freezeScripts = Literal("freezeScripts")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorCostume = Group(leVariable)("target") + SupLit("=") + Literal("getActorCostume")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorElevation = Group(leVariable)("target") + SupLit("=") + Literal("getActorElevation")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorFacing = Group(leVariable)("target") + SupLit("=") + Literal("getActorFacing")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorMoving = Group(leVariable)("target") + SupLit("=") + Literal("getActorMoving")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorRoom = Group(leVariable)("target") + SupLit("=") + Literal("getActorRoom")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorScale = Group(leVariable)("target") + SupLit("=") + Literal("getActorScale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorWalkBox = Group(leVariable)("target") + SupLit("=") + Literal("getActorWalkBox")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorWidth = Group(leVariable)("target") + SupLit("=") + Literal("getActorWidth")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        #self.grFunc_getActorX = Group(leVariable)("target") + SupLit("=") + Literal("getActorX")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        #self.grFunc_getActorY = Group(leVariable)("target") + SupLit("=") + Literal("getActorY")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_getActorX = Forward()
        self.grFunc_getActorY = Forward()
        #self.grFunc_getAnimCounter = Group(leVariable)("target") + SupLit("=") + Literal("getAnimCounter")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getAnimCounter = Forward()
        self.grFunc_getClosestObjActor = Group(leVariable)("target") + SupLit("=") + Literal("getClosestObjActor")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_getDist = Group(leVariable)("target") + SupLit("=") + Literal("getDist")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_getInventoryCount = Group(leVariable)("target") + SupLit("=") + Literal("getInventoryCount")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getObjectOwner = Group(leVariable)("target") + SupLit("=") + Literal("getObjectOwner")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_getObjectState = Forward() # only in V5
        self.grFunc_getRandomNr = Group(leVariable)("target") + SupLit("=") + Literal("getRandomNr")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getStringWidth = Group(leVariable)("target") + SupLit("=") + Literal("getStringWidth")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getVerbEntryPoint = Group(leVariable)("target") + SupLit("=") + Literal("getVerbEntryPoint")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_isScriptRunning = Group(leVariable)("target") + SupLit("=") + Literal("isScriptRunning")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_isSoundRunning = Group(leVariable)("target") + SupLit("=") + Literal("isSoundRunning")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_lights = Literal("lights")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leByte)("arg2") + SupLit(",") + Group(leByte)("arg3") + SupLit(")")
        self.grFunc_loadRoom = Literal("loadRoom")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        
        # --- Start sub-opcodes ---
        # V3 only supports setBoxFlags, so we just mark all of these as Forwards and override as appropriate.
        # (Forwards will not match anything if they are never fully defined.)
        self.grFunc_matrixOp_setBoxFlags = Forward()
        self.grFunc_matrixOp_setBoxScale = Forward()
        self.grFunc_matrixOp_SetBoxSlot = Forward()
        self.grFunc_matrixOp_createBoxMatrix = Forward()
        self.grFunc_matrixOp_SO = self.grFunc_matrixOp_setBoxFlags | self.grFunc_matrixOp_setBoxScale | self.grFunc_matrixOp_SetBoxSlot | self.grFunc_matrixOp_createBoxMatrix
        # --- End sub-opcodes ---
        
        self.grFunc_panCameraTo = Literal("panCameraTo")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        
        # --- Start sub-opcodes ---
        self.grFunc_print_Pos = Literal("Pos")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_print_Color = Literal("Color")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_print_Clipped = Literal("Clipped")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_print_RestoreBG = Literal("RestoreBG")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_print_Center = Literal("Center")("function") + SupLit("(") + SupLit(")")
        # Shared grammar for Left (V4-5) or Height (V3) functions
        self.grFunc_print_LeftHeight = Forward()
        self.grFunc_print_Overhead = Literal("Overhead")("function") + SupLit("(") + SupLit(")")
        # PlayCDTrack is only used in LoomCD, but we will just allow it for all.
        self.grFunc_print_PlayCDTrack = Literal("PlayCDTrack")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_print_Text = Literal("Text")("function") + SupLit("(") + NamedElement(leString, "arg1") + SupLit(")")
        self.grFunc_print_SO = self.grFunc_print_Pos | self.grFunc_print_Color | self.grFunc_print_Clipped | self.grFunc_print_RestoreBG | self.grFunc_print_Center | self.grFunc_print_LeftHeight | self.grFunc_print_Overhead | self.grFunc_print_PlayCDTrack | self.grFunc_print_Text
        # --- End sub-opcodes ---
        self.grFunc_print = Literal("print")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + SupLit("[") + Optional(delimitedList(self.grFunc_print_SO))("arg2") + SupLit("]")  + SupLit(")")
        self.grFunc_putActor = Literal("putActor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(",") + Group(leVarOrWord)("arg3") + SupLit(")")
        self.grFunc_putActorAtObject = Literal("putActorAtObject")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_putActorInRoom = Literal("putActorInRoom")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        
        # --- Start sub-opcodes ---
        self.grFunc_Resource_ResourceloadScript = Literal("Resource.loadScript")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceloadSound = Literal("Resource.loadSound")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceloadCostume = Literal("Resource.loadCostume")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceloadRoom = Literal("Resource.loadRoom")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcenukeScript = Literal("Resource.nukeScript")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcenukeSound = Literal("Resource.nukeSound")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcenukeCostume = Literal("Resource.nukeCostume")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcenukeRoom = Literal("Resource.nukeRoom")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcelockScript = Literal("Resource.lockScript")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcelockSound = Literal("Resource.lockSound")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcelockCostume = Literal("Resource.lockCostume")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcelockRoom = Literal("Resource.lockRoom")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceunlockScript = Literal("Resource.unlockScript")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceunlockSound = Literal("Resource.unlockSound")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceunlockCostume = Literal("Resource.unlockCostume")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceunlockRoom = Literal("Resource.unlockRoom")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceclearHeap = Literal("Resource.clearHeap")("function") + SupLit("(") + SupLit(")")
        self.grFunc_Resource_ResourceloadCharset = Literal("Resource.loadCharset")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourcenukeCharset = Literal("Resource.nukeCharset")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_Resource_ResourceloadFlObject = Literal("Resource.loadFlObject")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_Resource_SO = self.grFunc_Resource_ResourceloadScript | self.grFunc_Resource_ResourceloadSound | self.grFunc_Resource_ResourceloadCostume | self.grFunc_Resource_ResourceloadRoom | self.grFunc_Resource_ResourcenukeScript | self.grFunc_Resource_ResourcenukeSound | self.grFunc_Resource_ResourcenukeCostume | self.grFunc_Resource_ResourcenukeRoom | self.grFunc_Resource_ResourcelockScript | self.grFunc_Resource_ResourcelockSound | self.grFunc_Resource_ResourcelockCostume | self.grFunc_Resource_ResourcelockRoom | self.grFunc_Resource_ResourceunlockScript | self.grFunc_Resource_ResourceunlockSound | self.grFunc_Resource_ResourceunlockCostume | self.grFunc_Resource_ResourceunlockRoom | self.grFunc_Resource_ResourceclearHeap | self.grFunc_Resource_ResourceloadCharset | self.grFunc_Resource_ResourcenukeCharset | self.grFunc_Resource_ResourceloadFlObject
        # --- End sub-opcodes ---
        
        self.grFunc_saveLoadGame = Forward()
        self.grFunc_saveLoadVars = Forward()
        self.grFunc_setCameraAt = Literal("setCameraAt")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_setObjectName = Literal("setObjectName")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + NamedElement(leString, "arg2") + SupLit(")")
        self.grFunc_setOwnerOf = Literal("setOwnerOf")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_setState = Literal("setState")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_soundKludge = Literal("soundKludge")("function") + SupLit("(") + leArgList("arg1") + SupLit(")")
        self.grFunc_startMusic = Literal("startMusic")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_startObject = Literal("startObject")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(",") + leArgList("arg3") + SupLit(")")
        self.grFunc_startSound = Literal("startSound")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_stopMusic = Literal("stopMusic")("function") + SupLit("(") + SupLit(")")
        self.grFunc_stopObjectScript = Literal("stopObjectScript")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_stopScript = Literal("stopScript")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_stopSound = Literal("stopSound")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        
        # --- Start sub-opcodes ---
        self.grFunc_stringOps_PutCodeInString = Literal("PutCodeInString")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Optional(NamedElement(leString, "arg2")) + SupLit(")")
        self.grFunc_stringOps_CopyString = Literal("CopyString")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_stringOps_SetStringChar = Literal("SetStringChar")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(",") + Group(leVarOrByte)("arg3") + SupLit(")")
        self.grFunc_stringOps_GetStringChar = Group(leVariable)("target") + SupLit("=") + Literal("GetStringChar")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_stringOps_CreateString = Literal("CreateString")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_stringOps_SO = self.grFunc_stringOps_PutCodeInString | self.grFunc_stringOps_CopyString | self.grFunc_stringOps_SetStringChar | self.grFunc_stringOps_GetStringChar | self.grFunc_stringOps_CreateString
        # --- End sub-opcodes ---

        # --- Start sub-opcodes ---
        self.grFunc_VerbOps_Image = Literal("Image")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_VerbOps_Text = Literal("Text")("function") + SupLit("(") + NamedElement(leString, "arg1") + SupLit(")")
        self.grFunc_VerbOps_Color = Literal("Color")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_VerbOps_HiColor = Literal("HiColor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_VerbOps_SetXY = Literal("SetXY")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_VerbOps_On = Literal("On")("function") + SupLit("(") + SupLit(")")
        self.grFunc_VerbOps_Off = Literal("Off")("function") + SupLit("(") + SupLit(")")
        self.grFunc_VerbOps_Delete = Literal("Delete")("function") + SupLit("(") + SupLit(")")
        self.grFunc_VerbOps_New = Literal("New")("function") + SupLit("(") + SupLit(")")
        self.grFunc_VerbOps_DimColor = Literal("DimColor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_VerbOps_Dim = Literal("Dim")("function") + SupLit("(") + SupLit(")")
        self.grFunc_VerbOps_Key = Literal("Key")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_VerbOps_Center = Literal("Center")("function") + SupLit("(") + SupLit(")")
        self.grFunc_VerbOps_SetToString = Literal("SetToString")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_VerbOps_SetToObject = Literal("SetToObject")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_VerbOps_BackColor = Literal("BackColor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_VerbOps_SO = self.grFunc_VerbOps_Image | self.grFunc_VerbOps_Text | self.grFunc_VerbOps_Color | self.grFunc_VerbOps_HiColor | self.grFunc_VerbOps_SetXY | self.grFunc_VerbOps_On | self.grFunc_VerbOps_Off | self.grFunc_VerbOps_Delete | self.grFunc_VerbOps_New | self.grFunc_VerbOps_DimColor | self.grFunc_VerbOps_Dim | self.grFunc_VerbOps_Key | self.grFunc_VerbOps_Center | self.grFunc_VerbOps_SetToString | self.grFunc_VerbOps_SetToObject | self.grFunc_VerbOps_BackColor
        # --- End sub-opcodes ---
        self.grFunc_VerbOps = Literal("VerbOps")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + SupLit("[") + Optional(delimitedList(self.grFunc_VerbOps_SO))("arg2") + Optional(SupLit(";")) + SupLit("]")  + SupLit(")")
        
        # --- Start sub-opcodes ---
        self.grFunc_wait_WaitForActor = Literal("WaitForActor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_wait_WaitForMessage = Literal("WaitForMessage")("function") + SupLit("(") + SupLit(")")
        self.grFunc_wait_WaitForCamera = Literal("WaitForCamera")("function") + SupLit("(") + SupLit(")")
        self.grFunc_wait_WaitForSentence = Literal("WaitForSentence")("function") + SupLit("(") + SupLit(")")
        self.grFunc_wait_SO = self.grFunc_wait_WaitForActor | self.grFunc_wait_WaitForMessage | self.grFunc_wait_WaitForCamera | self.grFunc_wait_WaitForSentence
        # --- End sub-opcodes ---
        
        
        self.grFunc_walkActorTo = Literal("walkActorTo")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(",") + Group(leVarOrWord)("arg3") + SupLit(")")
        self.grFunc_walkActorToActor = Literal("walkActorToActor")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(",") + Group(leByte)("arg3") + SupLit(")")
        self.grFunc_walkActorToObject = Literal("walkActorToObject")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunctions = (self.grFunc_actorFollowCamera | self.grFunc_actorFromPos | self.grFunc_ActorOps | self.grFunc_setClass |
                       self.grFunc_animateCostume | self.grFunc_breakHere | self.grFunc_chainScript | self.grFunc_cursorCommand_SO |
                       self.grFunc_cutscene | self.grFunc_debug | self.grFunc_delayVariable | self.grFunc_dummyA7 | self.grFunc_endCutscene |
                       self.grFunc_faceActor | self.grFunc_findInventory | self.grFunc_findObject | self.grFunc_freezeScripts |
                       self.grFunc_getActorCostume | self.grFunc_getActorElevation | self.grFunc_getActorFacing | self.grFunc_getActorMoving |
                       self.grFunc_getActorRoom | self.grFunc_getActorScale | self.grFunc_getActorWalkBox | self.grFunc_getActorWidth |
                       self.grFunc_getActorX | self.grFunc_getActorY | self.grFunc_getAnimCounter | self.grFunc_getClosestObjActor |
                       self.grFunc_getDist | self.grFunc_getInventoryCount | self.grFunc_getObjectOwner | self.grFunc_getObjectState |
                       self.grFunc_getRandomNr | self.grFunc_getStringWidth | self.grFunc_getVerbEntryPoint | self.grFunc_isScriptRunning |
                       self.grFunc_isSoundRunning | self.grFunc_lights | self.grFunc_loadRoom | self.grFunc_matrixOp_SO | self.grFunc_panCameraTo |
                       self.grFunc_print | self.grFunc_putActor | self.grFunc_putActorAtObject | self.grFunc_putActorInRoom |
                       self.grFunc_Resource_SO | self.grFunc_saveLoadGame | self.grFunc_saveLoadVars |
                       self.grFunc_setCameraAt | self.grFunc_setObjectName | self.grFunc_setOwnerOf |
                       self.grFunc_setState | self.grFunc_soundKludge | self.grFunc_startMusic | self.grFunc_startObject | self.grFunc_startSound |
                       self.grFunc_stopMusic | self.grFunc_stopObjectScript | self.grFunc_stopScript | self.grFunc_stopSound |
                       self.grFunc_stringOps_SO | self.grFunc_VerbOps | self.grFunc_wait_SO | self.grFunc_walkActorTo |
                       self.grFunc_walkActorToActor | self.grFunc_walkActorToObject)
        # ~~~~~~~~~~~~ End Mostly Auto-Generated Functions ~~~~~~~~~~~~~
        
        
        
        # Inline opcodes (not function calls)
        self.grInlineOperation = Group(leVariable)("target") + oneOf("+= -= /= *= &= |= =")("operation") + Group(leVarOrWord)("value")
        self.grIncDec = Group(leVariable)("target") + oneOf("++ --")("operation") # not sure if Bits can be incremented/decremented
        
        # Jumps
        self.grJumpLabel = SupLit("[") + leLabel("label") + SupLit("]")
        self.grJumpGoto = SupLit("goto") + leLabel("target")
        self.grJumpExpression = self.grJumpGoto
        
        # Comparison & conditional jump/"if" related opcodes
        self.grIfComparison = Group(leVariable)("arg1") + oneOf(" ".join(opComparisons.keys()))("comparator") + Group(leVarOrWord)("arg2")
        self.grIfZeroEquality = Optional(Literal("!")("!")) + leVariable
        self.grIfClassOfIs = Literal("classOfIs")("function") + SupLit("(") + Group(leVarOrWord)("testobject") + SupLit(",") + leArgList("classes") + LegacyElement(SupLit(")"), ELEMENT_OPTIONAL, ELEMENT_REQUIRED) # legacy descumm forgets to add the last parenthesis
        self.grIfActorInBox = Literal("isActorInBox")("function") + SupLit("(") + Group(leVarOrByte)("actor") + SupLit(",") + Group(leVarOrByte)("box") + SupLit(")")
        self.grIfState = Forward() # V3-4
        self.grBooleanExpression = self.grIfComparison ^ self.grIfZeroEquality ^ self.grIfClassOfIs ^ self.grIfActorInBox ^ self.grIfState
        self.grJumpUnless = SupLit("unless") + SupLit("(") + (self.grBooleanExpression)("test") + SupLit(")") + SupLit("goto") + leLabel("target")
        self.grIfStart = SupLit("if") + SupLit("(") + (self.grBooleanExpression) + SupLit(")") + SupLit("{")
        self.grIfElse = SupLit("}") + SupLit("else")
        self.grIfEnd = SupLit("}")
        
        # Other control flow
        self.grWhileStart = SupLit("while") + SupLit("(") + self.grBooleanExpression + SupLit(")") + SupLit("{")
        self.grWhileEnd = SupLit("}") # obviously this conflicts with grIfEnd...
        self.grDoWhileStart = SupLit("do") + SupLit("{")
        self.grDoWhileEnd = SupLit("}") + SupLit("while") + SupLit("(") + self.grBooleanExpression + SupLit(")")
        self.grForLoopStart = (SupLit("for") + SupLit("(") +
                          Optional(self.grInlineOperation)("init") + SupLit(";") + 
                          Group(self.grBooleanExpression)("test") + SupLit(";") + 
                          Optional(self.grInlineOperation | self.grIncDec)("increm") +
                          SupLit(")") + SupLit("{")) # "For" loops only allow basic inline maths for now
        self.grForLoopEnd = SupLit("}")
        
        
        # This used to be below but I need it for startScript
        self.grDescummOpcode = SupLit("(") + (leHexByte | leLabel | Literal("**"))("dop") + SupLit(")")
        
        # Functions that can't be automatically generated due to quirks in their grammar.
        
        # delay has its own type of argument, a 24-bit constant
        self.grFunc_delay = Literal("delay")("function") + SupLit("(") + Group(leDelay)("arg1") + SupLit(")")
        # doSentence normally takes 3 params, except when it only takes 1 (which is 0xFE, descumm outputs it as "STOP")
        self.grFunc_doSentence = (Literal("doSentence")("function") + SupLit("(") +
                             (Literal("STOP")("arg1") | (Group(leVarOrByte)("arg1") + SupLit(",") +
                                                         Group(leVarOrWord)("arg2") + SupLit(",") +
                                                         Group(leVarOrWord)("arg3")
                                                         )
                             ) + SupLit(")"))
        # drawBox has aux opcodes
        self.grFunc_drawBox = ( Literal("drawBox")("function") + SupLit("(") +
                          Group(leVarOrWord)("left") + SupLit(",") + 
                          Group(leVarOrWord)("top") + Optional(SupLit(";")) + SupLit(",") + # workaround for descumm extra semicolons
                          Group(leVarOrWord)("right") + SupLit(",") +
                          Group(leVarOrWord)("bottom") + SupLit(",") +
                          Group(leVarOrByte)("colour") + SupLit(")") )
        # drawObject is different in V3-4 and V5
        self.grFunc_drawObject = Forward()
        # loadRoomWithEgo has two params and two constants
        self.grFunc_loadRoomWithEgo = (Literal("loadRoomWithEgo")("function") + SupLit("(") +
                                  Group(leVarOrWord)("object") + SupLit(",") +
                                  Group(leVarOrByte)("room") + SupLit(",") +
                                  leWord("x") + SupLit(",") +
                                  leWord("y") +
                                  SupLit(")"))
        # oldRoomEffect is dodgy
        self.grFunc_oldRoomEffect = Forward() #V3-4
        # override in legacy descumm is like a soft bunny without ears (no parentheses) (except those) (and those)
        self.grFunc_override = (Literal("beginOverride") | Literal("endOverride"))("function") + LegacyElement(SupLit("(") + SupLit(")"), ELEMENT_OPTIONAL, ELEMENT_REQUIRED)
        # pickupObject can be one of two opcodes, one which takes a word and a byte, the other ("pickupObjectOld") only takes a word.
        #self.grFunc_pickupObject = Literal("pickupObject")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + Optional( SupLit(",") + Group(leVarOrByte)("arg2") ) + SupLit(")")
        self.grFunc_pickupObject = Forward()
        # "printEgo" re-uses the sub-opcodes for "print"
        self.grFunc_printEgo = Literal("printEgo")("function") + SupLit("(") + SupLit("[") + Optional(delimitedList(self.grFunc_print_SO))("arg1") + SupLit("]")  + SupLit(")")
        # pseudoRoom takes one constant followed by a variable number of constants.
        # Each res item is ORed with 0x80. A value of 0x80 is output as "IG" in descumm.
        self.grFunc_PseudoRoom = (Literal("PseudoRoom")("function") + SupLit("(") +
                             leByte("val") + SupLit(",") + 
                             delimitedList(leByte | Literal("IG"))("reslist") +
                             SupLit(")")
                            )
        # roomOps has sub-opcodes with non-standard encoding (mostly because of red, green, blue values)
        # A few sub-ops (RoomIntensity, SetScren) output an extra closing parenthesis
        
        self.grFunc_roomOps_RoomScroll = Forward()
        self.grFunc_roomOps_RoomColor = Forward()
        self.grFunc_roomOps_SetScreen = Forward()
        self.grFunc_roomOps_ShakeOn = Forward()
        self.grFunc_roomOps_ShakeOff = Forward()
        self.grFunc_roomOps_RoomIntensity = Forward()
        self.grFunc_roomOps_saveLoad = Forward()
        # screenEffect has a question mark and extra closing parenthesis
        self.grFunc_roomOps_screenEffect = Forward()
        self.grFunc_roomOps_colorCycleDelay = Forward()
        # Uses aux opcode, also extra closing parenthesis
        self.grFunc_roomOps_SetPalColor = Forward()
        # Lots of parameters, descumm calls it "Unused" which (while possibly true) isn't very descriptive
        self.grFunc_roomOps_SetRoomScale = Forward()
        # This has params and an aux opcode, but I'm also cheating and using this for setRoomShadow.
        self.grFunc_roomOps_setRGBRoomIntensity = Forward()
        # Share grammar & parse action for saveString and loadString
        self.grFunc_roomOps_saveLoadString = Forward()
        # Lots of params & aux opcodes
        self.grFunc_roomOps_palManipulate = Forward()
        # This big thing marks the end of roomOps, phew! Also, looks like a lot of roomOps add
        #  an extra closing parenthesis in legacy descumm, so account for that here instead of in each sub-op.
        self.grFunc_roomOps_SO = (self.grFunc_roomOps_RoomScroll | self.grFunc_roomOps_RoomColor | self.grFunc_roomOps_SetScreen | self.grFunc_roomOps_ShakeOn | self.grFunc_roomOps_ShakeOff | 
                             self.grFunc_roomOps_RoomIntensity | self.grFunc_roomOps_saveLoad | self.grFunc_roomOps_screenEffect | 
                             self.grFunc_roomOps_colorCycleDelay | self.grFunc_roomOps_SetPalColor | self.grFunc_roomOps_SetRoomScale |
                             self.grFunc_roomOps_setRGBRoomIntensity | self.grFunc_roomOps_saveLoadString | self.grFunc_roomOps_palManipulate) + LegacyElement(SupLit(")"), ELEMENT_OPTIONAL, ELEMENT_OMITTED)
        # setVarRange takes a starting variable, the number of constants that will be next in the instruction (I'm making this optional),
        #  and a delmitedList of either bytes or words (but not mixed). We determine which in the parse action.
        self.grFunc_setVarRange = (Literal("setVarRange")("function") + SupLit("(") +
                              Group(leVariable)("startvar") + Optional(SupLit(";")) + SupLit(",") + # workaround for dodgy descumm semi-colons
                              Optional(leByte("numitems") + SupLit(",")) +
                              SupLit("[") + delimitedList(leByte | leWord)("listvals") + SupLit("]") +
                              SupLit(")"))
        # saveRestoreVerbs - I originally misunderstood this instruction; I thought it had an aux opcode, three params, then a sub-opcode,
        #  when it actually just has a sub-opcode and three params. Still, this is more concise than the auto-generated instruction would be.
        self.grFunc_saveRestoreVerbs_saveVerbs = Literal("saveVerbs")
        self.grFunc_saveRestoreVerbs_restoreVerbs = Literal("restoreVerbs")
        self.grFunc_saveRestoreVerbs_deleteVerbs = Literal("deleteVerbs")
        self.grFunc_saveRestoreVerbs = ((self.grFunc_saveRestoreVerbs_saveVerbs | self.grFunc_saveRestoreVerbs_restoreVerbs | self.grFunc_saveRestoreVerbs_deleteVerbs)("function") + SupLit("(") +
                                    Group(leVarOrByte)("start") + SupLit(",") +
                                    Group(leVarOrByte)("end") + SupLit(",") +
                                    Group(leVarOrByte)("mode") +
                                    SupLit(")")
                                    )
        # startScript modifies the opcode, but descumm doesn't 
        self.grFunc_startScript = (Literal("startScript")("function") + SupLit("(") +
                              Group(leVarOrByte)("arg1") + SupLit(",") +
                              leArgList("arg2") +
                              Optional(SupLit(",") + Literal("F"))("freezeres") + 
                              Optional(SupLit(",") + Literal("R"))("recursive") + 
                              SupLit(")"))
        # stopObjectCode must be the last item in a script
        self.grFunc_stopObjectCode = Literal("stopObjectCode")("function") + SupLit("(") + SupLit(")")
        # systemOps takes sub-opcodes, but they're only represented as the numbers 1, 2, or 3. I also allow meaningful words.
        self.grFunc_systemOps = (Literal("systemOps")("function") + SupLit("(") +
                            ((Literal("1") | Literal("RESTART")) | (Literal("2") | Literal("PAUSE")) | (Literal("3") | Literal("QUIT")))("subop") + # this is a bit crap
                            SupLit(")"))
        # ... here endeth the quirky functions
        
        # Pragramas (compiler directives)
        self.grPragmaScriptNum = Literal("Script#") + leUnsignedInt("scriptnum")
        self.grPragmaEventTable = SupLit("Events:") + OneOrMore(Group(Word(nums + srange("[a-fA-F]"), max=2)("key") + SupLit("-") + leLabel("value")))("entries") # keys shouldn't be leLabels
        self.grPragmaScriptType = SupLit("#script-type") + oneOf("entry exit global local object verb")("stype")
        # V3-4 stores object metadata with the code block.
        self.grPragmaOldObjectData_id = Literal("id")("key") + leWord("val")
        self.grPragmaOldObjectData_unknown = Literal("unknown")("key") + leByte("val")
        self.grPragmaOldObjectData_xPos = Literal("x-pos")("key") + leByte("val")
        self.grPragmaOldObjectData_yPos = Literal("y-pos")("key") + leByte("val")
        self.grPragmaOldObjectData_parentState = Literal("parent-state")("key") + (Literal("0") | Literal("1"))("val")
        self.grPragmaOldObjectData_imageWidth = Literal("width")("key") + leByte("val")
        self.grPragmaOldObjectData_parent = Literal("parent")("key") + leByte("val")
        self.grPragmaOldObjectData_walkX = Literal("walk-x")("key") + leWord("val")
        self.grPragmaOldObjectData_walkY = Literal("walk-y")("key") + leWord("val")
        self.grPragmaOldObjectData_height = Literal("height")("key") + leByte("val")
        self.grPragmaOldObjectData_actorDir = Literal("actor-dir")("key") + leByte("val")
        self.grPragmaOldObjectData_name = Literal("name")("key") + NamedElement(leString, "val") # possibly parsing issues using leString
        self.grPragmaOldObjectData_SO = (self.grPragmaOldObjectData_id | self.grPragmaOldObjectData_unknown | self.grPragmaOldObjectData_xPos |
                                    self.grPragmaOldObjectData_yPos | self.grPragmaOldObjectData_parentState | self.grPragmaOldObjectData_imageWidth |
                                    self.grPragmaOldObjectData_parent | self.grPragmaOldObjectData_walkX | self.grPragmaOldObjectData_walkY |
                                    self.grPragmaOldObjectData_height | self.grPragmaOldObjectData_actorDir | self.grPragmaOldObjectData_name)
        self.grPragmaOldObjectData = (SupLit("#object-data") + Optional(SupLit("[")) +
                                 delimitedList(Group(self.grPragmaOldObjectData_SO))("objdata") +
                                 Optional(SupLit("]"))
                                 )
        self.grPragmaDefine = SupLit("#define") + leDefinedValueDef + Optional(SupLit("=")) + Group(leVarOrWord)
        self.grPragma = self.grPragmaScriptNum | self.grPragmaDefine | self.grPragmaEventTable | self.grPragmaScriptType | self.grPragmaOldObjectData
        
        # All quirky functions
        self.grQuirkyFunctions = (self.grFunc_printEgo | self.grFunc_delay | self.grFunc_doSentence | self.grFunc_drawBox | self.grFunc_drawObject | self.grFunc_loadRoomWithEgo | self.grFunc_pickupObject |
                             self.grFunc_PseudoRoom | self.grFunc_oldRoomEffect | self.grFunc_override | self.grFunc_setVarRange | self.grFunc_saveRestoreVerbs | self.grFunc_systemOps | 
                             self.grFunc_roomOps_SO | self.grFunc_stopObjectCode)
        
        # Expression mode stuff
        self.grSubExpression = Forward()
        self.grExpressionOpcode = SupLit("<") + (self.grQuirkyFunctions | self.grFunctions)("expop") + Optional(SupLit(";")) + SupLit(">") # TODO: make this only funcs that return a result
        self.grExpressionMode = (SupLit("Exprmode") +
                            Group(leVariable)("target") +
                            SupLit("=") +
                            Group(self.grSubExpression | self.grExpressionOpcode | leVarOrWord)("subexp"))
        self.grSubExpression << (SupLit("(") +
                            Group(leVarOrWord | self.grSubExpression | self.grExpressionOpcode)("arg1") +
                            oneOf("+ - / * =")("operation") +
                            Group(leVarOrWord | self.grSubExpression | self.grExpressionOpcode)("arg2") +
                            SupLit(")"))
        
        # Blocks and larger constructs
        self.grConstruct = self.grIncDec | self.grInlineOperation | self.grExpressionMode | self.grJumpGoto | self.grJumpUnless | self.grQuirkyFunctions | self.grFunctions # single-line construct
        self.grLinePrefix = Optional(self.grJumpLabel) + Suppress(Optional(self.grDescummOpcode))
        self.grLineSuffix = Suppress(Optional(leComment))
        
        # grStartScriptLine is a hack to get around legacy descumm not outputting the extra opcode flags
        # Should probably make this use LegaqcyElement somehow...
        self.grStartScriptLine = Optional(self.grJumpLabel) + Optional(self.grDescummOpcode)("descummop") + self.grFunc_startScript + LegacyElement(SupLit(";"), ELEMENT_OPTIONAL, ELEMENT_REQUIRED) + self.grLineSuffix
        # grStopObjectCodeLine marks the end of a script
        self.grStopObjectCodeLine = self.grLinePrefix + self.grFunc_stopObjectCode + self.grLineSuffix
        self.grNormalLine = self.grLinePrefix + ((self.grConstruct + LegacyElement(SupLit(";"), ELEMENT_OPTIONAL, ELEMENT_OPTIONAL)) | Suppress(leComment)) + self.grLineSuffix # TODO: make this legacyElemnt Optional/Required, when descumm is fixed
        self.grIfLineStart = self.grLinePrefix + self.grIfStart + self.grLineSuffix
        self.grIfLineElse = self.grLinePrefix + self.grIfElse + (Optional(self.grIfStart)("elseif") ^ SupLit("{")) + self.grLineSuffix
        self.grIfLineEnd = self.grLinePrefix + self.grIfEnd + self.grLineSuffix
        
        self.grWhileLineStart = self.grLinePrefix + self.grWhileStart + self.grLineSuffix
        self.grWhileLineEnd = self.grLinePrefix + self.grWhileEnd + self.grLineSuffix
        self.grDoWhileLineStart = self.grLinePrefix + self.grDoWhileStart + self.grLineSuffix
        self.grDoWhileLineEnd = self.grLinePrefix + self.grDoWhileEnd + self.grLineSuffix
        self.grForLoopLineStart = self.grLinePrefix + self.grForLoopStart + self.grLineSuffix
        self.grForLoopLineEnd = self.grLinePrefix + self.grForLoopEnd + self.grLineSuffix
        
        self.grBlock = Forward()
        # grBlock is optional, because descumm might try to be clever and create "if/else" statements when it's just doing
        #  conditional jumps.
        self.grIfBlock = self.grIfLineStart + Optional(OneOrMore(self.grBlock)) + Optional(OneOrMore(self.grIfLineElse + ZeroOrMore(self.grBlock))) + self.grIfLineEnd
        self.grWhileBlock = self.grWhileLineStart + OneOrMore(self.grBlock) + self.grWhileLineEnd
        self.grDoWhileBlock = self.grDoWhileLineStart + OneOrMore(self.grBlock) + self.grDoWhileLineEnd
        self.grForLoopBlock = self.grForLoopLineStart + OneOrMore(self.grBlock) + self.grForLoopLineEnd
        #grBlock << (grNormalLine ^ grStartScriptLine ^ grIfBlock ^ grDoWhileBlock ^ grWhileBlock ^ grForLoopBlock)
        self.grBlock << (self.grNormalLine | self.grStartScriptLine | self.grIfBlock | self.grDoWhileBlock | self.grWhileBlock | self.grForLoopBlock)
        # I have removed grStopObjectCodeLine as the compulsory last object since OBCD scripts have them spread throughout the script,
        #  so we will match it once and then fail on the compulsory check.
        #grMainBlock = StringStart() + ZeroOrMore(grPragma) + ZeroOrMore(grBlock) + grStopObjectCodeLine + Optional(SupLit("END")) + StringEnd()
        self.grMainBlock = StringStart() + ZeroOrMore(self.grPragma) + ZeroOrMore(self.grBlock) + Optional(SupLit("END")) + StringEnd()
        # This is used for testing, so we don't have to put "stopObjectCode()" at the end of every test
        self.grMainBlockTesting = StringStart() + ZeroOrMore(self.grPragma) + ZeroOrMore(self.grBlock) + Optional(self.grStopObjectCodeLine) + Optional(SupLit("END")) + StringEnd()
        self.rootExpression = 'grMainBlock'
        self.testExpression = 'grMainBlockTesting'

class GrammarV3Old(GrammarV345Common):
    def overrideGrammar(self):
        leKnownGlobalVar << oneOf(" ".join( (vn for vn in scummbler_vars.varNames3list if vn != None) ))("knownvar") #dodgy
        self.grFunc_ActorOps_Scale << Literal("Scale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_pickupObject << Literal("pickupObject")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_cursorCommand_CursorCommandLoadCharset << Literal("LoadCharset")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_drawObject << (Literal("drawObject")("function") + SupLit("(") +
                                        Group(leVarOrWord)("arg1") +
                                        SupLit(",") + Group(leVarOrWord)("arg2")  +
                                        SupLit(",") + Group(leVarOrWord)("arg3")  +
                                        SupLit(")"))
        self.grFunc_matrixOp_setBoxFlags << Literal("setBoxFlags")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leByte)("arg2") + SupLit(")")
        self.grFunc_print_LeftHeight << Literal("Height")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        # roomOps
        self.grFunc_roomOps_RoomScroll << Literal("RoomScroll")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_RoomColor << Literal("RoomColor")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_SetScreen << Literal("SetScreen")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_SetPalColor << (Literal("SetPalColor")("function") + SupLit("(") + 
                                                Group(leVarOrWord)("arg1") + SupLit(",") + 
                                                Group(leVarOrWord)("arg2") + 
                                                SupLit(")")
                                                )
        self.grFunc_roomOps_ShakeOn << Literal("ShakeOn")("function") + SupLit("(") + SupLit(")")
        self.grFunc_roomOps_ShakeOff << Literal("ShakeOff")("function") + SupLit("(") + SupLit(")")
        self.grIfState << Literal("getState")("function") + SupLit("(") + Group(leVarOrWord)("testobject") + (Literal("==") | Literal("!="))("comparator") + Group(leVarOrByte)("state") + SupLit(")")
        self.grFunc_saveLoadGame << Group(leVariable)("target") + SupLit("=") + Literal("saveLoadGame")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_oldRoomEffect << ((Literal("oldRoomEffect-set") | Literal("oldRoomEffect-fadein"))("function") + SupLit("(") +
                                            Group(leVarOrWord)("effect") +
                                            SupLit(")")
                                            )
        self.grFunc_saveLoadVars_VarRange = (Literal("VarRange")("function") + SupLit("(") +
                                                  Group(leVariable)("arg1") + SupLit(",") +
                                                  Group(leVariable)("arg2") +
                                                  SupLit(")"))
        self.grFunc_saveLoadVars_StringRange = (Literal("StringRange")("function") + SupLit("(") +
                                                    Group(leVarOrByte)("arg1") + SupLit(",") +
                                                    Group(leVarOrByte)("arg2") +
                                                    SupLit(")"))
        self.grFunc_saveLoadVars_Open = (Literal("Open") + SupLit("(") +
                                              Group(leString)("arg1") +
                                              SupLit(")"))
        self.grFunc_saveLoadVars_Append = (Literal("Append"))("function")
        self.grFunc_saveLoadVars_Close = (Literal("Close"))("function")
        self.grFunc_saveLoadVars << (Literal("saveLoadVars")("function") + SupLit("(") +
                                          (Literal("Save") | Literal("Load"))("operation") +
                                          ZeroOrMore(SupLit(",") + (self.grFunc_saveLoadVars_VarRange |
                                                                    self.grFunc_saveLoadVars_StringRange |
                                                                    self.grFunc_saveLoadVars_Open))("subops") +
                                          Optional((SupLit(",") + self.grFunc_saveLoadVars_Append) |
                                                   (SupLit(",") + self.grFunc_saveLoadVars_Close))("lastop") +
                                          SupLit(")")
                                          )
        # The below is the only difference in grammar; the rest is handled in the compiler.
        self.grFunc_getActorX << Group(leVariable)("target") + SupLit("=") + Literal("getActorX")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorY << Group(leVariable)("target") + SupLit("=") + Literal("getActorY")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")

class GrammarV3(GrammarV345Common):
    def overrideGrammar(self):
        leKnownGlobalVar << oneOf(" ".join( (vn for vn in scummbler_vars.varNames3list if vn != None) ))("knownvar") #dodgy
        self.grFunc_ActorOps_Scale << Literal("Scale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_pickupObject << Literal("pickupObject")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_cursorCommand_CursorCommandLoadCharset << Literal("LoadCharset")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_drawObject << (Literal("drawObject")("function") + SupLit("(") +
                                        Group(leVarOrWord)("arg1") +
                                        SupLit(",") + Group(leVarOrWord)("arg2")  +
                                        SupLit(",") + Group(leVarOrWord)("arg3")  +
                                        SupLit(")"))
        self.grFunc_matrixOp_setBoxFlags << Literal("setBoxFlags")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leByte)("arg2") + SupLit(")")
        self.grFunc_print_LeftHeight << Literal("Height")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        # roomOps
        self.grFunc_roomOps_RoomScroll << Literal("RoomScroll")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_RoomColor << Literal("RoomColor")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_SetScreen << Literal("SetScreen")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_SetPalColor << (Literal("SetPalColor")("function") + SupLit("(") + 
                                                Group(leVarOrWord)("arg1") + SupLit(",") + 
                                                Group(leVarOrWord)("arg2") + 
                                                SupLit(")")
                                                )
        self.grFunc_roomOps_ShakeOn << Literal("ShakeOn")("function") + SupLit("(") + SupLit(")")
        self.grFunc_roomOps_ShakeOff << Literal("ShakeOff")("function") + SupLit("(") + SupLit(")")
        self.grIfState << Literal("getState")("function") + SupLit("(") + Group(leVarOrWord)("testobject") + SupLit(")") + (Literal("==") | Literal("!="))("comparator") + Group(leVarOrByte)("state")
        self.grFunc_saveLoadGame << Group(leVariable)("target") + SupLit("=") + Literal("saveLoadGame")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_oldRoomEffect << ((Literal("oldRoomEffect-set") | Literal("oldRoomEffect-fadein"))("function") + SupLit("(") +
                                            Group(leVarOrWord)("effect") +
                                            SupLit(")")
                                            )
        self.grFunc_saveLoadVars_VarRange = (Literal("VarRange")("function") + SupLit("(") +
                                                  Group(leVariable)("arg1") + SupLit(",") +
                                                  Group(leVariable)("arg2") +
                                                  SupLit(")"))
        self.grFunc_saveLoadVars_StringRange = (Literal("StringRange")("function") + SupLit("(") +
                                                    Group(leVarOrByte)("arg1") + SupLit(",") +
                                                    Group(leVarOrByte)("arg2") +
                                                    SupLit(")"))
        self.grFunc_saveLoadVars_Open = (Literal("Open") + SupLit("(") +
                                              Group(leString)("arg1") +
                                              SupLit(")"))
        self.grFunc_saveLoadVars_Append = (Literal("Append"))("function")
        self.grFunc_saveLoadVars_Close = (Literal("Close"))("function")
        self.grFunc_saveLoadVars << (Literal("saveLoadVars")("function") + SupLit("(") +
                                          (Literal("Save") | Literal("Load"))("operation") +
                                          ZeroOrMore(SupLit(",") + (self.grFunc_saveLoadVars_VarRange |
                                                                    self.grFunc_saveLoadVars_StringRange |
                                                                    self.grFunc_saveLoadVars_Open))("subops") +
                                          Optional((SupLit(",") + self.grFunc_saveLoadVars_Append) |
                                                   (SupLit(",") + self.grFunc_saveLoadVars_Close))("lastop") +
                                          SupLit(")")
                                          )
        self.grFunc_getActorX << Group(leVariable)("target") + SupLit("=") + Literal("getActorX")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_getActorY << Group(leVariable)("target") + SupLit("=") + Literal("getActorY")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        
class GrammarV4(GrammarV345Common):
    def overrideGrammar(self):
        leKnownGlobalVar << oneOf(" ".join( (vn for vn in scummbler_vars.varNames4list if vn != None) ))("knownvar") #dodgy
        self.grFunc_ActorOps_Scale << Literal("Scale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_pickupObject << Literal("pickupObject")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_cursorCommand_CursorCommandLoadCharset << Literal("CursorCommand")("function") + SupLit("(") + leArgList("arg1") + SupLit(")")
        self.grFunc_drawObject << (Literal("drawObject")("function") + SupLit("(") +
                                        Group(leVarOrWord)("arg1") +
                                        SupLit(",") + Group(leVarOrWord)("arg2")  +
                                        SupLit(",") + Group(leVarOrWord)("arg3")  +
                                        SupLit(")"))
        self.grFunc_matrixOp_setBoxFlags << Literal("setBoxFlags")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_matrixOp_setBoxScale << Literal("setBoxScale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_matrixOp_SetBoxSlot << Literal("SetBoxSlot")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_matrixOp_createBoxMatrix << Literal("createBoxMatrix")("function") + SupLit("(") + SupLit(")")
        self.grFunc_print_LeftHeight << Literal("Left")("function") + SupLit("(") + SupLit(")")
        # roomOps
        self.grFunc_roomOps_RoomScroll << Literal("RoomScroll")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_RoomColor << Literal("RoomColor")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_SetScreen << Literal("SetScreen")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_SetPalColor << (Literal("SetPalColor")("function") + SupLit("(") + 
                                                Group(leVarOrWord)("arg1") + SupLit(",") + 
                                                Group(leVarOrWord)("arg2") + 
                                                SupLit(")")
                                                )
        self.grFunc_roomOps_ShakeOn << Literal("ShakeOn")("function") + SupLit("(") + SupLit(")")
        self.grFunc_roomOps_ShakeOff << Literal("ShakeOff")("function") + SupLit("(") + SupLit(")")
        self.grIfState << Literal("getState")("function") + SupLit("(") + Group(leVarOrWord)("testobject") + SupLit(")") + (Literal("==") | Literal("!="))("comparator") + Group(leVarOrByte)("state")
        self.grFunc_saveLoadGame << Group(leVariable)("target") + SupLit("=") + Literal("saveLoadGame")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_oldRoomEffect << ((Literal("oldRoomEffect-set") | Literal("oldRoomEffect-fadein"))("function") + SupLit("(") +
                                            Group(leVarOrWord)("effect") +
                                            SupLit(")")
                                            )
        self.grFunc_saveLoadVars_VarRange = (Literal("VarRange")("function") + SupLit("(") +
                                                  Group(leVariable)("arg1") + SupLit(",") +
                                                  Group(leVariable)("arg2") +
                                                  SupLit(")"))
        self.grFunc_saveLoadVars_StringRange = (Literal("StringRange")("function") + SupLit("(") +
                                                    Group(leVarOrByte)("arg1") + SupLit(",") +
                                                    Group(leVarOrByte)("arg2") +
                                                    SupLit(")"))
        self.grFunc_saveLoadVars_Open = (Literal("Open") + SupLit("(") +
                                              Group(leString)("arg1") +
                                              SupLit(")"))
        self.grFunc_saveLoadVars_Append = (Literal("Append"))("function")
        self.grFunc_saveLoadVars_Close = (Literal("Close"))("function")
        self.grFunc_saveLoadVars << (Literal("saveLoadVars")("function") + SupLit("(") +
                                          (Literal("Save") | Literal("Load"))("operation") +
                                          ZeroOrMore(SupLit(",") + (self.grFunc_saveLoadVars_VarRange |
                                                                    self.grFunc_saveLoadVars_StringRange |
                                                                    self.grFunc_saveLoadVars_Open))("subops") +
                                          Optional((SupLit(",") + self.grFunc_saveLoadVars_Append) |
                                                   (SupLit(",") + self.grFunc_saveLoadVars_Close))("lastop")
                                          )
        self.grFunc_getActorX << Group(leVariable)("target") + SupLit("=") + Literal("getActorX")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_getActorY << Group(leVariable)("target") + SupLit("=") + Literal("getActorY")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        
class GrammarV5(GrammarV345Common):
    def overrideGrammar(self):
        leKnownGlobalVar << oneOf(" ".join( (vn for vn in scummbler_vars.varNames5list if vn != None) ))("knownvar") #dodgy
        self.grFunc_ActorOps_Scale << Literal("Scale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_ActorOps_NeverZClip << Literal("NeverZClip")("function") + SupLit("(") + SupLit(")")
        self.grFunc_ActorOps_SetZClip << Literal("SetZClip")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_FollowBoxes << Literal("FollowBoxes")("function") + SupLit("(") + SupLit(")")
        self.grFunc_ActorOps_AnimSpeed << Literal("AnimSpeed")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_ActorOps_ShadowMode << Literal("ShadowMode")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        
        self.grFunc_pickupObject << Literal("pickupObject")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_cursorCommand_CursorCommandLoadCharset << Literal("CursorCommand")("function") + SupLit("(") + leArgList("arg1") + SupLit(")")
        # drawObject omits opening bracket of 0x1F (unnamed sub-opcode) but accidentally leaves in the closing bracket.
        self.grFunc_drawObject_setXY = Literal("setXY")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_drawObject_setImage = Literal("setImage")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_drawObject_SO = self.grFunc_drawObject_setXY | self.grFunc_drawObject_setImage
        # Make the whole of "arg2" optional to support the strange "empty" function - if it's missing, parse action knows what to do
        self.grFunc_drawObject << (Literal("drawObject")("function") + SupLit("(") +
                                        Group(leVarOrWord)("arg1") +
                                        Optional( Suppress(Optional(Literal(","))) + self.grFunc_drawObject_SO("arg2") ) +
                                        SupLit(")") + LegacyElement(SupLit(")"), ELEMENT_OPTIONAL, ELEMENT_OMITTED))
        self.grFunc_getObjectState << Group(leVariable)("target") + SupLit("=") + Literal("getObjectState")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")        
        self.grFunc_matrixOp_setBoxFlags << Literal("setBoxFlags")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_matrixOp_setBoxScale << Literal("setBoxScale")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_matrixOp_SetBoxSlot << Literal("SetBoxSlot")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        self.grFunc_matrixOp_createBoxMatrix << Literal("createBoxMatrix")("function") + SupLit("(") + SupLit(")")
        self.grFunc_print_LeftHeight << Literal("Left")("function") + SupLit("(") + SupLit(")")
        
        # roomOps
        self.grFunc_roomOps_RoomScroll << Literal("RoomScroll")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        #self.grFunc_roomOps_RoomColor << Forward() # V5 does not support RoomColor
        self.grFunc_roomOps_SetScreen << Literal("SetScreen")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(",") + Group(leVarOrWord)("arg2") + SupLit(")")
        self.grFunc_roomOps_ShakeOn << Literal("ShakeOn")("function") + SupLit("(") + SupLit(")")
        self.grFunc_roomOps_ShakeOff << Literal("ShakeOff")("function") + SupLit("(") + SupLit(")")
        self.grFunc_roomOps_RoomIntensity << Literal("RoomIntensity")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(",") + Group(leVarOrByte)("arg3") + SupLit(")")
        self.grFunc_roomOps_saveLoad << (Literal("saveLoad?") ^ Literal("saveLoad"))("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        # screenEffect has a question mark and extra closing parenthesis
        self.grFunc_roomOps_screenEffect << (Literal("screenEffect?") ^ Literal("screenEffect"))("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_roomOps_colorCycleDelay << Literal("colorCycleDelay")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(",") + Group(leVarOrByte)("arg2") + SupLit(")")
        # Uses aux opcode, also extra closing parenthesis
        self.grFunc_roomOps_SetPalColor << (Literal("SetPalColor")("function") + SupLit("(") + 
                                                Group(leVarOrWord)("red") + SupLit(",") + 
                                                Group(leVarOrWord)("green") + SupLit(",") + 
                                                Group(leVarOrWord)("blue") + SupLit(",") + 
                                                Group(leVarOrByte)("index") +
                                                SupLit(")")
                                                )
        # Lots of parameters, descumm calls it "Unused" which (while possibly true) isn't very descriptive
        self.grFunc_roomOps_SetRoomScale << ((Literal("SetRoomScale") | Literal("Unused"))("function") + SupLit("(") + 
                                                    Group(leVarOrByte)("scale1") + SupLit(",") + 
                                                    Group(leVarOrByte)("y1") + SupLit(",") + 
                                                    Group(leVarOrByte)("scale2") + SupLit(",") + 
                                                    Group(leVarOrByte)("y2") + SupLit(",") + 
                                                    Group(leVarOrByte)("slot") + SupLit(",") + 
                                                    SupLit(")")
                                                    )
        # This has params and an aux opcode, but I'm also cheating and using this for setRoomShadow.
        self.grFunc_roomOps_setRGBRoomIntensity << ((Literal("setRGBRoomIntensity") | Literal("setRoomShadow"))("function") + SupLit("(") + 
                                                        Group(leVarOrWord)("redscale") + SupLit(",") + 
                                                        Group(leVarOrWord)("greenscale") + SupLit(",") + 
                                                        Group(leVarOrWord)("bluescale") + SupLit(",") + 
                                                        Group(leVarOrByte)("start") + SupLit(",") +
                                                        Group(leVarOrByte)("end") +
                                                        SupLit(")")
                                                        )
        # Share grammar & parse action for saveString and loadString
        self.grFunc_roomOps_saveLoadString << ((Literal("saveString") | Literal("loadString"))("function") + SupLit("(") + 
                                                    Group(leVarOrByte)("slot") + SupLit(",") + 
                                                    NamedElement(leString, "stringy") +
                                                    SupLit(")")
                                                    )
        # Lots of params & aux opcodes
        self.grFunc_roomOps_palManipulate << (Literal("palManipulate")("function") + SupLit("(") + 
                                                    Group(leVarOrByte)("slot") + SupLit(",") + 
                                                    Group(leVarOrByte)("start") + SupLit(",") + 
                                                    Group(leVarOrByte)("end") + SupLit(",") + 
                                                    Group(leVarOrByte)("time") +
                                                    SupLit(")"))
        
        self.grFunc_getAnimCounter << Group(leVariable)("target") + SupLit("=") + Literal("getAnimCounter")("function") + SupLit("(") + Group(leVarOrByte)("arg1") + SupLit(")")
        self.grFunc_getActorX << Group(leVariable)("target") + SupLit("=") + Literal("getActorX")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        self.grFunc_getActorY << Group(leVariable)("target") + SupLit("=") + Literal("getActorY")("function") + SupLit("(") + Group(leVarOrWord)("arg1") + SupLit(")")
        

        
class GrammarFactory(object):
    # SCUMM engine version
    grammars = { "3old": GrammarV3Old, # Indy 3 uses an "old" version of 3
                 "3": GrammarV3,
                 "4": GrammarV4,
                 "5": GrammarV5 }
    
    def __new__(cls, scummver, *args, **kwds):
        assert type(scummver) == str
        if not scummver in GrammarFactory.grammars:
            raise ScummblerException("Unsupported SCUMM version: " + str(scummver))
        return GrammarFactory.grammars[scummver](*args, **kwds)
    
    
def _unit_test():
    print "Starting scummbler_grammar.py unit test."
    scummgram = GrammarFactory("4")

    for g in scummgram:
        print str(g[0])
    
    print "Finished scummbler_grammar.py unit test."

    
if __name__ == '__main__':
    _unit_test()
