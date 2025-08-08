import os.path
import sys

from pyparsing import ParseException

import scummbler_compiler
import scummbler_compiler_helper
from scummbler_misc import ScummblerException


def __run_tests():
    SCUMM_version = "5" # only used in testing
    
    testlist = [
"Local[0] += 7", # Test 01: addition
"Var[166 + Var[165]] = Var[310 + Local[0]]", # Test 02: indirect
"Local[15] = Var[64 + 22]", # Test 03: indirect
"""Bit[22]--
Var[230]++;
Var[3 + Local[11]] &= Var[4 + Var[24]]""", # Test 04: inc, dec, indirect anding
"""[002B] (5A) Var[229] += 8;
[00A9] Var[229] += 8
(5A) Var[229] += Var[230];""", # Test 05: labels, descummed crud
"""Var[256] /= Bit[254] /* comment 1 */
/* This line is a comment */
[005D] /* Var[155]++
[006F] Local[2] -= Var[155]*/""", # Test 06: comments
"Local[2] = Gibberish", # Test 07: expected parse failure
"Exprmode Local[2] = (Var[238] + 6);", # Test 08: expression mode
"Exprmode Var[100] = ((120 + Var[165]) - 1);", # Test 09: expression mode (nested subexpression)
"""
goto 006F;
/* FLARGH */

[00A9] Var[229] += 8
[006F] Local[2] -= Var[155]

goto 00A9;
goto infloop;
[infloop] goto infloop

""", # Test 10: empty lines, jumps
"""[0013] (C4) if (Local[2] > Var[308]) {
Local[2] += 8
}
[afterif] /* hi there */
Local[0]++
goto afterif""", # Test 11: if statement
"""[0013] if (Local[2] > Var[308]) {
Local[2] += 8;
} else if (Local[2] > Var[308]) {
Local[3] += 4;
} else {
Local[7] += 5
}

[infloop] goto infloop""", # Test 12: if/else statement
"""
[0013] (C4) if (Local[2] > Var[308]) {
[001A] (AC)   Exprmode Var[238] = (Var[308] - 6);
[0025] (78)   if (Var[238] < 0) {
[002C] (1A)     Var[238] = 0;
[0031] (**)   }
[0031] (**) }
""", # Test 13: real if/else example. Nested if statements.
"""
[monkey] Var[238] = 0;
if (Local[7]) {
    unless (!Var[238]) goto monkey;
}
Var[238] = 1
""", # Test 14: equality to zero tests, "unless" statement.
"""
breakHere();
Var[240] = actorFromPos(-8,8);
walkActorTo(Var[1],179,44);
setObjectName(124,"bucket o' mud");
cutscene([2]);
chainScript(3,[Local[0],Local[1]]);
setClass(346, [1,2,3,4,Var[5]]);
startScript(11,[]);
""", # Test 15: functions, auto-generated grammar, a negative number (wrong usage), varargs
"""
ActorOps(11,[TalkAnimNr(4,5)]);
ActorOps(8,[Init(),Costume(21),IgnoreBoxes(),SetZClip(1)]);
ActorOps(Var[1],[Init(),Costume(1),TalkColor(15),Name("Guybrush")]);
ActorOps(8,[Init(),Costume(28),IgnoreBoxes(),NeverZClip(),WalkAnimNr(7),StandAnimNr(7),InitAnimNr(7),WalkSpeed(15,15)]);
ActorOps(Var[1],[TalkColor(Var[485])]);
""", # Test 16: functions with sub-opcodes (multival, emit root)
"""
CursorShow()
SetCursorImg(24,25)
CursorCommand([6,7,8,9])
createBoxMatrix()
""", # Test 17: functions with sub-opcodes (non-multival, omit root), varargs
"""
printEgo([Text("What's that?")]);
print(252,[Color(12),Text("Are you sure you want to win? (Y/N)")]);
printEgo([Text("Nice ^255^6^1@.")]);
print(6,[Text("Well, you'd better have more tomorrow^")]);
""", # Test 18: functions with sub-opcodes (print), quirky function, escape codes & "..." karats.
"""
delay(127000);
drawBox(10,20,60,80,72);
drawBox(Var[10],Var[20],Var[60],Var[80],Var[72]);
drawObject(16,setXY(12,14));
drawObject(16);
loadRoomWithEgo(43,7,696,49);
pickupObject(1058,97);
pickupObject(1058);
setVarRange(Var[178],9,[0,0,0,0,0,0,0,0,0]);
setVarRange(Var[178],[0,0,0,0,0,0,0,0,0]);
setVarRange(Var[178],9,[256,0,257,0,258,0,259,0,260]);
restoreVerbs(200,209,1);
systemOps(3);
PseudoRoom(98,12,16,18,23);
""", # Test 19: quirky functions
"""
Script# 201
[0000] (2C) CursorHide();
[0002] (2C) UserputOff();
[0004] (1A) VAR_VERB_SCRIPT = 14;
[0009] (0A) startScript(16,[5]);
""", # Test 20: defining preprocessor info
"""
Script# 201
[0000] (A8) if (Bit[321]) {
[0005] (11)   animateCostume(8,250)
[0008] (13)   ActorOps(8,[Init(),Costume(21),IgnoreBoxes(),SetZClip(1)]);
[0011] (2D)   putActorInRoom(8,2)
[0014] (01)   putActor(8,198,30)
[001A] (5D)   setClass(20,[32])
[0021] (18) } else {
[0024] (2D)   putActorInRoom(8,0)
[0027] (5D)   setClass(20,[160])
[002E] (**) }
[002E] (A0) stopObjectCode()
END
""", # Test 21: This is an entire (small) script!
"""
[058D] (28)     if (!Bit[5 + Var[1]]) {
[059B] (19)         doSentence(STOP)
[05AD] (**)     }
""", # Test 22: Indirect Bit variable
"""
[0000] (48) if (Local[1] == 1) {
[0007] (14)   print(255,[Text(" ")]);
[000C] (60)   freezeScripts(127)
[000E] (33)   saveLoad?(1,26)
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
[003D] (33)   saveLoad?(2,26)
[0041] (80)   breakHere()
[0042] (**) }
[0042] (A0) stopObjectCode()
""", # Test 23: example section
"""
while (Var[109] <= 40) {
 CursorHide()
}
""", # Test 24: while loop
"""
for ( Var[109] = 0 ; Var[109] <= 40 ; Var[109] += 1 ) {
 CursorHide()
}
""", # Test 25: for loop
"""
[004A] (AC) Exprmode Var[100] = <VAR_RESULT = getObjectState(379)>;
""", # Test 26: expression mode with single instructions
#"""
#ActorOps(46, [Scale(8)])
#""", # Test 27: different SCUMM versions... not sure how to test this.
"""
printEgo([Text(wait() + "What's" + wait() + "that?" + wait())]);
printEgo([Text("newline" + newline())]);
printEgo([Text("keepText" + keepText())]);
printEgo([Text("getInt" + getInt(Var[10]))]);
printEgo([Text("getVerb" + getVerb(Var[10]))]);
printEgo([Text("getName" + getName(Var[10]))]);
printEgo([Text("getString" + getString(Var[10]))]);
printEgo([Text("startAnim" + startAnim(10))]);
printEgo([Text("sound" + sound(10, 20))]);
printEgo([Text("sound" + sound(0x10, 0x20))]);
printEgo([Text("setColor" + setColor(10))]);
printEgo([Text("setFont" + setColor(10))]);
""" # Test 27: test string functions
]

    knownfailures = frozenset(["07"]) # These tests are supposed to fail

    failedtests = [] # keep track of test that have failed

    for i, t in enumerate(testlist):
        #if i != 26: # used for debugging specific problems, should be commented out
        #    continue

        istr = str(i + 1).zfill(2)

        try:
            print "Test " + istr + ":\n>> " + t.replace("\n", "\n   ")

            comp = scummbler_compiler.CompilerFactory(SCUMM_version)
            comp.enableTesting()
            results = comp.compileString(t)

            if not istr in knownfailures:
                print "== Results: " + str(results) + "\n"
            else:
                print "!! ERRONEOUSLY SUCCEEDED: " + str(results) + "\n"
        except ParseException, pe:
            if not istr in knownfailures:
                print "!! FAILED: " + str(pe) + "... lineNum: " + str(comp.lineNum) + "\n" + pe.line
                failedtests.append(istr)
            else:
                print "== Failed: " + str(pe) + "... lineNum: " + str(comp.lineNum) + "\n"

    print "Finished tests."

    if len(failedtests) > 0:
        print "\nThe following tests failed: " + ', '.join(failedtests)


