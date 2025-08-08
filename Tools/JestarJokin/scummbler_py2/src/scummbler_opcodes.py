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

Differences in older engines:

v3, v4: actorOps - Scale(p8)
v3: cursorCommand - LoadCharset(p8, p8) is $0E
v3, v4: drawObject(p16, p16, p16), can be $25 (overrides pickupObject) but base is still $05 as normal.
indy3: waitForActor is $3B (overrides getActorScale)
indy3: getActorX and getActorY take p8
v3, v4: ifState is new, $0F (overrides getObjectState), ifNotState is new, $2F
v3: setBoxFlags(p8, b) is $30 (overrides matrixOps)
v3?, v4: oldRoomEffect-set and oldRoomEffect-fadein is new, $5C
v3, v4: pickupObject(p16) (old) is $50
v3: print and printEgo subop $06 is Height(p16)
LoomCD v4: print and printEgo adds subop $08 PlayCDTrack(p16, p16)
FM-Towns: ResourceRoutines adds some sub-ops
v3: roomOps stores arguments before sub-op
v3, v4: roomOps adds sub-op $02 ("RoomColor")
v3, v4: roomOps $04 SetPalColor only takes the two arguments
v3, v4: saveLoadGame is $22 (overrides getAnimCounter)
v3, v4: saveLoadVars is $A7 (overrides dummy)
small header: WaitForSentence is $4C (overrides soundKludge),
indy3: WaitForMessage is $AE (overrides wait with sub-ops)

