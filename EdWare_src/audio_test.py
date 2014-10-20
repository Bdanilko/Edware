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

FAR = 1
NEAR = 2
START = 4
DecodeState = 0
BitCount = 0
Byte = 0

def decode(inFilePath, quiet = False):
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
    outputList = []

    while (count < frames):
        data = waveReader.readframes(1)

        if (width == 1):
            if (quiet):
                outputList.append((ord(data[0]), ord(data[1])))
            else:
                print "%00d Left: 0x%02x, Right: 0x%02x" % \
                    (count, ord(data[0]), ord(data[1]))
        elif (width == 2):
            if (quiet):
                outputList.append((ord(data[0]) << 8 + ord(data[1]), ord(data[3]) << 8 + ord(data[4])))
            else:
                print "%00d Left: 0x%02x%02x, Right: 0x%02x%02x" % \
                    (count, ord(data[1]), ord(data[0]), ord(data[3]), ord(data[2]))
        else:
            print "Error: only handle 8 or 16-bit audio"
            sys.exit(1)
            
        count += 1
    return outputList

def detectedState(newState, count):
    global DecodeState
    global BitCount
    global Byte

    output = (False, 0)
    #print "DetectedState state:", newState, " count:", count, "Decode:", DecodeState, " BitCount:", BitCount, " Byte:", Byte
    if (newState == "Start"):
        return False, 0
    
    # sanity check)
    if (newState in ["near", "far"] and count != 22):
        print "ERROR -- %s is wrong length -- should be 22, bit it's %d" % (newState, count)
        return False, 1

    if (newState == "mid"):
        if (((count % 22) == 0) and (((count / 22) == 2) or
                                     ((count / 22) == 6) or
                                     ((count / 22) == 8))):
            pass
        else:
            print "ERROR -- mid is wrong length -- should be either 2,6 or 8 * 22, but it's %d" % (count,)
            return False, 1
    
    if (newState == "far"):
        if (DecodeState == (FAR | NEAR | START)):
            # 0-bit
            BitCount += 1
            DecodeState = START | FAR
        elif (DecodeState & NEAR):
            # pre/post amble
            #DecodeState = 0
            return False, 1
        else:
            # start of a bit or start/stop
            DecodeState |= FAR

    if (newState == "near"):
        # if (DecodeState == START):
        #     # ignore as it could be pre or post amble
        #     pass
        if (DecodeState & NEAR):
            # wrong order if inside byte
            if (BitCount > 0):
                print "ERROR two nears seen together", hex(DecodeState), BitCount
            DecodeState = 0
            return False, 1
        elif not (DecodeState & FAR):
            # should have had "far"
            print "ERROR near with far", hex(DecodeState), BitCount
            DecodeState = 0
            return False, 1
        else:
            # start of a bit or start/stop
            DecodeState |= NEAR

    if (newState == "mid"):
        if not(DecodeState & (FAR | NEAR)):
            # wrong order
            print "ERROR mid without far and near"
            return False, 1
        else:
            if ((count / 22) == 8):
                # start or stop
                if (DecodeState & START):  # stop
                    if (BitCount != 8):
                        print "ERROR stop without 8 bits -- there were", BitCount
                        return False, 1
                    else:
                        output = (True, Byte)
                        BitCount = 0
                        Byte = 0
                        DecodeState = 0
                else:
                    print "ERROR stop bit not in STOP state!"
            elif ((count / 22) == 6):
                # start
                DecodeState = START
            else: #((count / 22) == 2)
                # 1-bit
                Byte |= (1 << BitCount)
                BitCount += 1
                DecodeState = START

    return output
        
def audioToBin(inFilePath):
    # get the list of samples
    sampleList = decode(inFilePath, True)
    byteList = []
    
    state = "Start"
    count = 0
    for left,right in sampleList:
        valid = False
        if (left == 255 and right == 0):
            if (state == "far"):
                count += 1
            else:
                # change of state -- check the old one first
                valid,byte = detectedState(state, count)
                count = 1
                state = "far"
        elif (left == 0 and right == 255):
            if (state == "near"):
                count += 1
            else:
                # change of state -- check the old one first
                valid,byte = detectedState(state, count)
                count = 1
                state = "near"
        elif (left == 128 and right == 128):
            if (state == "mid"):
                count += 1
            else:
                # change of state -- check the old one first
                valid,byte = detectedState(state, count)
                count = 1
                state = "mid"
        else:
            # unknown state
            print "ERROR -- unknown state of the audio channels left %x, right %x" % (left, right)
        
        if (valid):
            #print "Adding byte %x" % byte
            byteList.append(byte)
                
    # whatever is left -- should be end of stop
    if (count > 0):
        valid,byte = detectedState(state, count)
        if (valid):
            #print "Adding byte %x" % byte
            byteList.append(byte)

    # now binaryList should have the decoded binary
    print len(byteList), "bytes decoded from the audio file :"
    count = 0
    for b in byteList:
        if (count == 0):
            print "%02x" % (b),
        elif (count % 16 == 0):
            print ",%02x" % (b)
            count = -1
        else:
            print ", %02x" % (b),
        count += 1

    if (count != 0):
        print
    
        
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
    preamble = 0
    while (preamble < 20):
        waveWriter.writeframes(createAudio(0))
        preamble += 1
        
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
        waveWriter.writeframes(createAudio(8))

        index += 2

    preamble = 0
    while (preamble < 20):
        waveWriter.writeframes(createAudio(0))
        preamble += 1

        
def usage():
    progName = os.path.basename(sys.argv[0])
    print "Usage: %s <hex-string> <output-file-name>" % (progName)
    print "\twhere hex-string is a sequence of 2 character hex bytes"
    print "\t\tExample 1020AABBCCDDEEFFA55A"
    print "\tand output-file-name is the name of a file to save the wav into\n"
    print "\tTwo special hex strings are also supported:"
    print "\tDECODE <input-file-name> which reads and prints the audio data, and"
    print "\tTOBIN <input-file-name> which reads, converts to original, and prints it."
    
    
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

    hexString = args[0].lower()
    outFilePath = os.path.abspath(args[1])

    # is hex string the special 'decode' string?
    if (hexString == "decode"):
        if (not os.path.isfile(outFilePath)):
            print "Error: input file doesn't exist!"
            sys.exit(1)
            
        decode(outFilePath)
        sys.exit(0)

    if (hexString == "tobin"):
        if (not os.path.isfile(outFilePath)):
            print "Error: input file doesn't exist!"
            sys.exit(1)
            
        audioToBin(outFilePath)
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
    
