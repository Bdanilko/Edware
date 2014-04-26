#!/usr/bin/env python

# * **************************************************************** **
#
# File: tass.py
# Desc: Front-end for the token assembler
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# Copyright 2006, Microbric Pty Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License (in the docs/licenses directory)
# for more details.
#
# Svn: $Id: tass.py 51 2006-12-02 01:14:52Z briand $
# * **************************************************************** */

import gui.logging_utils
import logging
import warnings
import sys
import optparse
import os
import os.path

import gui.token_assembler
import gui.token_downloader
import gui.tokens
import gui.hl_parser


def assemble(options, f_name):

    err = gui.logging_utils.Error_reporter()
    err.set_exit_on_error(True)
    if (not options.throw):
        err.set_throw_on_error(False)
        
    err.set_context(1, "Reading tokens from master file: %s" % (f_name))

    # setup the token stream
    token_stream = gui.tokens.Token_stream(err)
    token_stream.clear()

    file_read = gui.token_assembler.assem_file(f_name, [], token_stream, err)

    if (not file_read):
        sys.exit(1)
        
    # analysis the token stream
    err.set_context(1, "Analysing tokens from master file: %s" % (f_name))
    
    #token_stream.dump_tokens()
    #gui.logging_utils.dump_object(token_stream, "Token_stream")

    token_analysis = gui.tokens.Token_analyser(token_stream, err)
    token_analysis.map_all_variables()

    if (options.debug):
        gui.hl_parser.dump_devices()
        token_analysis.dump_variable_map()
        
    token_analysis.fixup_jumps()

    if (options.debug):
        token_stream.dump_tokens(options.source)
        token_analysis.dump_extras()

    download_type, version, header = token_analysis.create_header()
    #print download_type, version, header
    
    #gui.logging_utils.dump_object(token_analysis, "Token_analyser")

    # get the token bytes
    download_str = ""
    download_bytes = []
    for t in header:
        download_bytes.append(t)
        download_str += chr(t)
    
    for t in token_stream.token_stream:
        bytes = t.get_token_bits()
        download_bytes.extend(bytes)
        for b in bytes:
            download_str += chr(b)

    # some sort of output
    print "Assembly completed of file: %s -- created %d bytes of tokens and header" % (f_name, len(download_str))

    err.set_context(1, "Writing assembled bytes.")
    
    # now output to a file and/or a comms channel
    if (options.filename):
        download_str = gui.token_downloader.serial_wakeup_bytes(download_type, version) + download_str
        print "Writing %d bytes to file: %s" % (len(download_str), options.filename)
        fh = file(options.filename, 'wb')
        fh.write(download_str)
        fh.close

    if (options.device):
        print "Writing %d bytes to device: %s" % (len(download_bytes), options.device)
        return gui.token_downloader.send_bytes(download_type, version, download_bytes, options.device, err)
    else:
        return True

def main(args):
    usage = "usage: %prog [options] input_token_filename"
    version="%prog 1.1 (for token_spec 3.6)"
    
    # clear global memory
    gui.hl_parser.reset_devices_and_locations()
    gui.token_assembler.reset_tokens()
    
    parser = optparse.OptionParser(usage=usage, version=version)
    parser.add_option("-r", "--reghelp", action="store_true", dest="reghelp",
                      help="Output all of the device types, locations and registers")
    
    parser.add_option("-f", "--file", dest="filename",
                      help="A file to store the output into")
    parser.add_option("-c", "--comms", dest="device",
                      help="Choose the communications device to use.")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="Output parsing information.")
    parser.add_option("-s", "--source", action="store_true", dest="source",
                      help="Output source info with debug info.")
    parser.add_option("-t", "--throw", action="store_true", dest="throw",
                      help="Throw an exception (so lots of info) on a parsing error.")
    
    parser.set_defaults(debug = False, source=False, throw = False, reghelp=False, strip=False)
    parser.set_defaults(filename=None, device=None)

    (options, arguments) = parser.parse_args(args)

    if (options.source and not options.debug):
        print "Warning: --source (or -s) makes no sense without --debug (or -d)."

    if (options.reghelp):
        print "Device type, locations and register help"
        print "----------------------------------------"
        gui.hl_parser.dump_reg_help()
        sys.exit(0)

    if (len(arguments) != 1):
        print "ERROR - no token filename to use"
        sys.exit(1)

    f_name = arguments[0]
    
    # check files
    if (not os.path.isfile(f_name) or not os.access(f_name, os.R_OK)):
        print "ERROR - input file %s doesn't exist or isn't readable" % (f_name)
        sys.exit(1)

    if (options.device):
        if (not os.path.exists(options.device) or not os.access(options.device, os.R_OK|os.W_OK)):
            print "ERROR - device %s doesn't exist or isn't readable and writable." % (options.device)
            sys.exit(1)
            
    if (options.filename):
        if (os.path.exists(options.filename) and not os.access(options.filename, os.W_OK)):
            print "ERROR - output file %s exists but isn't writable." % (options.filename)
            sys.exit(1)
            

    # setup logging
    warnings.filterwarnings("ignore", "tempnam is a potential security risk to your program")
    tmp_dir = os.path.dirname(os.tempnam())

    if (options.debug):
        console_level = logging.INFO
        file_level = logging.DEBUG
    else:
        console_level = logging.WARNING
        file_level = logging.INFO
        
    log_fname = os.path.join(tmp_dir, "tass.log")
    gui.logging_utils.setup_root(fname = log_fname, console_level=console_level, file_level=file_level)

    assemble(options, f_name)



#####################################
if __name__ == "__main__":
    main(sys.argv[1:])
    