def __mass_test():
    """ Parses all .txt files in the \tests subdirectory of the current working directory.

    TODO: support seperate sub-directories for each SCUMM version."""
    global SCUMM_version
    returnval = 0

    testpath = os.path.join(os.getcwd(), 'tests')

    testfiles = [os.path.join(testpath, t) for t in os.listdir(testpath) if os.path.splitext(t)[1] == '.txt']

    failed_files = []

    for infile in testfiles:
        try:
            scummbler_compiler_helper.compile_script(infile, SCUMM_version, None)

        except ParseException, pe:
            print "Error parsing input file: " + str(pe)
            print pe.line
            returnval = 1
            failed_files.append(infile)
            continue
        except ScummblerException, se:
            print "Error parsing input file: " + str(se)
            returnval = 1
            failed_files.append(infile)
            continue
        except Exception, e:
            returnval = 1
            print "ERROR - Unhandled Exception: " + str(e)
            failed_files.append(infile)
            continue

    if returnval != 0:
        print "\nFAILED: the following files failed parsing:"
        print ','.join(failed_files)

    return returnval


def main_selector(args):
    msg = "Pass 1 to run old tests, or 2 to run batch compiling tests."
    if len(args) != 2:
        print msg
        return
    arg = int(args[1]) # will crash if arg isn't an int
    if arg == 1:
        return __run_tests()
    elif arg == 2:
        return __mass_test()
    else:
        print msg
        return


if __name__ == "__main__":
    sys.exit(main_selector(sys.argv))