"""

# Scummbler Opcodes
# Mappings of strings to their associated bytecode

opInlineOperation = {
    "+=" : 0x5A,
    "-=" : 0x3A,
    "/=" : 0x5B,
    "*=" : 0x1B,
    "&=" : 0x17,
    "|=" : 0x57,
    "="  : 0x1A,
    "++" : 0x46,
    "--" : 0xC6
}

# String function opcodes
opStringFunctionStart = 0xFF # this might be 0xFE in some SCUMM versions!
opStringFunctions = {
    "newline" : 0x01,
    "keepText" : 0x02,
    "wait" : 0x03,
    "getInt" : 0x04,
    "getVerb" : 0x05,
    "getName" : 0x06,
    "getString" : 0x07,
    "startAnim" : 0x09,
    "sound" : 0x0A,
    "setColor" : 0x0C,
    "setFont" : 0x0E
}

# Not sure what to do about expression mode
opExpressionOpcode = 0xAC
opExpressionValue = 0x01
opExpressionSubOpcode = 0x06
opExpressionEnd = 0xFF
opExpressionOperation = {
    "+" : 0x02,
    "-" : 0x03,
    "*" : 0x04,
    "/" : 0x05
}


# Logical comparisons
opComparisonsNoParameters = {
    "equalZero" : 0x28,
    "notEqualZero" : 0xA8
}


# Comparisons are swapped from the actual opcode meanings, because
#  the output of the variables is swapped.
opComparisons = {
    "==" : 0x48,
    "<" : 0x78,
    "<=" : 0x04,
    ">" : 0x44,
    ">=" : 0x38,
    "!=" : 0x08
}


opJump = 0x18

# actorOps conversion table looks like this in ScummVM
#{ 1, 0, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20 };
#opcode = (opcode & 0xE0) | convertTable[(opcode & 0x1F) - 1];

opFunctionTable = {
    "actorFollowCamera" : 0x52,
    "actorFromPos" : 0x15,
    "ActorOps" : 0x13,
     "AO_Unknown" : 0x00,
     "AO_Costume" : 0x01,
     "AO_WalkSpeed" : 0x04,
     "AO_Sound" : 0x05,
     "AO_WalkAnimNr" : 0x06,
     "AO_TalkAnimNr" : 0x07,
     "AO_StandAnimNr" : 0x08,
     "AO_Nothing" : 0x09,
     "AO_Init" : 0x0A,
     "AO_Elevation" : 0x0B,
     "AO_DefaultAnims" : 0x0C,
     "AO_Palette" : 0x0D,
     "AO_TalkColor" : 0x0E,
     "AO_Name" : 0x0F,
     "AO_InitAnimNr" : 0x10,
     # sub-op 0x11 (0x0F in V5) not used
     "AO_Width" : 0x12,
     "AO_Scale" : 0x13,
     #"AO_NeverZClip" : 0x012, # V5
     #"AO_SetZClip" : 0x13, # V5
     "AO_IgnoreBoxes" : 0x14,
     #"AO_FollowBoxes" : 0x15, # V5
     #"AO_AnimSpeed" : 0x16, # V5
     #"AO_ShadowMode" : 0x17, # V5
    
    "setClass" : 0x5d,
    "animateCostume" : 0x11,
    "breakHere" : 0x80,
    "chainScript" : 0x42,
    "cursorCommand" : 0x2c,
     "CursorShow" : 0x01,
     "CursorHide" : 0x02,
     "UserputOn" : 0x03,
     "UserputOff" : 0x04,
     "CursorSoftOn" : 0x05,
     "CursorSoftOff" : 0x06,
     "UserputSoftOn" : 0x07,
     "UserputSoftOff" : 0x08,
     "SetCursorImg" : 0x0A,
     "setCursorHotspot" : 0x0B,
     "InitCursor" : 0x0C,
     "InitCharset" : 0x0D,
     "CursorCommand" : 0x0E, # V4-5
         
    "classOfIs" : 0x1D, 
    "cutscene" : 0x40,
    "debug" : 0x6B,
    "debug?" : 0x6b,
    "delay" : 0x2E,
    "delayVariable" : 0x2b,
    "doSentence" : 0x19,
    "drawBox" : 0x3F,
    #"drawObject" : 0x25, # V3-4 <-- ? Why did I think that? It seems to be 0x05, as in SCUMM V5.
    "drawObject" : 0x05,
    "dummy(A7)" : 0xa7,
    "endCutscene" : 0xc0,
    "faceActor" : 0x9,
    "findInventory" : 0x3d,
    "findObject" : 0x35,
    "freezeScripts" : 0x60,
    "getActorCostume" : 0x71,
    "getActorElevation" : 0x6,
    "getActorFacing" : 0x63,
    "getActorMoving" : 0x56,
    "getActorRoom" : 0x3,
    "getActorScale" : 0x3b,
    "getActorWalkBox" : 0x7b,
    "getActorWidth" : 0x6c,
    "getActorX" : 0x43,
    "getActorY" : 0x23,
    "getAnimCounter" : 0x22, # V5
    "getClosestObjActor" : 0x66,
    "getDist" : 0x34,
    "getInventoryCount" : 0x31,
    "getObjectOwner" : 0x10,
    "getObjectState" : 0xf,
    "getRandomNr" : 0x16,
    "getStringWidth" : 0x67,
    "getVerbEntryPoint" : 0xb,
    "ifState" : 0x0F, # V3-4
    "ifNotState" : 0x2F, # V3-4
    "isActorInBox" : 0x1F,
    "isScriptRunning" : 0x68,
    "isSoundRunning" : 0x7c,
    "lights" : 0x70,
    "loadRoom" : 0x72,
    "loadRoomWithEgo" : 0x24,
    "matrixOp" : 0x30,
     "setBoxFlags" : 0x01,
     "setBoxScale" : 0x02,
     "SetBoxSlot" : 0x03,
     "createBoxMatrix" : 0x04,
     
    "oldRoomEffect" : 0x5C, # V3-4
     "oldRoomEffect-fadein" : 0x01, # I don't think this is right
     "oldRoomEffect-set" : 0x03, 
    "override" : 0x58,
     "beginOverride" : 0x01,
     "endOverride" : 0x00,
    "panCameraTo" : 0x12,
    "pickupObject" : 0x50, # V3-4
    "print" : 0x14,
     "PO_Pos" : 0x00,
     "PO_Color" : 0x01,
     "PO_Clipped" : 0x02,
     "PO_RestoreBG" : 0x03,
     "PO_Center" : 0x04,
     "PO_Left" : 0x06, # V4-5
     "PO_Overhead" : 0x07,
     "PO_PlayCDTrack" : 0x08, # LOOM CD only
     "PO_Text" : 0x0F,
    "printEgo" : 0xD8,
    "PseudoRoom" : 0xCC,
    "putActor" : 0x01,
    "putActorAtObject" : 0x0E,
    "putActorInRoom" : 0x2D,
    "Resource" : 0x0C,
     "Resource.loadScript" : 0x01,
     "Resource.loadSound" : 0x02,
     "Resource.loadCostume" : 0x03,
     "Resource.loadRoom" : 0x04,
     
     "Resource.nukeScript" : 0x05,
     "Resource.nukeSound" : 0x06,
     "Resource.nukeCostume" : 0x07,
     "Resource.nukeRoom" : 0x08,
     
     "Resource.lockScript" : 0x09,
     "Resource.lockSound" : 0x0A,
     "Resource.lockCostume" : 0x0B,
     "Resource.lockRoom" : 0x0C,
     
     "Resource.unlockScript" : 0x0D,
     "Resource.unlockSound" : 0x0E,
     "Resource.unlockCostume" : 0x0F,
     "Resource.unlockRoom" : 0x10,
     
     "Resource.clearHeap" : 0x11,
     "Resource.loadCharset" : 0x12,
     "Resource.nukeCharset" : 0x13,
     "Resource.loadFlObject" : 0x14,
     
    "roomOps" : 0x33,
     "RoomScroll" : 0x01,
     "RoomColor" : 0x02, # not supported in V5
     "SetScreen" : 0x03,
     "SetPalColor" : 0x04,
     "ShakeOn" : 0x05,
     "ShakeOff" : 0x06,
     # The rest are V5 only
    
    "saveLoadGame" : 0x22, # V3-4
    "saveLoadVars" : 0xA7, # V3-4
     "SLV_VarRange" : 0x01,
     "SLV_StringRange" : 0x02,
     "SLV_Open" : 0x03,
     "SLV_Append" : 0x04,
     "SLV_Close" : 0x1F,
     "SLV_Load" : 0x00,
     "SLV_Save" : 0x01,
     
    "saveRestoreVerbs" : 0xAB,
     "saveVerbs" : 0x01,
     "restoreVerbs" : 0x02,
     "deleteVerbs" : 0x03,
     
    "setCameraAt" : 0x32,
    "setObjectName" : 0x54,
    "setOwnerOf" : 0x29,
    "setState" : 0x07,
    "setVarRange" : 0x26,
    "soundKludge" : 0x4C, # V4-5?
    "startMusic" : 0x02,
    "startObject" : 0x37,
    "startSound" : 0x1C,
    "startScript" : 0x0A,
    "stopMusic" : 0x20,
    "stopObjectCode" : 0xA0,
    "stopObjectCode-alt" : 0x00, # this only seems to be used in objects...?
    "stopObjectScript" : 0x6E,
    "stopScript" : 0x62,
    "stopSound" : 0x3C,
    "stringOps" : 0x27,
     "PutCodeInString" : 0x01,
     "CopyString" : 0x02,
     "SetStringChar" : 0x03,
     "GetStringChar" : 0x04,
     "CreateString" : 0x05,
    
    "systemOps" : 0x98,
    "VerbOps" : 0x7a,
     "VO_Image" : 0x01,
     "VO_Text" : 0x02,
     "VO_Color" : 0x03,
     "VO_HiColor" : 0x04,
     "VO_SetXY" : 0x05,
     "VO_On" : 0x06,
     "VO_Off" : 0x07,
     "VO_Delete" : 0x08,
     "VO_New" : 0x09,
     "VO_DimColor" : 0x10,
     "VO_Dim" : 0x11,
     "VO_Key" : 0x12,
     "VO_Center" : 0x13,
     "VO_SetToString" : 0x14,
     "VO_SetToObject" : 0x16,
     "VO_BackColor" : 0x17,
    
    "wait" : 0xAE,
     "WaitForActor" : 0x01,
     "WaitForMessage" : 0x02,
     "WaitForCamera" : 0x03,
     "WaitForSentence" : 0x04,
    
    "walkActorTo" : 0x1E,
    "walkActorToActor" : 0x0D,
    "walkActorToObject" : 0x36,
    }


opFunctionTableV3Old = {
     "WaitForActor" : 0x3B,
     "WaitForMessage" : 0xAE,
    }

opFunctionTableV3 = {
    "LoadCharset" : 0x0E,
    "setBoxFlags" : 0x30,
    "PO_Height" : 0x06,
    "WaitForSentence" : 0x4C,
    }

opFunctionTableV5 = {
     "AO_Unknown" : 0x00,
     "AO_Costume" : 0x01,
     "AO_WalkSpeed" : 0x02,
     "AO_Sound" : 0x03,
     "AO_WalkAnimNr" : 0x04,
     "AO_TalkAnimNr" : 0x05,
     "AO_StandAnimNr" : 0x06,
     "AO_Nothing" : 0x07,
     "AO_Init" : 0x08,
     "AO_Elevation" : 0x09,
     "AO_DefaultAnims" : 0x0A,
     "AO_Palette" : 0x0B,
     "AO_TalkColor" : 0x0C,
     "AO_Name" : 0x0D,
     "AO_InitAnimNr" : 0x0E,
     # sub-op 0x11 (0x0F in V5) not used
     "AO_Width" : 0x10,
     "AO_Scale" : 0x11,
     "AO_NeverZClip" : 0x012,
     "AO_SetZClip" : 0x13,
     "AO_IgnoreBoxes" : 0x14,
     "AO_FollowBoxes" : 0x15,
     "AO_AnimSpeed" : 0x16,
     "AO_ShadowMode" : 0x17,
    
    "pickupObject" : 0x25,
    "drawObject" : 0x05,
     "setXY" : 0x01,
     "setImage" : 0x02,
     "drawObject()" : 0xFF,
     
    # roomOps sub-opcodes that are V5 specific
     "Unused" : 0x07, # hrm
     "SetRoomScale" : 0x07,
     "RoomIntensity" : 0x08,
     "saveLoad" : 0x09,
     "saveLoad?" : 0x09,
     "screenEffect" : 0x0A,
     "screenEffect?" : 0x0A,
     "setRGBRoomIntensity" : 0x0B,
     "setRoomShadow" : 0x0C,
     "saveString" : 0x0D,
     "loadString" : 0x0E,
     "palManipulate" : 0x0F,
     "colorCycleDelay" : 0x10,
    }

#opFunctionsV3 = {
    #"LoadCharset" : 0x0E, # cursorCommand sub-op, 2x p8 args
    #}



# The below was used to generate some code, but has rotted.
opAutogenTable = [
    # Format:
    # name : ( opcode, descumm equiv, varstore, arg1, arg2, arg3 )
    # varstore indicates if the function returns a value to be stored in a var
    #Argument types:
    #* V = variable
    #* B = byte constant
    #* W = word constant
    #* P8 = variable or byte
    #* P16 = variable or word
    #* L = list
    #* J = jump (used by almost all boolean expressions, comparisons) (equivalent to W)
    #* D = delay; 24-bit constant (only used by delay instruction, strangely enough)
    #* A = ASCII string, without any terminating character
    #* A0 = ASCII string, null-terminated
    #* A1 = ASCII string, $FF terminated
    #* FF = the hex value $FF, used for terminating some lists, strings etc.
    #* SO = sub-opcode, variants listed underneath as "opcode$sub-opcode"
    #* NS = non-standard encoding that cannot be sufficiently expressed in this table
    #* + = one or more of the preceding argument (parameter bits usually don't matter)
    #* None = does not take that argument argument
    #* a Python tuple = nested sub-opcode
    ( 0x52, "actorFollowCamera", False, "P8", None, None ),
    ( 0x15, "actorFromPos", True, "P16", "P16", None ),
    ( 0x13, "ActorOps", False, "P8",
        (
            ( True, False ), # can have multiple values, omits root function name
            ( 0x00, "Unknown", False, "P8", None, None ),
            ( 0x01, "Costume", False, "P8", None, None ),
            ( 0x02, "WalkSpeed", False, "P8", "P8", None ),
            ( 0x03, "Sound", False, "P8", None, None ),
            ( 0x04, "WalkAnimNr", False, "P8", None, None ),
            ( 0x05, "TalkAnimNr", False, "P8", "P8", None ),
            ( 0x06, "StandAnimNr", False, "P8", None, None ),
            ( 0x07, "Nothing", False, "P8", "P8", "P8" ),
            ( 0x08, "Init", False, None, None, None ),
            ( 0x09, "Elevation", False, "P16", None, None ),
            ( 0x0A, "DefaultAnims", False, None, None, None ),
            ( 0x0B, "Palette", False, "P8", "P8", None ),
            ( 0x0C, "TalkColor", False, "P8", None, None ),
            ( 0x0D, "Name", False, "A0", None, None ),
            ( 0x0E, "InitAnimNr", False, "P8", None, None ),
            ( 0x10, "Width", False, "P8", None, None ),
            ( 0x11, "Scale", False, "P8", "P8", None ),
            ( 0x12, "NeverZClip", False, None, None, None ),
            ( 0x13, "SetZClip", False, "P8", None, None ),
            ( 0x14, "IgnoreBoxes", False, None, None, None ),
            ( 0x15, "FollowBoxes", False, None, None, None ),
            ( 0x16, "AnimSpeed", False, "P8", None, None ),
            ( 0x17, "ShadowMode", False, "P8", None, None )
        ),
        "FF" ),
    ( 0x5D, "setClass", False, "P16", "L", None ),
    ( 0x11, "animateCostume", False, "P8", "P8", None ),
    ( 0x80, "breakHere", False, None, None, None ),
    ( 0x42, "chainScript", False, "P8", "L", None ),
    ( 0x2C, "cursorCommand", False,
        (
            ( False, True ), # can have multiple values, omits root function name
            ( 0x01, "CursorShow", False, None, None, None ),
            ( 0x02, "CursorHide", False, None, None, None ),
            ( 0x03, "UserputOn", False, None, None, None ),
            ( 0x04, "UserputOff", False, None, None, None ),
            ( 0x05, "CursorSoftOn", False, None, None, None ),
            ( 0x06, "CursorSoftOff", False, None, None, None ),
            ( 0x07, "UserputSoftOn", False, None, None, None ),
            ( 0x08, "UserputSoftOff", False, None, None, None ),
            ( 0x0A, "SetCursorImg", False, "P8", "P8", None ),
            ( 0x0B, "setCursorHotspot", False, "P8", "P8", "P8" ),
            ( 0x0C, "InitCursor", False, "P8", None, None ),
            ( 0x0D, "InitCharset", False, "P8", None, None ),
            ( 0x0E, "CursorCommand", False, "L", None, None )
        ),
        None, None ),
    ( 0x40, "cutscene", False, "L", None, None),
    ( 0x6B, "debug?", False, "P16", None, None ),
    #( 0x2E, "delay", False, "D", None, None ), # doesn't used do_tok. "delay(%d)"
    ( 0x2B, "delayVariable", False, "V", None, None ),
    #( 0x19, "doSentence", False, "P8", "P16", "P16" ),
    #( 0x3F, "drawBox", False, "P16", "P16", "NS"),
    #( 0x05, "drawObject", False, "P16", # This is auto-generated except for sub-opcode 0x1F.
    #    (
    #        ( False, False ), # can have multiple values, omits root function name
    #        ( 0x01, "setXY", False, "P16", "P16", None ),
    #        ( 0x02, "setImage", False, "P16", None, None ),
    #        ( 0x1F, "", False, None, None, None ) # descumm has incorrect output and adds extra ")"
    #    ),
    #    None ),
    ( 0xA7, "dummy(A7)", False, None, None, None ), # 0xA7
    ( 0xC0, "endCutscene", False, None, None, None ),
    ( 0x09, "faceActor", False, "P8", "P16", None ),
    ( 0x3D, "findInventory", True, "P8", "P8", None ),
    ( 0x35, "findObject", True, "P8", "P8", None ), # Interesting, descumm thinks these are words, but ScummVM looks for bytes.
    ( 0x60, "freezeScripts", False, "P8", None, None ),
    ( 0x71, "getActorCostume", True, "P8", None, None ),
    ( 0x06, "getActorElevation", True, "P8", None, None ),
    ( 0x63, "getActorFacing", True, "P8", None, None ),
    ( 0x56, "getActorMoving", True, "P8", None, None ),
    ( 0x03, "getActorRoom", True, "P8", None, None ),
    ( 0x3B, "getActorScale", True, "P8", None, None ),
    ( 0x7B, "getActorWalkBox",True, "P8", None, None ),
    ( 0x6C, "getActorWidth", True, "P8", None, None ),
    ( 0x43, "getActorX", True, "P16", None, None ),
    ( 0x23, "getActorY", True, "P16", None, None ),
    ( 0x22, "getAnimCounter", True, "P8", None, None ),
    ( 0x66, "getClosestObjActor", True, "P16", None, None ),
    ( 0x34, "getDist", True, "P16", "P16", None ),
    ( 0x31, "getInventoryCount", True, "P8", None, None ),
    ( 0x10, "getObjectOwner", True, "P16", None, None ),
    ( 0x0F, "getObjectState", True, "P16", None, None ),
    ( 0x16, "getRandomNr", True, "P8", None, None ),
    ( 0x67, "getStringWidth", True, "P8", None, None ),
    ( 0x0B, "getVerbEntryPoint", True, "P16", "P16", None ),
    #( 0x1D, "classOfIs", False, "P16", "L", "J" ),
    #"ifNotState" :         ( 0x2F, "getState (inline)", False, "P16", "P8", "J" ), 
    #"ifState" :            ( 0x4F, "getState (inline)", False, "P16", "P8", "J" ), 
    #( 0x1F, "isActorInBox", False, "P8", "P8", "J" ),
    ( 0x68, "isScriptRunning", True, "P8", None, None ),
    ( 0x7C, "isSoundRunning", True, "P8", None, None ),
    ( 0x70, "lights", False, "P8", "B", "B" ),
    ( 0x72, "loadRoom", False, "P8", None, None ),
    #( 0x24, "loadRoomWithEgo", False, "P16", "P8", "NS" ),
    ( 0x30, "matrixOp", False,
        (
            ( False, True ), # can have multiple values, omits root function name
            ( 0x01, "setBoxFlags", False, "P8", "P8", None ),
            ( 0x02, "setBoxScale", False, "P8", "P8", None ),
            ( 0x03, "SetBoxSlot", False, "P8", "P8", None ),
            ( 0x04, "createBoxMatrix", False, None, None, None )
        ),
        None, None ),

    #"oldRoomEffect" :      ( 0x5C, "oldRoomEffect-fadein", False, "SO", None, None ), # not quite right
    #"oldRoomEffect$03" :   ( 0x03, "oldRoomEffect-set", False, "P16", None, None ), # not quite right
    #"oldRoomEffect-fadein" : ( False, "P16", None, None ), # // dodgy? #descumm
    #"oldRoomEffect-set" :  ( False, "P16", None, None ), # // dodgy? #descumm
    #( 0x58, "override", False,
        #(
            #( False, True ), # can have multiple values, omits root function name
            #( 0x00, "endOverride", False, None, None, None ),
            #( 0x01, "beginOverride", False, None, None, None )
        #),
        #None, None ),
    ( 0x12, "panCameraTo", False, "P16", None, None ),
    #( 0x25, "pickupObject", False, "P16", "P8", None ), # v5 specific, shares opcode with something else
    #( 0x50, "pickupObject", False, "P16", None, None ), # "pickupObjectOld"
    # print and printEgo have auto-generated parse actions, but these are overriden,
    # so we can terminate with 0xFF only when the last sub-opcode is not 0x0f ("Text")
    ( 0x14, "print", False, "P8",
        (
            ( True, False ), # can have multiple values, omits root function name
            ( 0x00, "Pos", False, "P16", "P16", None ),
            ( 0x01, "Color", False, "P8", None, None ),
            ( 0x02, "Clipped", False, "P16", None, None ),
            ( 0x03, "RestoreBG", False, "P16", "P16", None),
            ( 0x04, "Center", False, None, None, None ),
            ( 0x06, "Left", False, None, None, None ),
            ( 0x07, "Overhead", False, None, None, None ),
            ( 0x08, "PlayCDTrack", False, "P16", "P16", None ),
            ( 0x0F, "Text", False, "A0", None, None )
        ), "FF" ),
    #( 0xD8, "printEgo", False, # removed because we can re-use the sub-ops for "print"
    #    (
    #        ( True, False ), # can have multiple values, omits root function name
    #        ( 0x00, "Pos", False, "P16", "P16", None ),
    #        ( 0x01, "Color", False, "P8", None, None ),
    #        ( 0x02, "Clipped", False, "P16", None, None ),
    #        ( 0x03, "RestoreBG", False, "P16", "P16", None),
    #        ( 0x04, "Center", False, None, None, None ),
    #        ( 0x06, "Left", False, None, None, None ),
    #        ( 0x07, "Overhead", False, None, None, None ),
    #        ( 0x08, "PlayCDTrack", False, "P16", "P16", None ),
    #        ( 0x0F, "Text", False, "A", None, None )
    #    ), "FF", None ),
#    "pseudoRoom" :         ( 0xCC, "PsuedoRoom", False, "B", "NS", "NS"),  # requires better grammar 
    ( 0x01, "putActor", False, "P8", "P16", "P16" ),
    ( 0x0E, "putActorAtObject", False, "P8", "P16", None ),
    ( 0x2D, "putActorInRoom", False, "P8", "P8", None ),
    ( 0x0C, "Resource", False, # Annoying, descumm uses "." instead of "()" for this.
        (
            ( False, True ), # can have multiple values, omits root function name
            ( 0x01, "Resource.loadScript", False, "P8", None, None ),
            ( 0x02, "Resource.loadSound", False, "P8", None, None ),
            ( 0x03, "Resource.loadCostume", False, "P8", None, None ),
            ( 0x04, "Resource.loadRoom", False, "P8", None, None ),
            
            ( 0x05, "Resource.nukeScript", False, "P8", None, None ),
            ( 0x06, "Resource.nukeSound", False, "P8", None, None ),
            ( 0x07, "Resource.nukeCostume", False, "P8", None, None ),
            ( 0x08, "Resource.nukeRoom", False, "P8", None, None ),
            
            ( 0x09, "Resource.lockScript", False, "P8", None, None ),
            ( 0x0A, "Resource.lockSound", False, "P8", None, None ),
            ( 0x0B, "Resource.lockCostume", False, "P8", None, None ),
            ( 0x0C, "Resource.lockRoom", False, "P8", None, None ),
            
            ( 0x0D, "Resource.unlockScript", False, "P8", None, None ),
            ( 0x0E, "Resource.unlockSound", False, "P8", None, None ),
            ( 0x0F, "Resource.unlockCostume", False, "P8", None, None ),
            ( 0x10, "Resource.unlockRoom", False, "P8", None, None ),
            
            ( 0x11, "Resource.clearHeap", False, None, None, None ),
            ( 0x12, "Resource.loadCharset", False, "P8", None, None ),
            ( 0x13, "Resource.nukeCharset", False, "P8", None, None ),
            ( 0x14, "Resource.loadFlObject", False, "P8", "P16", None )
        ),
        None, None ),  # descumm supports the FM-Towns sub-ops in the form of "resUnk1... resUnk3"

    #( 0x33, "roomOps", False,
        #(
            #( False, True ), # can have multiple values, omits root function name
            #( 0x01, "RoomScroll", False, "P16", "P16", None ),
            ## 0x02 not supported in V5
            #( 0x03, "SetScreen", False, "P16", "P16", None ),
            ##( 0x04, "SetPalColor", False, "P16", "P16", "NS" ),
            #( 0x05, "ShakeOn", False, None, None, None ),
            #( 0x06, "ShakeOff", False, None, None, None ),
            ##( 0x07, "Unused", False, "P8", "P8", "NS" ),
            #( 0x08, "RoomIntensity", False, "P8", "P8", "P8" ),
            #( 0x09, "saveLoad?", False, "P8", "P8", None ),
            #( 0x0A, "screenEffect?", False, "P16", None, None ),
            ##( 0x0B, "setRGBRoomIntensity", False, "P16", "P16", "NS" ),
            ##( 0x0C, "setRoomShadow", False, "P16", "P16", "NS" ),
            ##( 0x0D, "saveString", False, "P8", "NS", "NS" ),
            ##( 0x0E, "loadString", False, "P8", "NS", "NS" ),
            ##( 0x0F, "palManipulate", False, "P8", "NS", "NS" ),
            #( 0x10, "colorCycleDelay", False, "P8", "P8", None )
        #),
        #None, None ),

    # saveRestoreVerbs could actually be autogenerated, but I already did the
    # work and entered it manually.
    #( 0xAB, "saveRestoreVerbs", False,
    #    (
    #        ( False, True ), # can have multiple values, omits root function name
    #        ( 0x01, "saveVerbs", False, "P8", "P8", "P8" ),
    #        ( 0x02, "restoreVerbs", False, "P8", "P8", "P8" ),
    #        ( 0x03, "deleteVerbs", False, "P8", "P8", "P8" ),
    #    ),
    #    None, None ),
    
    ( 0x32, "setCameraAt", False, "P16", None, None ),
    ( 0x54, "setObjectName", False, "P16", "A0", None ),
    ( 0x29, "setOwnerOf", False, "P16", "P8", None ),
    ( 0x07, "setState", False, "P16", "P8", None ),
    #( 0x26, "setVarRange", False, "B", "NS", "NS" ),
    ( 0x4C, "soundKludge", False, "L", None, None ),
    ( 0x02, "startMusic", False, "P8", None, None ),
    ( 0x37, "startObject", False, "P16", "P8", "L" ),
    #( 0x0A, "startScript",  False, "P8", "L", None ),
    ( 0x1C, "startSound", False, "P8", None, None ),
    ( 0x20, "stopMusic", False, None, None, None ),
    #( 0xA0, "stopObjectCode", False, None, None, None ),
    ( 0x6E, "stopObjectScript", False, "P16", None, None ),
    ( 0x62, "stopScript", False, "P8", None, None ),
    ( 0x3C, "stopSound", False, "P8", None, None ),
    ( 0x27, "stringOps", False,
        (
            ( False, True ), # can have multiple values, omits root function name
            ( 0x01, "PutCodeInString", False, "P8", "A0", None ),
            ( 0x02, "CopyString", False, "P8", "P8", None ),
            ( 0x03, "SetStringChar", False, "P8", "P8", "P8" ),
            ( 0x04, "GetStringChar", True, "P8", "P8", None ),
            ( 0x05, "CreateString", False, "P8", "P8", None )
        ),
        None, None ),
    
    # systemOps will require custom grammar
    #"systemOps" :          ( 0x98, "systemOps", False, "SO", None, None ), # not sure bout this, might describe sub-opcodes
    #"systemOps$01" :       ( 0x01, "N/A", False, None, None, None ),
    #"systemOps$02" :       ( 0x02, "N/A", False, None, None, None ),
    #"systemOps$03" :       ( 0x03, "N/A", False, None, None, None ),
    
    ( 0x7A, "VerbOps", False, "P8",
        (
            ( True, False ),  # can have multiple values, omits root function name
            ( 0x01, "Image", False, "P16", None, None ),
            ( 0x02, "Text", False, "A0", None, None ),
            ( 0x03, "Color", False, "P8", None, None ),
            ( 0x04, "HiColor", False, "P8", None, None ),
            ( 0x05, "SetXY", False, "P16", "P16", None ),
            ( 0x06, "On", False, None, None, None ),
            ( 0x07, "Off", False, None, None, None ),
            ( 0x08, "Delete", False, None, None, None ),
            ( 0x09, "New", False, None, None, None ),
            ( 0x10, "DimColor", False, "P8", None, None ),
            ( 0x11, "Dim", False, None, None, None ),
            ( 0x12, "Key", False, "P8", None, None ),
            ( 0x13, "Center", False, None, None, None ),
            ( 0x14, "SetToString", False, "P16", None, None ),
            ( 0x16, "SetToObject", False, "P16", "P8", None ),
            ( 0x17, "BackColor", False, "P8", None, None )
        ),
        "FF" ), 

    ( 0xAE, "wait", False, 
        (
            ( False, True ), # can have multiple values, omits root function name
            ( 0x01, "WaitForActor", False, "P8", None, None ),
            ( 0x02, "WaitForMessage", False, None, None, None ),
            ( 0x03, "WaitForCamera", False, None, None, None ),
            ( 0x04, "WaitForSentence", False, None, None, None ),
        ),
        None, None ), 
    ( 0x1E, "walkActorTo", False, "P8", "P16", "P16" ),
    ( 0x0D, "walkActorToActor", False, "P8", "P8", "B" ),
    ( 0x36, "walkActorToObject", False, "P8", "P16", None )
    
]

# Quirky instructions that can't be auto-generated
# - classOfIs (jump; all jump instructions are defined manually)
# - delay (has its own unique type of argument)
# - doSentence (takes 3 params, except when it doesn't and only takes 0xFE (descumm outputs "STOP"))
# - drawBox (has aux opcode, extra params)
# - drawObject ("empty" sub-opcode, extra closing parenthesis)
# - ifState (jump; inline)
# - ifNotState (jump; inline)
# - isActorInBox (jump: all jump instructions are defined manually)
# - loadRoomWithEgo (has two params, followed by two constants)
# - oldRoomEffect (can either fadein or set effect, strange subopcode)
# - override (descumm omits the parentheses)
# - pickupObject (can be one of two opcodes; only applicable for supporting SCUMM < 5)
# - print (terminates with 0xFF only if no Text (0x0F) sub-op)
# - printEgo (so we can re-use the sub-opcodes for "print", same terminating as print)
# - pseudoRoom (one const, variable num of consts ORed with 0x80, terminated with 0)
# - roomOps (lots of non-standard encoding in sub-ops)
# - saveRestoreVerbs (I already implemented this manually, but it could be auto-generated)
# - setVarRange (takes a variable number of either byte or word constants, not mixed)
# - startScript (has extra flags in the opcode, descumm does not specifically output them)
# - stopObjectCode (must be the last item in a script)
# - systemOps (single "sub-opcode" argument, descumm outputs it as a number argument)