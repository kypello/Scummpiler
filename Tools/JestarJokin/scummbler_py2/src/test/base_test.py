import unittest
from pyparsing import ParseFatalException, ParseException
import scummbler_compiler
import scummbler_grammar

class BaseScummblerTest(unittest.TestCase):

    compilers = { "3old" : scummbler_compiler.CompilerV3Old,
              "3": scummbler_compiler.CompilerV3,
              "4": scummbler_compiler.CompilerV4,
              "5": scummbler_compiler.CompilerV5 }
    # SCUMM engine version
    grammars = { "3old": scummbler_grammar.GrammarV3Old, # Indy 3 uses an "old" version of 3
                 "3": scummbler_grammar.GrammarV3,
                 "4": scummbler_grammar.GrammarV4,
                 "5": scummbler_grammar.GrammarV5 }

    def compile(self, version, script):
        grammar = self.grammars[version]()
        comp = self.compilers[version](grammar)
        comp.enableTesting()
        try:
            return comp.compileString(script)[0]
        except ParseException, pe:
            print "Error parsing input string: " + str(pe)
            print pe.line
            raise pe
        except ParseFatalException, pfe:
            print "Error parsing input string: " + str(pfe)
            print pfe.line
            raise pfe

