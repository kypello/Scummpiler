#! /usr/bin/python
import logging
import sys

def _do_specific_test(test_name):
    print "Starting tests for module: " + test_name
    test_module = __import__(test_name)
    test_func = getattr(test_module, "test_" + test_name.replace(".", "_"))
    test_func()
    print "Finished tests for module: " + test_name

def _do_test_suite():
    pass

def _start_tests():
    logging.basicConfig(format="", level=logging.DEBUG)
    args = sys.argv[1:]
    if len(args) > 0:
        for a in args:
            _do_specific_test(a)
    else:
        do_test_suite()

if __name__ == "__main__":
   _start_tests()
