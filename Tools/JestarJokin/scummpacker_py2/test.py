#! /usr/bin/python
"""
Bootstrap loader for unit tests. Run from the command line like so:
> test.py base.animation
"""

import logging
import os
import sys
import unittest

def _do_specific_test(test_name):
    print "Starting tests for module: test." + test_name
    test_module = __import__("test." + test_name)
    unittest.main(test_module)
    print "Finished tests for module: " + test_name

def _do_test_suite():
    test_module = __import__("test")
    unittest.main(test_module)

def _start_tests():
    logging.basicConfig(format="", level=logging.DEBUG)
    args = sys.argv[1:]
    if len(args) > 0:
        for a in args:
            _do_specific_test(a)
    else:
        logging.info("No tests specified, running entire suite.")
        _do_test_suite()

if __name__ == "__main__":
    sys.path.append(os.path.join(os.getcwd(), "src"))
    _start_tests()

