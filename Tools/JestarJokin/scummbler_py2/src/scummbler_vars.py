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

This file contains a list of known variable names. The list is taken from
ScummVM's descumm tool.
"""

varNames3list = [
	# /* 0 */
	"VAR_RESULT",
	"VAR_EGO",
	"VAR_CAMERA_POS_X",
	"VAR_HAVE_MSG",
	# /* 4 */
	"VAR_ROOM",
	"VAR_OVERRIDE",
	"VAR_MACHINE_SPEED",
	"VAR_ME",
	# /* 8 */
	"VAR_NUM_ACTOR",
	"VAR_CURRENT_LIGHTS",
	"VAR_CURRENTDRIVE",
	"VAR_TMR_1",
	# /* 12 */
	"VAR_TMR_2",
	"VAR_TMR_3",
	"VAR_MUSIC_TIMER",
	"VAR_ACTOR_RANGE_MIN",
	# /* 16 */
	"VAR_ACTOR_RANGE_MAX",
	"VAR_CAMERA_MIN_X",
	"VAR_CAMERA_MAX_X",
	"VAR_TIMER_NEXT",
	# /* 20 */
	"VAR_VIRT_MOUSE_X",
	"VAR_VIRT_MOUSE_Y",
	"VAR_ROOM_RESOURCE",
	"VAR_LAST_SOUND",
	# /* 24 */
	"VAR_CUTSCENEEXIT_KEY",
	"VAR_TALK_ACTOR",
	"VAR_CAMERA_FAST_X",
	"VAR_SENTENCE_OBJECT1", # V2
	# /* 28 */
	"VAR_ENTRY_SCRIPT",
	"VAR_ENTRY_SCRIPT2",
	"VAR_EXIT_SCRIPT",
	"VAR_EXIT_SCRIPT2",
	# /* 32 */
	"VAR_VERB_SCRIPT",
	"VAR_SENTENCE_SCRIPT",
	"VAR_INVENTORY_SCRIPT",
	"VAR_CUTSCENE_START_SCRIPT",
	# /* 36 */
	"VAR_CUTSCENE_END_SCRIPT",
	"VAR_CHARINC",
	"VAR_WALKTO_OBJ",
	"VAR_KEYPRESS", # V2
	# /* 40 */
	"VAR_CUTSCENEEXIT_KEY", # V2
	"VAR_TALK_ACTOR", # V2
	"VAR_RESTART_KEY",
	"VAR_PAUSE_KEY",
	# /* 44 */
	"VAR_MOUSE_X",
	"VAR_MOUSE_Y",
	"VAR_TIMER",
	"VAR_TMR_4",
	# /* 48 */
	"VAR_SOUNDCARD",
	"VAR_VIDEOMODE"
	#None, # NULL
	#None # NULL
]

varNames4list = [
	# /* 0 */
	"VAR_RESULT",
	"VAR_EGO",
	"VAR_CAMERA_POS_X",
	"VAR_HAVE_MSG",
	# /* 4 */
	"VAR_ROOM",
	"VAR_OVERRIDE",
	"VAR_MACHINE_SPEED",
	"VAR_ME",
	# /* 8 */
	"VAR_NUM_ACTOR",
	"VAR_CURRENT_LIGHTS",
	"VAR_CURRENTDRIVE",
	"VAR_TMR_1",
	# /* 12 */
	"VAR_TMR_2",
	"VAR_TMR_3",
	"VAR_MUSIC_TIMER",
	"VAR_ACTOR_RANGE_MIN",
	# /* 16 */
	"VAR_ACTOR_RANGE_MAX",
	"VAR_CAMERA_MIN_X",
	"VAR_CAMERA_MAX_X",
	"VAR_TIMER_NEXT",
	# /* 20 */
	"VAR_VIRT_MOUSE_X",
	"VAR_VIRT_MOUSE_Y",
	"VAR_ROOM_RESOURCE",
	"VAR_LAST_SOUND",
	# /* 24 */
	"VAR_CUTSCENEEXIT_KEY",
	"VAR_TALK_ACTOR",
	"VAR_CAMERA_FAST_X",
	"VAR_SCROLL_SCRIPT",
	# /* 28 */
	"VAR_ENTRY_SCRIPT",
	"VAR_ENTRY_SCRIPT2",
	"VAR_EXIT_SCRIPT",
	"VAR_EXIT_SCRIPT2",
	# /* 32 */
	"VAR_VERB_SCRIPT",
	"VAR_SENTENCE_SCRIPT",
	"VAR_INVENTORY_SCRIPT",
	"VAR_CUTSCENE_START_SCRIPT",
	# /* 36 */
	"VAR_CUTSCENE_END_SCRIPT",
	"VAR_CHARINC",
	"VAR_WALKTO_OBJ",
	"VAR_DEBUGMODE",
	# /* 40 */
	"VAR_HEAPSPACE",
	"VAR_TALK_ACTOR", # V2
	"VAR_RESTART_KEY",
	"VAR_PAUSE_KEY",
	# /* 44 */
	"VAR_MOUSE_X",
	"VAR_MOUSE_Y",
	"VAR_TIMER",
	"VAR_TMR_4",
	# /* 48 */
	"VAR_SOUNDCARD",
	"VAR_VIDEOMODE",
	"VAR_MAINMENU_KEY",
	"VAR_FIXEDDISK",
	# /* 52 */
	"VAR_CURSORSTATE",
	"VAR_USERPUT",
	"VAR_V5_TALK_STRING_Y",
	# /* Loom CD specific */
	None, # NULL
	# /* 56 */
	None, # NULL
	None, # NULL
	None, # NULL
	None, # NULL
	# /* 60 */
	"VAR_NOSUBTITLES",
	None, # NULL
	None, # NULL
	None, # NULL
	# /* 64 */
	"VAR_SOUNDPARAM",
	"VAR_SOUNDPARAM2",
	"VAR_SOUNDPARAM3",
	None # NULL
]

varNames5list = [
    # /* 0 */
    "VAR_RESULT",
    "VAR_EGO",
    "VAR_CAMERA_POS_X",
    "VAR_HAVE_MSG",
    # /* 4 */
    "VAR_ROOM",
    "VAR_OVERRIDE",
    "VAR_MACHINE_SPEED",
    "VAR_ME",
    # /* 8 */
    "VAR_NUM_ACTOR",
    "VAR_CURRENT_LIGHTS",
    "VAR_CURRENTDRIVE",
    "VAR_TMR_1",
    # /* 12 */
    "VAR_TMR_2",
    "VAR_TMR_3",
    "VAR_MUSIC_TIMER",
    "VAR_ACTOR_RANGE_MIN",
    # /* 16 */
    "VAR_ACTOR_RANGE_MAX",
    "VAR_CAMERA_MIN_X",
    "VAR_CAMERA_MAX_X",
    "VAR_TIMER_NEXT",
    # /* 20 */
    "VAR_VIRT_MOUSE_X",
    "VAR_VIRT_MOUSE_Y",
    "VAR_ROOM_RESOURCE",
    "VAR_LAST_SOUND",
    # /* 24 */
    "VAR_CUTSCENEEXIT_KEY",
    "VAR_TALK_ACTOR",
    "VAR_CAMERA_FAST_X",
    "VAR_SCROLL_SCRIPT",
    # /* 28 */
    "VAR_ENTRY_SCRIPT",
    "VAR_ENTRY_SCRIPT2",
    "VAR_EXIT_SCRIPT",
    "VAR_EXIT_SCRIPT2",
    # /* 32 */
    "VAR_VERB_SCRIPT",
    "VAR_SENTENCE_SCRIPT",
    "VAR_INVENTORY_SCRIPT",
    "VAR_CUTSCENE_START_SCRIPT",
    # /* 36 */
    "VAR_CUTSCENE_END_SCRIPT",
    "VAR_CHARINC",
    "VAR_WALKTO_OBJ",
    "VAR_DEBUGMODE",
    # /* 40 */
    "VAR_HEAPSPACE",
    "VAR_TALK_ACTOR", # V2
    "VAR_RESTART_KEY",
    "VAR_PAUSE_KEY",
    # /* 44 */
    "VAR_MOUSE_X",
    "VAR_MOUSE_Y",
    "VAR_TIMER",
    "VAR_TMR_4",
    # /* 48 */
    "VAR_SOUNDCARD",
    "VAR_VIDEOMODE",
    "VAR_MAINMENU_KEY",
    "VAR_FIXEDDISK",
    # /* 52 */
    "VAR_CURSORSTATE",
    "VAR_USERPUT",
    "VAR_V5_TALK_STRING_Y", # V4
    None, # NULL
    # /* 56 */
    "VAR_SOUNDRESULT",
    "VAR_TALKSTOP_KEY",
    None, # NULL
    "VAR_FADE_DELAY",
    # /* 60 */
    "VAR_NOSUBTITLES",
    None, # NULL
    None, # NULL
    None, # NULL
    # /* 64 */
    "VAR_SOUNDPARAM",
    "VAR_SOUNDPARAM2",
    "VAR_SOUNDPARAM3",
    "VAR_INPUTMODE",
    # /* 68 */
    "VAR_MEMORY_PERFORMANCE",
    "VAR_VIDEO_PERFORMANCE",
    "VAR_ROOM_FLAG",
    "VAR_GAME_LOADED",
    # /* 72 */
    "VAR_NEW_ROOM"
    #None, # NULL
    #None, # NULL
    #None, # NULL
    # /* 76 */
    #None, # NULL
    #None, # NULL
    #None, # NULL
    #None #NULL
]

varNames3map = {}
for i, vn3 in enumerate(varNames3list):
    if vn3 != None:
        varNames3map[vn3] = i

varNames4map = {}
for i, vn4 in enumerate(varNames4list):
    if vn4 != None:
        varNames4map[vn4] = i
        
varNames5map = {}
for i, vn5 in enumerate(varNames5list):
    if vn5 != None:
        varNames5map[vn5] = i
