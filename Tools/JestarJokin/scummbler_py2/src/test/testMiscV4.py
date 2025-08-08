import unittest
from pyparsing import ParseException
from test.base_test import BaseScummblerTest

class TestMiscV4(BaseScummblerTest):
    def test_MI1_SC_026_v4(self):
        """This test checks that I haven't screwed up the grammar for "getState". I originally
        defined it so it was looking for this:
        if (getState(Local[0] == 1))
        when it should have been this:
        if (getState(Local[0]) == 1)
        """
        script = """
[000A] (8F) if (getState(Local[0]) == 1) {
[002D] (C0)   endCutscene();
[002E] (**) }"""
        results = self.compile("4", script)
        print repr(results)

    def test_MI1_SC_082_v4(self):
        """Check that we can support descumm outputting an empty 2nd argument for PutCodeInString.
        """
        script = """[0000] (27) PutCodeInString(24, );"""
        expected = ('\x27' + # "PutCodeInString" opcode
                    '\x01\x18' + # arg 1 - the object/code ref?
                    '\x00') # arg 2 - the string (empty)
        results = self.compile("4", script)
        print repr(results)
        self.assertEqual(expected, results)

    def test_MI1_SC_086_v4(self):
        """The "debug?" function was renamed to "debug" in descumm, so support the new version.
        TODO: add support for the legacy name."""
        script = """[0000] (6B) debug(1);"""
        expected = ('\x6B' + # "PutCodeInString" opcode
                    '\x01\x00') # arg 1

        results = self.compile("4", script)
        print repr(results)
        self.assertEqual(expected, results)

    def test_MI1_SC_135_v4(self):
        """descumm adds an annoying extra semicolon after the "Key()" instruction. Support it.
        Also, should support the "unknown8" inline string function, but I'm going to ignore it for now. User
        must manually alter the script to insert the code as escape characters."""

        script = ('[049C] (FA) VerbOps(Var[100],[SetXY(0,Var[228]),' +
                'Text("How to deal with frustration, disappointment, " + unknown8(8224) + " and irritating cynicism."),' +
                'On(),Key(Var[229]);]);')
        self.assertRaises(ParseException, self.compile, "4", script)

        # \\xFE\\x08\\x20\\x20 is output by descumm as "unknown8(8224)".
        script = ('[049C] (FA) VerbOps(Var[100],[SetXY(0,Var[228]),' +
                'Text("How to deal with frustration, disappointment, \\xFE\\x08\\x20\\x20 and irritating cynicism."),' +
                'On(),Key(Var[229]);]);')
        expected = ('\xfad\x00E\x00\x00\xe4\x00\x02How to deal with frustration, disappointment, \xfe\x08   and irritating cynicism.\x00\x06\x92\xe5\x00\xff') #

        results = self.compile("4", script)
        print repr(results)
        self.assertEqual(expected, results)

    def test_MI1_SC_152_v4(self):
        """descumm incorrectly outputs some string functions without a "+" in-between. Don't try to support this;
        Scummbler should fail. User must manually alter the script."""
        script = """[00BF] (14) print(255,[Color(Local[8]),Center(),Text(getString(VAR_HEAPSPACE)keepText())]);"""
        self.assertRaises(ParseException, self.compile, "4", script)

        script = """[00BF] (14) print(255,[Color(Local[8]),Center(),Text(getString(VAR_HEAPSPACE) + keepText())]);"""
        results = self.compile("4", script)

if __name__ == '__main__':
    unittest.main()
