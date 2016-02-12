
# * **************************************************************** **
#
# File: token_downloader.py
# Desc: Download tokens to the target
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# Copyright 2006, 2014, 2015, 2016 Microbric Pty Ltd.
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

import logging_utils
import logging

import sys
import os
import os.path
import time

# Using pyserial multi-platform serial library
# import serial

# SERIAL_BAUD = 38400
# SERIAL_STOP = serial.STOPBITS_ONE       # STOPBITS_ONE, STOPBITS_TWO
# SERIAL_BITS = serial.EIGHTBITS
# SERIAL_PARITY = serial.PARITY_NONE      # PARITY_NONE, PARITY_EVEN, PARITY_ODD
# SERIAL_READ_TIMEOUT = 5                 # timeout in seconds - need time for sector erase
# SERIAL_WRITE_TIMEOUT = 1                # Without flow control it should never paus

# SERIAL_BYTES_BETWEEN_ACKS = 256         # Set to zero for no ACK/NACKS

ACK = 0x06
NACK = 0x15
PRE_WAKEUP_ONE = "wakeup!!!"
PRE_WAKEUP_STR = PRE_WAKEUP_ONE*2
SERIAL_WAKEUP_STR = "\x1b\x00\xde\xad\xbe\xef\xff\x1b"
PROGRAM_STR = "\xa1"
FIRMWARE_STR = "\x56"

TIMEOUT = -1


# def send_bytes(dtype, version, bytes, device, err):
#     return use_serial(dtype, version, bytes, device, err)

# def get_ack_nack(ser):
#     which = ser.read(1)
#     if (not which):
#         return -1
#     else:
#         return ord(which[0])

# def serial_wakeup_bytes(dtype, version):
#     # output the wakeup bytes
#     wakeup = SERIAL_WAKEUP_STR
#     if (dtype == "program"):
#         wakeup += PROGRAM_STR
#     else:
#         wakeup += FIRMWARE_STR
#     wakeup += chr(((version[0] & 0x0f) << 4) | (version[1] & 0x0f))

#     return wakeup

# def use_serial(dtype, version, bytes, device, err, notify_func=None):
#     err.set_context(1, "Downloading to robot using serial device:%s" % (device))
#     if (not os.path.exists(device) or not os.access(device, os.R_OK|os.W_OK)):
#         err.report_error("ERROR - device %s doesn't exist or isn't readable and writable." % (device))
#         return False

#     index = 0
#     block_size = SERIAL_BYTES_BETWEEN_ACKS
#     block_count = 0

#     # open up the device
#     try:
#         ser = serial.Serial(port=device, baudrate=SERIAL_BAUD, bytesize=SERIAL_BITS,
#                             parity=SERIAL_PARITY, stopbits=SERIAL_STOP,
#                             timeout=SERIAL_READ_TIMEOUT, writeTimeout=1)

#     except serial.serialutil.SerialException, e:
#         err.report_error("ERROR opening device %s : %s" % (device, str(e)))
#         return False

#     ser.flushOutput()
#     ser.flushInput()

#     # output ANY bytes to arouse the robot
#     try:
#         ser.write(PRE_WAKEUP_STR)
#     except serial.serialutil.SerialException, e:
#         err.report_error("ERROR writing to device %s : %s" % (device, str(e)))
#         return False

#     # give time for the hybrid to wakeup and initialise it's hardware
#     time.sleep(2)

#     #
#     wakeup = serial_wakeup_bytes(dtype, version)
#     try:
#         ser.write(wakeup)
#     except serial.serialutil.SerialException, e:
#         err.report_error("ERROR writing to device %s : %s" % (device, str(e)))
#         return False

#     which = get_ack_nack(ser)
#     if (which != ACK):
#         if (which == NACK):
#             err.report_error("NACK received from robot after wakeup (incompatible version?)")
#         elif (which == -1):
#             err.report_error("Timed-out waiting on robot after wakeup.")
#         else:
#             err.report_error("Bad response (%s) from robot after wakeup." % (which))
#         return False

#     first_block = True
#     while (index < len(bytes)):
#         try:
#             ser.write(chr(bytes[index]))
#         except serial.serialutil.SerialException, e:
#             err.report_error("ERROR writing to device %s : %s" % (device, str(e)))
#             return False

#         if (block_size):
#             block_count += 1
#             if (block_count == block_size):
#                 which = get_ack_nack(ser)
#                 #print which
#                 if (which != ACK):
#                     if (which == NACK):
#                         if (first_block):
#                             err.report_error("NACKed after first block --\n" + \
#                                              "Download size is probably too large for the robot.")
#                         else:
#                             err.report_error("NACK received from robot at byte %d of %d (Bad CRC?)" % \
#                                              (index, len(bytes)))
#                     elif (which == -1):
#                         err.report_error("Timed-out waiting on robot at byte %d of %d." % \
#                                          (index+1, len(bytes)))

#                     else:
#                         err.report_error("Bad response (%s) from robot at byte %d of %d." % (which, index+1, len(bytes)))
#                     return False
#                 block_count = 0
#                 first_block = False

#         index += 1

#         if (notify_func):
#             notify_func(index)

