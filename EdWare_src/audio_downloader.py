#!/usr/bin/env python

# * **************************************************************** **
#
# File: audio_downloader.py
# Desc: Front-end for the audio downloader
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# Copyright 2014, Microbric Pty Ltd.
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
# * **************************************************************** */

import gui.logging_utils
import logging
import warnings
import sys
import optparse
import os
import os.path
import tempfile
import time

import wx
import gui.downloader
import gui.tokens

if sys.platform.startswith("linux"):
    PLATFORM="linux"
    import pyglet
elif sys.platform.startswith("win"):
    PLATFORM="win"
elif sys.platform.startswith("darwin"):
    PLATFORM="mac"
else:
    print "Unsupported platform -", sys.platform
    sys.exit(1)

def main(args):
    usage = "usage: %prog [options] input_binary_filename"
    version="%prog 0.5"
    
    # clear global memory
    gui.hl_parser.reset_devices_and_locations()
    gui.token_assembler.reset_tokens()
    
    parser = optparse.OptionParser(usage=usage, version=version)
    
    parser.add_option("-o", "--output", dest="filename",
                      help="A file to store the audio output into")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="Output parsing information.")
    parser.add_option("-f", "--firmware", action="store_true", dest="firmware",
                      help="Treat the input file as firmware")
    
    parser.set_defaults(debug = False)
    parser.set_defaults(filename=None)

    (options, arguments) = parser.parse_args(args)

    if (len(arguments) != 1):
        print "ERROR - no binary filename to read from"
        sys.exit(1)

    f_name = arguments[0]
    
    # check files
    if (not os.path.isfile(f_name) or not os.access(f_name, os.R_OK)):
        print "ERROR - input file %s doesn't exist or isn't readable" % (f_name)
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
        
    log_fname = os.path.join(tmp_dir, "audio_downloader.log")
    gui.logging_utils.setup_root(fname = log_fname, console_level=console_level, file_level=file_level)


    ## do the actual convert, etc.

    # get the binary code as a string
    inFh = open(f_name, "rb")
    strCode = inFh.read()

    binCode = bytearray(strCode, "ascii")

    # if firmware then add the header bytes
    if (options.firmware):
        length = gui.tokens.word_to_bytes(len(binCode))
        crc =  gui.tokens.word_to_bytes(gui.tokens.calculate_crc(binCode))
        
        headerBytes = [gui.downloader.FIRMWARE_DOWNLOAD_BYTE, gui.downloader.FIRMWARE_VERSION_BYTE,
                       length[0], length[1],
                       crc[0], crc[1]]
        headerBytes.extend(binCode)
        binCode = headerBytes
    
    print "size of binary code:", len(binCode)

    
    # convert to a audio file
    if (options.filename):
        outFh = open(options.filename, "wb")
    else:
        outFh = tempfile.NamedTemporaryFile(delete=False)
   
    gui.downloader.convert(binCode, outFh.name)
    outFh.flush()
    outName = outFh.name
    outFh.close()

    # need to sleep so that pyglet is happy that the file is closed
    time.sleep(1)
    
    # play the audio file
    if PLATFORM == "linux":
        s1 = pyglet.media.load(outName, streaming=False)
        s1.play()
    elif PLATFORM == "win":
        s1 = wx.Sound(outName)
        s1.Play(wx.SOUND_SYNC)


#####################################
if __name__ == "__main__":
    main(sys.argv[1:])
