import unittest
from test.base_test import BaseScummblerTest

class TestDrawObject(BaseScummblerTest):
    def test_drawObject_v4(self):
        script = "[0138] (05) drawObject(189,255,255);"
        expected = ('\x05' + # "drawObject" opcode, with bits set for args
                    '\xBD\x00' + # arg 1 - the object to draw
                    '\xff\x00' + # arg 2 - x
                    '\xff\x00') # arg 3 - y
        results = self.compile("4", script)
        print repr(results)
        self.assertEqual(expected, results)

if __name__ == '__main__':
    unittest.main()