#     # is a final ack needed?
#     if (block_size and block_count):
#         which = get_ack_nack(ser)
#         if (which != ACK):
#             if (which == NACK):
#                 err.report_error("NACK received from robot at end of transfer (Bad CRC?)")

#             elif (which == -1):
#                 err.report_error("Timed-out waiting on robot at end of transfer.")
#             else:
#                 err.report_error("Bad response (%x) from robot at end of transfer." % (which))
#             return False


#     # close port even though it will close when it goes out of scope
#     ser.close()

#     return True


def use_flashing():
    pass



def gui_serial(dtype, version, bytes, device, msg_ctrl, gauge_ctrl):
    # if (not os.path.exists(device) or not os.access(device, os.R_OK|os.W_OK)):
    #     msg_ctrl.SetLabel("ERROR - device %s doesn't exist or isn't readable and writable." % (device))
    #     return False

    # index = 0
    # block_size = SERIAL_BYTES_BETWEEN_ACKS
    # block_count = 0

    # # open up the device
    # try:
    #     ser = serial.Serial(port=device, baudrate=SERIAL_BAUD, bytesize=SERIAL_BITS,
    #                         parity=SERIAL_PARITY, stopbits=SERIAL_STOP,
    #                         timeout=SERIAL_READ_TIMEOUT, writeTimeout=1)

    # except serial.serialutil.SerialException, e:
    #     msg_ctrl.SetLabel("ERROR opening device %s : %s" % (device, str(e)))
    #     return False

    # ser.flushOutput()
    # ser.flushInput()

    # # output ANY bytes to arouse the robot
    # try:
    #     ser.write(PRE_WAKEUP_STR)
    # except serial.serialutil.SerialException, e:
    #     err.report_error("ERROR writing to device %s : %s" % (device, str(e)))
    #     return False

    # # give time for the hybrid to wakeup and initialise it's hardware
    # time.sleep(2)

    # # output the wakeup bytes
    # wakeup = serial_wakeup_bytes(dtype, version)
    # try:
    #     ser.write(wakeup)
    # except serial.serialutil.SerialException, e:
    #     msg_ctrl.SetLabel("ERROR writing to device %s : %s" % (device, str(e)))
    #     return False

    # which = get_ack_nack(ser)
    # if (which != ACK):
    #     if (which == NACK):
    #         msg_ctrl.SetLabel("NACK received from robot after wakeup (incompatible version?)")
    #     elif (which == -1):
    #         msg_ctrl.SetLabel("Timed-out waiting on robot after wakeup.")
    #     else:
    #         msg_ctrl.SetLabel("Bad response (%s) from robot after wakeup." % (which))
    #     return False

    # first_block = True
    # while (index < len(bytes)):
    #     try:
    #         ser.write(chr(bytes[index]))
    #     except serial.serialutil.SerialException, e:
    #         msg_ctrl.SetLabel("ERROR writing to device %s : %s" % (device, str(e)))
    #         return False

    #     if (block_size):
    #         block_count += 1
    #         if (block_count == block_size):
    #             which = get_ack_nack(ser)
    #             #print which
    #             if (which != ACK):
    #                 if (which == NACK):
    #                     if (first_block):
    #                         msg_ctrl.SetLabel("NACKed after first block -- \n" + \
    #                                           "Download size is probably too large for the robot.")
    #                     else:
    #                         msg_ctrl.SetLabel("NACKed at byte %d of %d (Bad CRC?)" % \
    #                                          (index, len(bytes)))

    #                 elif (which == -1):
    #                     msg_ctrl.SetLabel("Timed-out waiting on robot at byte %d of %d." % \
    #                                      (index+1, len(bytes)))

    #                 else:
    #                     msg_ctrl.SetLabel("Bad response (%s) from robot at byte %d of %d." % (which, index+1, len(bytes)))
    #                 return False

    #             block_count = 0
    #             first_block = False

    #     index += 1

    #     gauge_ctrl.SetValue(index)
    #     gauge_ctrl.Update()

    # # is a final ack needed?
    # if (block_size and block_count):
    #     which = get_ack_nack(ser)
    #     if (which != ACK):
    #         if (which == NACK):
    #             msg_ctrl.SetLabel("NACK received from robot at end of transfer (Bad CRC?)")

    #         elif (which == -1):
    #             msg_ctrl.SetLabel("Timed-out waiting on robot at end of transfer.")
    #         else:
    #             msg_ctrl.SetLabel("Bad response (%x) from robot at end of transfer." % (which))
    #         return False


    # # close port even though it will close when it goes out of scope
    # ser.close()

    return True

#####################################
class Stub_err_reporter(object):
    def __init__(self):
        self.contexts = {}

    def set_context(self, line, context):
        self.contexts[line] = context

        # clear lower contexts
        for k in self.contexts:
            if (k > line):
                del self.contexts[k]

    def report_error(self, message):
        print "Error - %s" % (message)
        ctxts = self.contexts.keys()
        ctxts.sort()
        for c in ctxts:
            print "  Context:%d - %s" % (c, self.contexts[c])
        print


if __name__ == "__main__":
    print "Testing token_downloader module"
    err = Stub_err_reporter()

    bytes = []
    for i in range(4):
        for j in range(256):
            bytes.append(j)

    device = '/dev/ttyUSB0'

    send_bytes("program", (0, 0), bytes, device, err)
