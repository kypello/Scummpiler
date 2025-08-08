#! /usr/bin/python
"""
Use, distribution, and modification of the ScummPacker binaries, source code,
or documentation, is subject to the terms of the MIT license, as below.

Copyright (c) 2008-2014 Laurence Dougal Myers

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
"""

import logging
import sys
import traceback
import scummpacker_control as control
import scummpacker_res_handler as res_handler
import scummpacker_util as util


if sys.version_info[0] < 2 or (sys.version_info[0] == 2 and sys.version_info[1] < 5):
    raise util.ScummPackerException("ScummPacker requires Python 2.5 or higher.")

def main():
    try:
        logging.basicConfig(format="", level=logging.DEBUG)
        logging.NORMAL = 15
        logging.normal = lambda x: logging.log(logging.NORMAL, x)
        logging.level = logging.NORMAL
        # Delegate argument parsing to the global arguments container
        control.global_args.parse_args()
        args_validation = control.global_args.validate_args()

        if args_validation is not None:
            logging.error(args_validation)
            control.global_args.print_help()
            return 1

        if control.global_args.unpack:
            logging.normal("Starting game resource unpacking.")
            # Check that we have an input file name
            if control.global_args.input_file_name == None:
                raise util.ScummPackerException("No input path specified")
            # Check that we have an output file name
            if control.global_args.output_file_name == None:
                raise util.ScummPackerException("No output path specified")
            
            res_handler.global_res_handler.unpack()
            logging.normal("Finished!")
            return 0

        elif control.global_args.pack:
            logging.normal("Starting packing to game resources.")
            # Check that we have an input file name
            if control.global_args.input_file_name == None:
                raise util.ScummPackerException("No input path specified")
            # Check that we have an output file name
            if control.global_args.output_file_name == None:
                raise util.ScummPackerException("No output path specified")
            
            res_handler.global_res_handler.pack()
            logging.normal("Finished!")
            return 0
        
    except Exception, e:
        logging.error("Unhandled exception occured: " + str(e))
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

