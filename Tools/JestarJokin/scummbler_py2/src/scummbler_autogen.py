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

This is a dev tool seperate to Scummbler's normal usage.

Potential tasks:
- Optimize parse actions so multiple grammars can use the same action.
- The generated grammar & actions could be evaluated at runtime (instead
  of writing to a file), but I don't think it's worth it (performance & security).
- Could just create one generic parse action that consults a table or two to 
  determine opcode & how to resolve arguments.
"""
import string
import scummbler_opcodes
from scummbler_misc import ScummblerAutogenException, ScummblerAutogenSubopcodeException

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
#* a Python list = nested sub-opcode
arg_lexicon = {
    "V"  : "Group(scummbler_lexicon.leVariable)", # var
    "B"  : "Group(scummbler_lexicon.leByte)", # byte
    "W"  : "Group(scummbler_lexicon.leWord)", # word
    "P8" : "Group(scummbler_lexicon.leVarOrByte)", # byte or var
    "P16": "Group(scummbler_lexicon.leVarOrWord)", # word or var
    "L"  : "scummbler_lexicon.leArgList", # arglist
    #"J"  : leLabel, # jump (do we need this?)
    "A"  : "scummbler_lexicon.leString", # ASCII string without terminating character
    "A0" : "scummbler_lexicon.leString", # ASCII string, null-terminated
    "A1" : "scummbler_lexicon.leString", # ASCII string, 0xFF-terminated
    "FF" : "" # 0xFF
}

indent = "    "

gramlist = []

def generate_name(name, parent=None):
    return "grFunc_" + \
            ("" if parent is None else ''.join([c for c in parent if c in (string.ascii_letters + string.digits)]) + "_") + \
            ''.join([c for c in name if c in (string.ascii_letters + string.digits)])

def resolve_subops(arg, argname, descumm, p_opcode, new_gram):
    """arg: a tuple containing instructions (tuples)
    argname: string containing the name of the arg
    descumm: string containing the name of the calling parent descumm function
    p_opcode: int, parent's opcode, required for instructions that omit the parent
    new_gram: string containing the existing generated grammar for parent function
    
    returns:
    A string.
    If the parent function should not be emitted, the string includes all the generated sub-op grammar.
    Otherwise, string is a modified version of new_gram, with the generated sub-op grammar prepended."""
    multival, omitroot = arg[0]
    
    SO_gram_names = []
    SO_grams = []
    
    for SO_inst in arg[1:]:
        SO_name = generate_name(SO_inst[1], descumm)
        SO_gram_names.append(SO_name)
        SO_grams.append( generate_grammar(SO_inst, descumm) + "\n" )
        SO_grams.append( generate_parse_action(SO_inst, descumm) + "\n")
    
    SO_options_name = generate_name(descumm) + "_SO"
    SO_options = SO_options_name + " = " + " | ".join(SO_gram_names)
    SO_grams.append(SO_options + "\n")
    
    if multival:
        # Surround the grammar for SOs with a delimitedList and bracket literals
        if omitroot:
            raise ScummblerAutogenException("You can't have a multi-subop instruction which omits the root function, silly!", 4203)
        # We make all sub-opcodes optional for multi-value things, because of this example:
        # [010A] (14)       print(255,[]);
        new_gram += "SupLit(\"[\") + Optional(delimitedList(" + SO_options_name + "))(\"" + argname + "\") + SupLit(\"]\")  + "
    elif omitroot:
        # Each sub-opcode acts as a separate function.
        # However, we still need to prepend the parent's opcode, so generate a parse action for the options,
        #  which merely output the parent opcode followed by the (resolved) sub-opcode.
        SO_options_action = ("def do_" + SO_options_name + "(s, loc, toks):\n" +
            indent + "return to_byte(opFunctionTable[\"" + descumm + "\"]) + ''.join(toks)\n" +
            SO_options_name + ".setParseAction(do_" + SO_options_name + ")\n")
        
        SO_grams.append(SO_options_action)
        gramlist.append(SO_options_name)
        return "# --- Start sub-opcodes ---\n" + ''.join(SO_grams) + "# --- End sub-opcodes ---\n" # generate_grammar will know to stop by checking the first item in the tuple
    else:
        new_gram += SO_options_name + "(\"" + argname + "\") + "
    
    # Prepend generated sub-opcode grammar, so that parent opcode can use it
    new_gram = "# --- Start sub-opcodes ---\n" + ''.join(SO_grams) + "# --- End sub-opcodes ---\n" + new_gram
    
    return new_gram

def resolve_arg(arg, argname, parambits):
    """arg: string, the argument type to match
    argname: string, the name of the argument to use in generated output
    parambits: string, representing integer value to be binary ORed with opcode (e.g. "0x80")"""
    global indent
    argact = "# No " + argname
    
    if arg != None:
        if arg == "P8" or arg == "P16": # TODO: bounds checking for bytes and words
            argact = argname + ", op = resolve_parameter(toks." + argname + ", op, " + parambits + ", " + str((arg == "P16")) + ")"
            #argact = ("if not 'vartype' in toks." + argname + ":\n" +
            #           indent + indent + argname + " = " + ("to_word_BE" if arg == "P16" else "to_byte") + "(toks." + argname + ".value)\n" +
            #           indent + "else:\n" +
            #           indent + indent + argname + " = resolve_var(toks." + argname + ")\n" +
            #           indent + indent + "op = op | " + parambits)
        elif arg == "V":
            argact = (argname + " = resolve_var(toks." + argname + ")\n" +
                       indent + "op = op | " + parambits)
        elif arg == "B":
            argact = argname + " = to_byte(toks." + argname + ".value)"
        elif arg == "W":
            argact = argname + " = to_word_LE(toks." + argname + ".value)"
        elif arg == "L":
            #iterate through the list items
            # for each item, create an aux opcode
            # do the same as P16, modifying the aux opcode
            #when done, 0xFF
            argact = (
                "for a in toks." + argname + ":\n" +
                indent + indent + "aux = 0x01\n" +
                indent + indent + "a, aux = resolve_parameter(a, aux, 0x80, True)\n" +
                indent + indent + argname + " += to_byte(aux) + a\n" +
                indent + argname + " += \"\\xFF\""
            )
        #elif arg == "D":
        #    # 24-bit constant... BE? not sure
        #    pass # TODO
        elif arg == "A":
            # terminating character is given in another argument
            # (also strip the quote marks)
            argact = argname + " = toks." + argname
        elif arg == "A1":
            # add "\xFF" to string
            argact = argname + " = toks." + argname + " + \"\\xFF\""
        elif arg == "A0":
            # add "\x00" to string
            argact = argname + " = toks." + argname + " + \"\\x00\""
        elif arg == "FF":
            argact = argname + " = \"\\xFF\""
        elif type(arg) is tuple:
            # If we omit the root parent, raise an exception so
            if arg[0][1]:
                raise ScummblerAutogenSubopcodeException("Catch me, darling! Catch meeee! (this arg don't want no parent emission, and who can blame it?)", 4201)
            elif arg[0][0]: # workaround for mutli-subop instruction with no subops
                argact = ("if \"" + argname + "\" in toks:\n" +
                          indent + indent + argname + " = ''.join(toks." + argname + ")")
            else:
                # Sub-opcode is already parsed by its own action, so just plonk it in
                # (might be multiple sub-ops, so join them all together)
                argact = argname + " = ''.join(toks." + argname + ")"
        else:
            raise ScummblerAutogenException("Stupid fool! You have done wrong! Prepare your family for your imminent demise! (unknown arg type in autogen: " + str(arg) + ")", 4202)
        
    return argact
    

def generate_grammar(instr, parent=None):
    """ instr: a tuple containing 6 items: opcode (int), descumm (string), returns_result (bool),
    arg1 type (string), arg2 type (string), arg3 type (string).
    parent: the descumm string of the parent grammar, used for naming sub-opcode grammars. Defaults to None.
    
    returns:
     a string containing the generated grammar.
    
    if parent is None, the generated grammar is added to the global gramlist, to be used in
    creating the final grammar of all functions."""
    global gramlist
    opcode, descumm, returns_result, arg1, arg2, arg3 = instr
    
    new_gram = generate_name(descumm, parent) + " = "
    
    if returns_result:
        new_gram += "Group(scummbler_lexicon.leVariable)(\"target\") + SupLit(\"=\") + "
        
    new_gram += "Literal(\"" + descumm + "\")(\"function\") + SupLit(\"(\") + "
    if arg1 != None:
        if type(arg1) is tuple:
            new_gram = resolve_subops(arg1, "arg1", descumm, opcode, new_gram)
            if arg1[0][1]: # I don't like this much
                return new_gram
        else:
            new_gram += arg_lexicon[arg1] + "(\"arg1\") + "
    if arg2 != None and arg2 != "FF":
        if type(arg2) is tuple:
            new_gram += "SupLit(\",\") + "
            new_gram = resolve_subops(arg2, "arg2", descumm, opcode, new_gram)
            if arg2[0][1]:
                return new_gram
        else:
            new_gram += "SupLit(\",\") + "  + arg_lexicon[arg2] + "(\"arg2\") + "
    if arg3 != None and arg3 != "FF":
        if type(arg3) is tuple:
            new_gram += "SupLit(\",\") + "
            new_gram = resolve_subops(arg3, "arg3", descumm, opcode, new_gram)
            if arg3[0][1]:
                return new_gram
        else:
            new_gram += "SupLit(\",\") + " + arg_lexicon[arg3] + "(\"arg3\") + "
    new_gram += "SupLit(\")\")"
    
    if parent is None:
        gramlist.append(generate_name(descumm))
        
    return new_gram
    
    
def generate_parse_action(instr, parent=None):
    """Creates a parse action and associates it with a grammar."""
    global indent
    global action_list
    opcode, descumm, returns_result, arg1, arg2, arg3 = instr
    
    indent = "    "
    actname = generate_name(descumm, parent)
    
    if returns_result:
        resultact = "target = resolve_var(toks.target)"
    else:
        resultact = "# No target"
        
    try:
        arg1act = resolve_arg(arg1, "arg1", "0x80")
        arg2act = resolve_arg(arg2, "arg2", "0x40")
        arg3act = resolve_arg(arg3, "arg3", "0x20")
    except ScummblerAutogenSubopcodeException, sae:
        # if instruction has sub-opcodes and they omit the parent function,
        #  don't generate any parse action text.
        return ""
    
    new_act = (
        "def do_" + actname + "(s, loc, toks):\n" +
        indent + "target = arg1 = arg2 = arg3 = \"\"\n" +
        #indent + "op = " + str(opcode) + "\n" +
        indent + "op = opFunctionTable[toks.function]\n" +
        indent + resultact + "\n" +
        indent + arg1act + "\n" +
        indent + arg2act + "\n" +
        indent + arg3act + "\n" +
        indent + "return to_byte(op) + target + arg1 + arg2 + arg3\n"
        )

    new_act += actname + ".setParseAction(do_" + actname + ")"
    return new_act


def autogen_grammar():
    global gramlist
    outfile = file("scummbler_autogram.py", "w")
    
    outfile.write("#!/usr/bin/env python\n")
    outfile.write(
        """\"\"\"
Scummbler v2

    This file is part of Scummbler.

    Scummbler is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Scummbler is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with Scummbler.  If not, see <http://www.gnu.org/licenses/>.

Laurence Dougal Myers
www.jestarjokin.net

December 2008 - July 2009

This file is automatically generated and should not be modified.
Run scummbler_autogen.py to recreate this file.

It is outdated and no longer used as a module, and in fact
there are errors with looking up sub-opcodes.
\"\"\"\n"""
    )
    outfile.write("from pyparsing import *\n" +
                  "import scummbler_lexicon\n" +
                  "from scummbler_misc import *\n" +
                  "from scummbler_opcodes import opFunctionTable\n" +
                  "\n")
    
    for i in scummbler_opcodes.opAutogenTable:
            gram = generate_grammar(i)
            outfile.write(gram + "\n")
            outfile.write(generate_parse_action(i) + "\n")
            outfile.write("\n")
    
    outfile.write("grFunctions = " + " | ".join(gramlist))
    outfile.close()
    print "Done!"

if __name__ == "__main__": autogen_grammar()
