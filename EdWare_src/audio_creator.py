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

import sys
import optparse
import os
import os.path
import tempfile
import time

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
    usage = "usage: %prog [options] input_binary_filename output_wave_filename"
    version="%prog 0.6"
    
    # clear global memory
    gui.hl_parser.reset_devices_and_locations()
    gui.token_assembler.reset_tokens()
    
    parser = optparse.OptionParser(usage=usage, version=version)
    
    parser.add_option("-f", "--firmware", action="store_true", dest="firmware",
                      help="Treat the input file as firmware")
    parser.add_option("-p", "--pause", dest="pause", type="int",
                      help="time to pause in msecs between bytes (2000)")
    parser.add_option("-b", "--bytes", dest="bytes", type="int",
                      help="bytes between pauses (default 1536)")
    
    parser.set_defaults(firmware = False)
    parser.set_defaults(pause = 2000)
    parser.set_defaults(bytes = 1536)

    (options, arguments) = parser.parse_args(args)

    if (len(arguments) < 1):
        parser.error("ERROR - no binary filename to read from");

    if (len(arguments) < 2):
        parser.error("ERROR - no filename to output the wave data into")
        
    inFilename = arguments[0]
    waveFilename = arguments[1]

    # check files
    if (not os.path.isfile(inFilename) or not os.access(inFilename, os.R_OK)):
        print "ERROR - input file %s doesn't exist or isn't readable" % (inFilename)
        sys.exit(1)

    if (waveFilename):
        if (os.path.exists(waveFilename) and not os.access(waveFilename, os.W_OK)):
            print "ERROR - output file %s exists but isn't writable." % (waveFilename)
            sys.exit(1)

    ## do the actual convert, etc.

    # get the binary code as a string
    inFh = open(inFilename, "rb")
    strBuffer = buffer(inFh.read())
    binCode = bytearray(strBuffer)

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
    if (waveFilename):
        outFh = open(waveFilename, "wb")
    else:
        outFh = tempfile.NamedTemporaryFile(delete=False)
   
    gui.downloader.convertWithPause(binCode, outFh.name, options.pause, options.bytes)
    outFh.flush()
    outName = outFh.name
    outFh.close()


#####################################
if __name__ == "__main__":
    main(sys.argv[1:])
