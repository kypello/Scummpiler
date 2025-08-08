#! /usr/bin/python
"""
Bootstrap loader for unit tests. Run from the command line like so:
> test.py base.animation
"""

import logging
import sys
import unittest

def _do_specific_test(test_name):
    print "Starting tests for module: test." + test_name
    test_module = __import__("test." + test_name)
    unittest.main(test_module)
    if hasattr(test_module, "perform_aux_tests"):
        test_func = getattr(test_module, "perform_aux_tests")
        test_func()
    print "Finished tests for module: " + test_name

def _start_tests():
    logging.basicConfig(format="", level=logging.DEBUG)
    args = sys.argv[1:]
    if len(args) > 0:
        for a in args:
            _do_specific_test(a)
    else:
        logging.warning("No tests specified.")

# TODO: not sure how to define comprehensive tests.
def _test_suite():
    return [
        "base.animation",
    ]

if __name__ == "__main__":
   _start_tests()

