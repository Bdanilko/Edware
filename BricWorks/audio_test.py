#!/usr/bin/env python

# * **************************************************************** **
#
# File: audio_test.py
# Desc: Create wave files
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# * **************************************************************** */

import sys
import os
import os.path
import string
import wave


def decode(inFilePath):
    print "Debug: in decode() with inFilePath:|%s|" % (inFilePath)
    waveReader = wave.open(inFilePath, 'rb')
    print "Channels:%d, Bytes/sample:%d, Framerate:%d" % \
        (waveReader.getnchannels(),waveReader.getsampwidth(), waveReader.getframerate())
    print "Frames:%d, Comp-type:%s, Comp-name:%s" % \
        (waveReader.getnframes(),waveReader.getcomptype(), waveReader.getcompname())

    chans = waveReader.getnchannels()
    width = waveReader.getsampwidth()
    frames = waveReader.getnframes()
    count = 0

    while (count < frames):
        data = waveReader.readframes(1)

        if (width == 1):
            print "%00d Left: 0x%02x, Right: 0x%02x" % \
                (count, ord(data[0]), ord(data[1]))
        elif (width == 2):
            print "%00d Left: 0x%02x%02x, Right: 0x%02x%02x" % \
                (count, ord(data[1]), ord(data[0]), ord(data[3]), ord(data[2]))
        else:
            print "Error: only handle 8 or 16-bit audio"
            sys.exit(1)
            
        count += 1

def createAudio(midQuantas):
    data = ""
    
    # write fars
    count = 0
    while (count < 22):
        data += chr(255) + chr(0)
        count += 1

    # write nears
    count = 0
    while (count < 22):
        data += chr(0) + chr(255)
        count += 1

    if (midQuantas > 0):
        count = 0
        samples = midQuantas * 22
        while (count < samples):
            data += chr(128) + chr(128)
            count += 1

    return data
        
    
def convert(hexString, outFilePath):
    print "Debug: in convert() with hexString:|%s|" % (hexString)
    waveWriter = wave.open(outFilePath, 'wb')
    waveWriter.setnchannels(2)
    waveWriter.setsampwidth(1)
    waveWriter.setframerate(44100)
    waveWriter.setcomptype("NONE", "")

    # now generate the file
    index = 0
    
    while (index < len(hexString)):
        data = int(hexString[index:index+2], 16)
        # add start
        waveWriter.writeframes(createAudio(6))
        
        # now the actual data -- big endian or little endian
        mask = 1
        while (mask <= 0x80):
            if (data & mask):
                waveWriter.writeframes(createAudio(2))
            else:
                waveWriter.writeframes(createAudio(0))
            mask <<= 1
            
        # add stop
        waveWriter.writeframes(createAudio(6))

        index += 2

def usage():
    progName = os.path.basename(sys.argv[0])
    print "Usage: %s <hex-string> <output-file-name>" % (progName)
    print "\twhere hex-string is a sequence of 2 character hex bytes"
    print "\t\tExample 1020AABBCCDDEEFFA55A"
    print "\tand output-file-name is the name of a file to save the wav into"
    
    
def main(args):
    print "Debug: in main() with args:|%s|" % (args)

    if (len(args) < 1 or len(args) > 2):
        usage()
        sys.exit(1)

    if (args[0] == '-h' or args[0] == '-?'):
        usage()
        sys.exit(0)

    if (len(args) != 2):
        usage()
        sys.exit(1)

    hexString = args[0]
    outFilePath = os.path.abspath(args[1])

    # is hex string the special 'decode' string?
    if (hexString == "decode"):
        if (not os.path.isfile(outFilePath)):
            print "Error: input file doesn't exist!"
            sys.exit(1)
            
        decode(outFilePath)
        sys.exit(0)
        
    # check if outFile is ok
    if (not os.path.isdir(os.path.dirname(outFilePath))):
        print "Error: output file directory doesn't exist!"
        sys.exit(1)

    if (len(os.path.splitext(outFilePath)[1])==0):
        outFilePath += ".wav"
            
    # check if hexString is ok
    count = 0
    for c in hexString:
        if c not in string.hexdigits:
            print "Error: hex-string had a bad character - %c" % (c)
            sys.exit(1)
        count += 1

    if ((count % 2) == 1):
        print "Error: hex-string has to have an even number of characters"
        sys.exit(1)

        
    convert(hexString, outFilePath)


#####################################
if __name__ == "__main__":
    main(sys.argv[1:])
    
