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

Parses & compiles SCUMM V3, V4, and V5 scripts.

Gotchas:
 - Labels only support alphanumeric characters and the underscore ("_") character.
 - "Local", "Var", and "Bit" are case sensitive and must begin with a capital letter.
 - The last item in a script should always be "stopObjectCode()" - maybe I could automate this?
 - "If" statements with no instructions after them will compile, but will create a runtime error 
   (because "ifs" are actually jumps, and the way I generate them it will try to jump to a
   non-existant only situation this could occur is if the above "gotcha" is violated.
 - You probably should not have a line containing just a label and a comment. It seems to
   work from testing, but I don't fully comprehend the grammar I wrote, so the world MAY end.
 - startScript is tricky. You can have opcode, or extra parameters R and F, but if you have
   the input opcode present, it will be ORed with the output opcode (which may already have
   flags from the extra "R" and "F" parameters). So, if you're using R and F, don't use the
   descumm opcodes.
   
Potential Tasks:
 - Compiler niceties, like arithmetic on constants, selecting "delay" or "delayVariable"
   based on the argument it's given...
 - Syntactic sugar, like joining multiple "if" statements with "and", "or".
 - Allow using returning functions in "if" statements (original SCUMM compiler seems
   to do this by calling the function, assigning value to VAR_RESULT, then testing
   if VAR_RESULT is equal/not equal to zero).
 - Have a "strict" command-line option. Change "Optional(SupLit(")"))" to a new function
   that returns the optional ")" if strict is not set, otherwise...?
 - Better parse error handling & messages (may not be possible with PyParsing); this is
   really VERY needed, as I've found with test scripts that if there's a problem within
   an "if" block, the error currently points to the start of the block, not the problem.
   There are a couple of solutions for this on the various Pyparsing discussion areas.
 
Need real example for comparison:
 - isActorInBox
 - most of roomOps
 - most sub-opcodes
"""
import os.path
import sys
from optparse import OptionParser

from pyparsing import ParseException, ParseFatalException

from scummbler_compiler_helper import compile_script
from scummbler_misc import ScummblerException, global_options

RUN_TESTS = 1

SCUMM_version = "5"
SCUMM_versions = ["3old", "3", "4", "5"] # this should probably be shared/centralised with compiler & grammar somehow

def main():
    global SCUMM_version
    global SCUMM_versions
    global global_options
    oparser = OptionParser(usage="%prog [options] arg1 arg2 arg3...",
                           version="Scummbler v2",
                           description="Compiles SCUMM scripts as output by descumm.")
    oparser.add_option("-v", "--script-version", action="store",
                       dest="scummver",
                       choices=SCUMM_versions,
                       help="Specify the SCUMM version to target. " +
                       "Possible options are: " +
                       ", ".join(SCUMM_versions) + ". " +
                       "[Default: " + SCUMM_version + "]")
    oparser.add_option("-o", "--output", action="store",
                       dest="outputfile",
                       help="Specify a name for the output script file. " +
                       "If no name is specified, Scummbler will generate one based on the script type. " +
                       "You cannot specify an output file name if you pass in multiple input files or a directory.")
    oparser.add_option("-l", "--legacy-descumm", action="store_true",
                       dest="legacydescumm", default=False,
                       help="Relaxed parsing of descumm scripts, and uses karat-style escape codes (e.g. \"^255^3\"). " +
                       "Only for backwards compatibility.")
    oparser.set_defaults(scummver=SCUMM_version, outputfile=None)

    options, args = oparser.parse_args()
    SCUMM_version = options.scummver
    outputfilename = options.outputfile
    global_options.legacy_descumm = options.legacydescumm
    
    returnval = 0

    if len(args) == 0:
        print "Please give a directory or at least one file name as the argument to Scummbler."
        oparser.print_help()
        return 1
    
    if len(args) == 1 and os.path.isdir(args[0]):
        args = [os.path.join(args[0], f) for f in os.listdir(args[0]) if os.path.splitext(f)[1].lower() == '.txt']
    
    if outputfilename != None and len(args) > 1:
        print "You cannot specify an output file name when you have multiple input files."
        oparser.print_help()
        return 1
        
    for infile in args:
        if not os.path.isfile(infile):
            print "Invalid filename: " + str(infile)
            returnval = 1
            continue
        
        try:
            compile_script(infile, SCUMM_version, outputfilename)
                
        except ParseException, pe:
            returnval = 2
            print "Error parsing input file: " + str(pe)
            print pe.line
            continue
        except ParseFatalException, pfe:
            returnval = 2
            print "Error parsing input file: " + str(pfe)
            print pfe.line
            continue
        except ScummblerException, se:
            returnval = 2
            print "Error parsing input file: " + str(se)
            continue
        except Exception, e:
            returnval = 3
            print "ERROR - Unhandled Exception: " + str(e)
            continue
    
    return returnval
        
if __name__ == "__main__":
    sys.exit(main())

