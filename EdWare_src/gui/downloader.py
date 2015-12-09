# * **************************************************************** **
#
# File: downloader.py
# Desc: Downloading to the robot (via screen, usb and firmware via usb)
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# Copyright 2006-2015, 2014 Microbric Pty Ltd.
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

import cPickle
import os
import os.path
import datetime
import wx.lib.filebrowsebutton as fbb
import string

import wx
import device_data
import bric_data
import program_data
import win_data

import logging_utils
import logging
import warnings
import sys
import optparse
import os
import os.path
import paths

import sys
import time

import time
import wave

import subprocess
import tempfile

PORTAUDIO_PRESENT = False
PYGAME_PRESENT = False
WAVER_PRESENT = False
USE_PYGAME = False
USE_PORTAUDIO = False
USE_WINSOUND = False
USE_WAVER = False

TOKEN_VERSION_STR = "\x20"
TOKEN_VERSION_BYTE = 0x20

TOKEN_DOWNLOAD_STR = "\xf1"
TOKEN_DOWNLOAD_BYTE = 0xf1

FIRMWARE_DOWNLOAD_STR = "\xac"
FIRMWARE_DOWNLOAD_BYTE = 0xac

FIRMWARE_VERSION_STR = "\x20"
FIRMWARE_VERSION_BYTE = 0x20

DOWNLOAD_BYTES_BETWEEN_PAUSES = 1536
DOWNLOAD_PAUSE_MSECS = 2000

try:
    import pyaudio
    PORTAUDIO_PRESENT = True
    #print "Pyaudio installed"
except:
    pass

try:
    import pygame
    PYGAME_PRESENT = True
    #print "Pygame installed"
except:
    pass


# if (not (PORTAUDIO_PRESENT or PYGAME_PRESENT)) and (paths.get_platform() != "win"):
#     print "ERROR - No Audio package (pygame or pyaudio) installed!"
#     sys.exit(1)
            
AUDIO_CHUNK = 1024
AUDIO_STRING = ""

def set_audio_output(choice):
    global USE_PORTAUDIO
    global USE_PYGAME
    global USE_WINSOUND
    global USE_WAVER
    global AUDIO_STRING
    
    choice = choice.lower()
    installed = "unknown"
    using = "unknown"

    waver_path = os.path.join(paths.get_run_dir(), "waver", "waver.exe")
    if os.path.isfile(waver_path):
        WAVER_PRESENT = True
    else:
        WAVER_PRESENT = False

    if (PORTAUDIO_PRESENT and PYGAME_PRESENT and WAVER_PRESENT):
        installed = "portaudio, pygame, waver"
    elif WAVER_PRESENT:
        installed = "waver"
    elif (PORTAUDIO_PRESENT):
        installed = "portaudio"
    elif (PYGAME_PRESENT):
        installed = "pygame"
    else:
        installed = "no extra audio backends"

    AUDIO_STRING = "(Audio installed: %s" % (installed)
    
    if (choice == "any"):
        if WAVER_PRESENT:
            USE_WAVER = True
            using = "waver"
        elif (PORTAUDIO_PRESENT):
            USE_PORTAUDIO = True
            using = "portaudio"
        elif (PYGAME_PRESENT):
            USE_PYGAME = True
            using = "pygame"
        else:
            USE_WINSOUND = True
            # must be windows built-in
            using = "built-in winsound"

    elif (choice == "waver"):
        if (not WAVER_PRESENT):
            print "\nERROR - selected audio 'waver' is not installed!"
            sys.exit(1)
        else:
            USE_WAVER = True
            using = choice

    elif (choice == "portaudio"):
        if (not PORTAUDIO_PRESENT):
            print "\nERROR - selected audio 'portaudio' is not installed!"
            sys.exit(1)
        else:
            USE_PORTAUDIO = True
            using = choice

    elif (choice == "pygame"):
        if (not PYGAME_PRESENT):
            print "\nERROR - selected audio 'pygame' is not installed!"
            sys.exit(1)
        else:
            USE_PYGAME = True
            using = choice

    elif (choice == "winsound"):
        if (paths.get_platform() != "win"):
            print "\nERROR - selected audio 'winsound' is not available on non-window systems"
            sys.exit(1)
        else:
            USE_WINSOUND = True
            using = "built-in winsound"
            
    else:
        print "\nERROR - selected audio '%s' is unknown!" % (choice)
        sys.exit(2)

    AUDIO_STRING +=" -  Audio to be used: %s)" % (using)

    #print AUDIO_STRING
    return AUDIO_STRING
            
    
import token_assembler
import token_downloader
import tokens
import hl_parser

err = None

def write_code(file_name):

    if (not file_name):
        file_name = os.path.join(paths.get_store_dir(), "last_compile")
        
    parts = os.path.splitext(file_name)
    file_name = parts[0]+".mbc"
    
    file_handle = file(file_name, 'w')

    win_data.get_all_code(file_handle)
    file_handle.close()
    
    return file_name

def assemble(f_name):
    global err
    err = logging_utils.Error_reporter()
    err.set_exit_on_error(True)
    err.set_throw_on_error(False)
        
    err.set_context(1, "Reading tokens from file: %s" % (f_name))

    # clear global memory
    hl_parser.reset_devices_and_locations()
    token_assembler.reset_tokens()
    
    # setup the token stream
    token_stream = tokens.Token_stream(err)
    token_stream.clear()
    
    file_read = token_assembler.assem_file(f_name, [], token_stream, err)

    if (not file_read):
        sys.exit(1)
        
    # analysis the token stream
    err.set_context(1, "Analysing tokens from file: %s" % (f_name))
    
    #token_stream.dump_tokens()
    #logging_utils.dump_object(token_stream, "Token_stream")

    token_analysis = tokens.Token_analyser(token_stream, err)
    token_analysis.map_all_variables()

    token_analysis.fixup_jumps()

    download_type, version, header = token_analysis.create_header()
    #print download_type, version, header

    # get the token bytes
    download_str = TOKEN_DOWNLOAD_STR + TOKEN_VERSION_STR
    download_bytes = [TOKEN_DOWNLOAD_BYTE, TOKEN_VERSION_BYTE]
    for t in header:
        download_bytes.append(t)
        download_str += chr(t)
    
    for t in token_stream.token_stream:
        bytes = t.get_token_bits()
        download_bytes.extend(bytes)
        for b in bytes:
            download_str += chr(b)

    #print download_bytes
    return download_bytes, download_type, version

def get_bytes(file_name):
    compile_file = write_code(file_name)
    return assemble(compile_file)

# --------------- Check size ----------------------------------

def check_size():
    download_bytes, dtype, version = get_bytes("")
    vars = win_data.vars_stats()
    program_bytes = len(download_bytes)-2

    message = "Program size (bytes): %d\n" % (program_bytes,)
    message += '\n'
    message += "Variables (%s) used: %d, max: %d\n" % (vars[0][0], vars[1][0], vars[2][0])
    message += "Variables (%s) used: %d, max: %d\n" % (vars[0][1], vars[1][1], vars[2][1])

    wx.MessageBox(message, caption="Program Size", style = wx.ICON_INFORMATION|wx.OK)

# --------------- USB dialog ----------------------------------

class usb_downloader(wx.Dialog):
    def __init__(self, usb_device, file_name, title="Set Title!", size=(200, 200)):
        wx.Dialog.__init__(self, None, -1, title, size=(500, 300))
        if (paths.get_platform() != "mac"):
            self.SetBackgroundColour("light grey")

        # self.ports = get_possible_ports()
        # if (usb_device not in self.ports):
        #     if (len(self.ports) > 0):
        #         usb_device = self.ports[0]
        #     else:
        #         usb_device = ""
        usb_device = ""
        
        self.usb_ctrl = wx.ComboBox(self, -1, value=usb_device, choices=self.ports, size=(150,-1))

        
        self.grid = wx.GridBagSizer(5,5)
        self.usb_prompt = wx.StaticText(self, -1, "USB Device:")
        self.progress_prompt = wx.StaticText(self, -1, "Download progress:")
        self.gauge = wx.Gauge(self, -1, range=100)
        self.start = wx.Button(self, -1, "Start Download")
        self.cancel = wx.Button(self, -1, "Cancel Download")
        self.help_text = wx.StaticText(self, -1, "")
        
        self.grid.Add(self.usb_prompt, (1,1),
                 flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        self.grid.Add(self.usb_ctrl, (1,2), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL)


        self.grid.Add(self.progress_prompt, (3,1), span=(1,2), flag=wx.EXPAND)
        self.grid.Add(self.gauge, (4,1), span=(1,3), flag=wx.EXPAND)
        
        self.grid.Add(self.help_text, (6,1), span=(2,2), flag=wx.EXPAND)

        self.grid.AddGrowableRow(7)
        self.grid.Add(self.cancel, (8,2), flag=wx.ALIGN_RIGHT | wx.BOTTOM)
        self.grid.Add(self.start, (8,3), flag=wx.ALIGN_LEFT | wx.BOTTOM)
        self.grid.Add((1,1), (9,2))

        self.SetSizer(self.grid)
        self.Layout()

        self.start.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.on_start, self.start)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel)

        self.download_bytes, self.dtype, self.version = get_bytes(file_name)
        self.byte_count = len(self.download_bytes)
        self.gauge.SetRange(self.byte_count)
        self.gauge.SetValue(0)

        self.help_text.SetLabel("Download size is %d bytes." % (len(self.download_bytes),))

    def get_port(self):
        return self.usb_ctrl.GetValue()

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)


    def on_start(self, event):
        # get the device
        device = self.usb_ctrl.GetValue()
##        if (not os.path.exists(device) or not os.access(device, os.R_OK|os.W_OK)):
##            self.help_text.SetLabel("ERROR - device %s doesn't exist or isn't readable and writable." % (device))
##            return
        
        # can't start twice so disable this button
        self.start.Disable()
        self.help_text.SetLabel("Starting download of %d bytes." % (self.byte_count,))
        self.Update()

        result = token_downloader.gui_serial(self.dtype, self.version, self.download_bytes,
                                             device, self.help_text, self.gauge)

        #print "Result:", result
        if (not result):
            self.start.Enable()
        else:
            self.gauge.SetValue(self.byte_count)
            self.help_text.SetLabel("Downloading was successful!")
            self.start.Enable()

        self.Refresh()
        

        # --------------- AUDIO dialog ----------------------------------

class audio_downloader(wx.Dialog):
    def __init__(self, file_name, title="Set Title!"):
        wx.Dialog.__init__(self, None, -1, title)
        if (paths.get_platform() != "mac"):
            co = wx.ColourDatabase().Find("light grey")
            #print co
            #self.SetBackgroundColour(co)
            self.SetBackgroundColour("lightgrey")
        #print self.GetBackgroundColour()

        self.progress_prompt = wx.StaticText(self, -1, "Download progress:")
        self.gauge = wx.StaticText(self, -1, "")
            
        self.start = wx.Button(self, -1, "Start Download")
        self.cancel = wx.Button(self, -1, "Cancel Download")
        self.help_text = wx.StaticText(self, -1, "")
        
        grid = wx.FlexGridSizer(3 ,1, 5, 5)
        grid.Add(self.progress_prompt)
        grid.Add(self.gauge, flag=wx.EXPAND)
        grid.Add(self.help_text, flag=wx.EXPAND)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.AddStretchSpacer()
        buttons.Add(self.cancel)
        buttons.Add(self.start, flag=wx.LEFT, border=10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, flag=wx.ALL, border=10)
        sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

        self.start.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.on_start, self.start)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel)

        self.download_bytes, self.dtype, self.version = get_bytes(file_name)
        
        self.byte_count = len(self.download_bytes)
        
        self.gauge.SetLabel("")
        
        self.help_text.SetLabel("Download size is %d bytes" % (self.byte_count,))

        # convert to wav file
        WAV_FILE = os.path.join(paths.get_store_dir(), "program.wav")
        convertWithPause(self.download_bytes, WAV_FILE,
                         DOWNLOAD_PAUSE_MSECS, DOWNLOAD_BYTES_BETWEEN_PAUSES);
        
    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)


    def on_start(self, event):
        # can't start twice so disable this button
        self.start.Disable()
        self.cancel.Disable()
        self.help_text.SetLabel("Downloading %d bytes." % (self.byte_count,))

        self.gauge.SetLabel("...DOWNLOADING...")
            
        self.Update()

        time.sleep(1)
        WAV_FILE = os.path.join(paths.get_store_dir(), "program.wav")

        if USE_WAVER:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            logfile_path = os.path.join(tempfile.gettempdir(), "waver.log")
            logfile = open(logfile_path, "a+")
            logfile.seek(0, os.SEEK_END)
            waver_path = os.path.join(paths.get_run_dir(), "waver", "waver.exe")
            process = subprocess.Popen([waver_path, WAV_FILE], startupinfo=startupinfo, stdout=logfile)
            process.wait()
            logfile.close()

        elif USE_PORTAUDIO:
            wf = wave.open(WAV_FILE, 'rb')
            p = pyaudio.PyAudio()

            totalFrames = wf.getnframes()
            framesRead = 0
            self.gauge.SetRange(totalFrames)
            self.gauge.SetValue(0)
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)
            data = wf.readframes(47)
            framesRead += 47
            if (framesRead > totalFrames):
                framesRead = totalFrames
            stream.write(data)

            while data != '':
                stream.write(data)
                self.gauge.SetValue(framesRead)
                self.Update()

                data = wf.readframes(AUDIO_CHUNK)
                framesRead += AUDIO_CHUNK
                if (framesRead > totalFrames):
                    framesRead = totalFrames

            self.gauge.SetValue(totalFrames)
            self.Update()
            correction = float(stream.get_write_available() - 32)/sample_rate
            time.sleep(stream.get_output_latency() - correction)
            stream.stop_stream()
            stream.close()
            p.terminate()

        
        elif USE_PYGAME:
            if (pygame.mixer.get_init() == None):
                pygame.mixer.init(frequency=44100, size=8, channels=2, buffer=4096)
                pygame.mixer.init()
            
            s = pygame.mixer.Sound(WAV_FILE)
            seconds = s.get_length()
            #print "Sounds seconds:", seconds
            if (seconds < 1):
                seconds = 1
            self.gauge.SetRange(seconds * 5)
            self.gauge.SetValue(0)
            elapsed = 0
            s.play()
            while ((elapsed < seconds) and pygame.mixer.get_busy()):
                time.sleep(0.2)
                elapsed += 0.2
                if (elapsed < seconds):
                    self.gauge.SetValue(elapsed * 5)
                    self.Update()

            self.gauge.SetValue(seconds * 5)
            self.Update()
            
        self.gauge.SetLabel("")
            
        self.help_text.SetLabel("Finished downloading")
        self.start.Enable()
        self.cancel.Enable()

        self.Refresh()
        
        # --------------- AUDIO FIRMWARE dialog ----------------------------------
        
class audio_firmware_downloader(wx.Dialog):
    def __init__(self, file_name, title="Set Title!"):
        wx.Dialog.__init__(self, None, -1, title)
        if (paths.get_platform() != "mac"):
            self.SetBackgroundColour("light grey")

        self.progress_prompt = wx.StaticText(self, -1, "Download progress:")
        self.gauge = wx.StaticText(self, -1, "")

        self.start = wx.Button(self, -1, "Start Download")
        self.cancel = wx.Button(self, -1, "Cancel Download")
        self.help_text = wx.StaticText(self, -1, AUDIO_STRING)
        self.file_browse = fbb.FileBrowseButton(self, -1, labelText="Firmware File:",
                                                dialogTitle="Find a Firmware File",
                                                fileMode=wx.OPEN)
        if (paths.get_platform() != "mac"):
            self.file_browse.SetBackgroundColour("light grey")

        grid = wx.FlexGridSizer(4 ,1, 5, 5)
        grid.Add(self.file_browse, flag=wx.EXPAND)
        grid.Add(self.progress_prompt)
        grid.Add(self.gauge, flag=wx.EXPAND)
        grid.Add(self.help_text, flag=wx.EXPAND)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.AddStretchSpacer()
        buttons.Add(self.cancel)
        buttons.Add(self.start, flag=wx.LEFT, border=10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, flag=wx.ALL, border=10)
        sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

        self.start.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.on_start, self.start)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def on_start(self, event):
        filename = self.file_browse.GetValue()
        if (not os.path.exists(filename)):
            self.help_text.SetLabel("Error - couldn't read file: %s" % (filename,))
            return

        # Assuming that the file is the binary firmware file with all header bytes
        # already added. Just have to convert to audio and play.
        
        file_handle = file(filename, 'rb')
        firmware_string = file_handle.read()
        file_handle.close()
        self.download_bytes = bytearray(firmware_string)
        self.byte_count = len(self.download_bytes)
        
        self.gauge.SetLabel("")
            
        self.help_text.SetLabel("Creating audio file.")
        self.Update()
        FIRMWARE_WAV = os.path.join(paths.get_store_dir(), "firmware.wav")
        # convert to wav file
        convertWithPause(self.download_bytes, FIRMWARE_WAV,
                         DOWNLOAD_PAUSE_MSECS, DOWNLOAD_BYTES_BETWEEN_PAUSES);
        
        # can't start twice so disable this button
        self.start.Disable()
        self.cancel.Disable()
        self.help_text.SetLabel("Downloading %d bytes." % (self.byte_count,))

        self.gauge.SetLabel("...DOWNLOADING...")
            
        self.Update()

        time.sleep(1)
        if USE_WAVER:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            logfile_path = os.path.join(tempfile.gettempdir(), "waver.log")
            logfile = open(logfile_path, "a+")
            logfile.seek(0, os.SEEK_END)
            waver_path = os.path.join(paths.get_run_dir(), "waver", "waver.exe")
            process = subprocess.Popen([waver_path, FIRMWARE_WAV], startupinfo=startupinfo, stdout=logfile)
            process.wait()
            logfile.close()

        elif USE_PORTAUDIO:
            wf = wave.open(FIRMWARE_WAV, 'rb')
            p = pyaudio.PyAudio()

            totalFrames = wf.getnframes()
            framesRead = 0
            self.gauge.SetRange(totalFrames)
            self.gauge.SetValue(0)
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)
            data = wf.readframes(47)
            framesRead += 47
            if (framesRead > totalFrames):
                framesRead = totalFrames
            stream.write(data)

            while data != '':
                stream.write(data)
                self.gauge.SetValue(framesRead)
                self.Update()
                
                data = wf.readframes(AUDIO_CHUNK)
                framesRead += AUDIO_CHUNK
                if (framesRead > totalFrames):
                    framesRead = totalFrames

            self.gauge.SetValue(totalFrames)
            self.Update()
            correction = float(stream.get_write_available() - 32)/sample_rate
            time.sleep(stream.get_output_latency() - correction)
            stream.stop_stream()
            stream.close()

            p.terminate()

        elif USE_PYGAME:
            if (pygame.mixer.get_init() == None):
                pygame.mixer.init(frequency=44100, size=8, channels=2, buffer=4096)
                pygame.mixer.init()
            
            s = pygame.mixer.Sound(FIRMWARE_WAV)
            seconds = s.get_length()
            #print "Sounds seconds:", seconds
            if (seconds < 1):
                seconds = 1
            self.gauge.SetRange(seconds * 5)
            self.gauge.SetValue(0)
            elapsed = 0
            s.play()
            while ((elapsed < seconds) and pygame.mixer.get_busy()):
                time.sleep(0.2)
                elapsed += 0.2
                if (elapsed < seconds):
                    self.gauge.SetValue(elapsed * 5)
                    self.Update()

            self.gauge.SetValue(seconds * 5)
            self.Update()
            
        self.gauge.SetLabel("")

        self.help_text.SetLabel("Finished downloading")
        self.start.Enable()
        self.cancel.Enable()

        self.Refresh()

        
# --------------- Screen dialog ----------------------------------

class screen_downloader(wx.Dialog):
    def __init__(self, file_name, title="Set Title!", size=(500, 600)):
        wx.Dialog.__init__(self, None, -1, title, size=size)

        self.SetBackgroundColour("light grey")
        
        self.grid = wx.GridBagSizer(5,5)

        self.scr_prompt = wx.StaticText(self, -1, "Flash Box:")
        self.progress_prompt = wx.StaticText(self, -1, "Download progress:")

        self.canvas = wx.Window(self, -1, size=(300, 300), style=wx.SIMPLE_BORDER)
        self.canvas.SetBackgroundColour("white")
        
        self.gauge = wx.Gauge(self, -1, range=100)
        self.start = wx.Button(self, -1, "Start Download")
        self.cancel = wx.Button(self, -1, "Cancel Download")
        self.screen_text = wx.StaticText(self, -1, "Place the Line\ntracker in the\nmiddle of the \nFlash Box.")
        self.help_text = wx.StaticText(self, -1, "")

        self.grid.Add(self.scr_prompt, (1,2))
        self.grid.Add(self.canvas, (2,2), span=(2,2))
        self.grid.Add(self.screen_text, (2,4), span=(1,2))


        self.grid.Add(self.progress_prompt, (4,2), span=(1,3), flag=wx.EXPAND)
        self.grid.Add(self.gauge, (5,2), span=(1,3), flag=wx.EXPAND)
        
        self.grid.Add(self.help_text, (6,2), span=(1,3), flag=wx.EXPAND)
        
        self.grid.AddGrowableRow(7)
        self.grid.Add(self.cancel, (8,3), flag=wx.ALIGN_RIGHT | wx.BOTTOM)
        self.grid.Add(self.start, (8,4), flag=wx.ALIGN_LEFT | wx.BOTTOM)
        self.grid.Add((1,1), (9,2))

        self.SetSizer(self.grid)
        self.Layout()

        self.black_brush = wx.Brush("black")
        self.white_brush = wx.Brush("white")
        self.last_brush = None

        self.download_bytes, self.dtype, self.version = get_bytes(file_name)
        
        self.total_bytes = [0xff, 0xa1, 0x00]+self.download_bytes
        self.total_bytes[2] = (((self.version[0] & 0x0f) << 4) | (self.version[1] & 0x0f))

        self.byte_count = len(self.total_bytes)

        
        self.gauge.SetRange(self.byte_count)
        self.gauge.SetValue(0)

        self.help_text.SetLabel("Download size is %d bytes." % (self.byte_count,))

        self.start.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.on_start, self.start)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel)
        self.Bind(wx.EVT_TIMER, self.on_timeout)


    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_timeout(self, event):
        # 16 baud is every 62.5 milliseconds

        dc = wx.ClientDC(self.canvas)
        
        # get the bit to send
        if (self.bit_index == 8):
            # start bit
            brush = self.black_brush
            self.bit_index -= 1
            
        elif (self.bit_index < 0):
            # stop bit
            brush = self.white_brush
            self.byte_index += 1
            self.bit_index = 8

            
        else:
            if ((1 << self.bit_index) & self.total_bytes[self.byte_index]):
                brush = self.black_brush
            else:
                brush = self.white_brush
            self.bit_index -= 1
            
        # wait until precisely the time
        wait_cycles = 0
        while (datetime.datetime.today() < self.next_bit_time):
            wait_cycles += 1
        #print wait_cycles

        if (brush != self.last_brush):
            dc.SetBrush(brush)
            dc.DrawRectangle(0,0,300,300)
            self.last_brush = brush


        if (self.byte_index >= self.byte_count):
            # done!
            self.gauge.SetValue(self.byte_index)
            self.help_text.SetLabel("Finished Downloading!")
            self.start.Enable()
            
        elif (self.bit_index == 8):
            # add a bit of extra time between bytes
            self.next_bit_time += datetime.timedelta(microseconds=62500+20000)
            self.timer.Start(70, oneShot=True)
            
            self.gauge.SetValue(self.byte_index)
        
        else:
            self.next_bit_time += datetime.timedelta(microseconds=62500)
            self.timer.Start(50, oneShot=True)
            

    def on_start(self, event):
        self.timer = wx.Timer(self)
        self.next_bit_time = datetime.datetime.today() + datetime.timedelta(microseconds=20000)
        self.timer.Start(10, oneShot=True)
        self.byte_index = 0
        self.bit_index = 8
        self.last_brush = None
        
        # can't start twice so disable this button
        self.start.Disable()
        self.help_text.SetLabel("Downloading %d bytes." % (self.byte_count,))
        


# --------------- USB - firmware - dialog ----------------------------------


class firmware_downloader(wx.Dialog):
    def __init__(self, usb_device, file_name, title="Set Title!", size=(200, 200)):
        wx.Dialog.__init__(self, None, -1, title, size=(500, 300))
        self.SetBackgroundColour("light grey")

        # self.ports = get_possible_ports()
        # if (usb_device not in self.ports):
        #     if (len(self.ports) > 0):
        #         usb_device = self.ports[0]
        #     else:
        #         usb_device = ""
        usb_device = ""
                
        self.usb_ctrl = wx.ComboBox(self, -1, value=usb_device, choices=self.ports, size=(150,-1))

        self.grid = wx.GridBagSizer(5,5)

        self.usb_prompt = wx.StaticText(self, -1, "USB Device:")
        self.progress_prompt = wx.StaticText(self, -1, "Download progress:")
        #self.usb_ctrl = wx.TextCtrl(self, -1, value=usb_device, size=(200,-1))
        self.gauge = wx.Gauge(self, -1, range=100)
        self.start = wx.Button(self, -1, "Start Download")
        self.cancel = wx.Button(self, -1, "Cancel Download")
        self.help_text = wx.StaticText(self, -1, "")
        self.file_browse = fbb.FileBrowseButton(self, -1, labelText="Firmware File:",
                                                dialogTitle="Find a Firmware File",
                                                fileMode=wx.OPEN)
        self.file_browse.SetBackgroundColour("light grey")

        self.grid.Add(self.file_browse, (1,1), span=(1,3), flag=wx.EXPAND)
        self.grid.Add(self.usb_prompt, (2,1),
                 flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        self.grid.Add(self.usb_ctrl, (2,2), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL)


        self.grid.Add(self.progress_prompt, (4,1), span=(1,2), flag=wx.EXPAND)
        self.grid.Add(self.gauge, (5,1), span=(1,3), flag=wx.EXPAND)
        
        self.grid.Add(self.help_text, (6,1), span=(2,2), flag=wx.EXPAND)
        
        self.grid.AddGrowableRow(7)
        self.grid.Add(self.cancel, (8,2), flag=wx.ALIGN_RIGHT | wx.BOTTOM)
        self.grid.Add(self.start, (8,3), flag=wx.ALIGN_LEFT | wx.BOTTOM)
        self.grid.Add((1,1), (9,2))

        self.SetSizer(self.grid)
        self.Layout()

        self.start.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.on_start, self.start)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel)

    def get_port(self):
        return self.usb_ctrl.GetValue()


    def on_cancel(self, event):
        self.EndModal(1)


    def on_start(self, event):
        # get the device
        device = self.usb_ctrl.GetValue()

        filename = self.file_browse.GetValue()
        if (not os.path.exists(filename)):
            self.help_text.SetLabel("Error - couldn't read file: %s" % (filename,))
            return
        
        file_handle = file(filename, 'rb')
        firmware_string = file_handle.read()
        file_handle.close()

        prefix = token_downloader.SERIAL_WAKEUP_STR + token_downloader.FIRMWARE_STR
        prefix_len = len(prefix)

        while (firmware_string.startswith(token_downloader.PRE_WAKEUP_ONE)):
               firmware_string = firmware_string[len(token_downloader.PRE_WAKEUP_ONE):]
               
        if ((len(firmware_string) < prefix_len) or
            (not firmware_string.startswith(prefix))):
            self.help_text.SetLabel("Error - file doesn't seem to be firmware.")
            return
        
        version = ((ord(firmware_string[prefix_len])&0xf0)>>4,
                   ord(firmware_string[prefix_len])&0x0f)

        firmware_bytes = []
        for i in range(prefix_len+1, len(firmware_string)):
            firmware_bytes.append(ord(firmware_string[i]))
        self.byte_count = len(firmware_string)
        self.gauge.SetRange(self.byte_count)
        
        # can't start twice so disable this button
        self.start.Disable()
        self.help_text.SetLabel("Starting download of %d bytes." % (self.byte_count,))
        self.Update()

        result = token_downloader.gui_serial("firmware", version, firmware_bytes,
                                             device, self.help_text, self.gauge)

        if (not result):
            self.start.Enable()

        else:
            self.gauge.SetValue(self.byte_count)
            self.gauge.Update()

            self.help_text.SetLabel("Downloading was successful!")
            self.start.Enable()

        self.Refresh()


# --------------- USB - intex hex - dialog ----------------------------------

def just_hex_digits(in_string):
    for i in range(len(in_string)):
        char = in_string[i]
        if char not in string.hexdigits:
            #print "Invalid character (%02x) for an intel hex file!" % (ord(char),)
            return False
    return True
    
def hex_to_bin(file_handle):
    """Convert an intel-hex file into a binary string.
    This code only handles type 00 data records but does handle gaps and
    out of order records"""

    bytes = []
    error = ""
    data = []
    addresses = []
    
    for line in file_handle:
        #print line
        if ((len(line) < 11) or (line[0] != ':') or
            (line[7:9] not in ('00', '01', '02')) or
            (not just_hex_digits(line[1:11]))):
            error = "Doesn't look like an intel hex file"
        else:
            data_len = int(line[1:3], 16)
            address = int(line[3:7], 16)
            
            line_type = int(line[7:9], 16)
            check_sum = int(line[1:3], 16) + int(line[3:5], 16) + \
                        int(line[5:7], 16) + int(line[7:9], 16)

            if (line_type == 0):
                addresses.append((address, len(data), data_len))

            if (len(line) < (11+2*data_len)):
                error = "Line too short"
            else:
                index = 9
                for i in range(data_len+1):
                    if (not just_hex_digits(line[index:index+2])):
                        error = "Invalid digits"
                        break
                    else:
                        datum = int(line[index:index+2], 16)
                        check_sum += datum
                        if (i < data_len and line_type == 0):
                            data.append(datum)
                        else:
                            # checksum -- should be zero
                            if ((check_sum & 0xff) != 0):
                                error = "Checksum error"
                                break
                    index += 2

        if (error):
            print "Error in reading intel hex file:", error
            return (error, bytes)

    #print "Addresses:", addresses
    #print "Data:", data

    # sort the addresses and create a string
    addresses.sort(key=lambda x:x[0])
    last_index = addresses[0][0]
    for start, data_index, length in addresses:
        #print last_index, start, length, data_index
        while (last_index < start):
            bytes.append(0xff)
            last_index += 1

        for j in range(length):
            bytes.append(data[data_index+j])

        last_index = start+length

    #print "Bytes:", bytes
    #print "Length:", len(bytes)
    return (error, bytes) 

class hex_downloader(wx.Dialog):
    def __init__(self, usb_device, file_name, title="Set Title!", size=(200, 200)):
        wx.Dialog.__init__(self, None, -1, title, size=(500, 300))
        self.SetBackgroundColour("light grey")

        # self.ports = get_possible_ports()
        # if (usb_device not in self.ports):
        #     if (len(self.ports) > 0):
        #         usb_device = self.ports[0]
        #     else:
        #         usb_device = ""
        usb_device = ""
                
        self.usb_ctrl = wx.ComboBox(self, -1, value=usb_device, choices=self.ports, size=(150,-1))

        self.grid = wx.GridBagSizer(5,5)

        self.usb_prompt = wx.StaticText(self, -1, "USB Device:")
        self.progress_prompt = wx.StaticText(self, -1, "Download progress:")
        #self.usb_ctrl = wx.TextCtrl(self, -1, value=usb_device, size=(200,-1))
        self.gauge = wx.Gauge(self, -1, range=100)
        self.start = wx.Button(self, -1, "Start Download")
        self.cancel = wx.Button(self, -1, "Cancel Download")
        self.help_text = wx.StaticText(self, -1, "")
        self.file_browse = fbb.FileBrowseButton(self, -1, labelText="Intel Hex File:",
                                                dialogTitle="Find an Intel Hex File",
                                                fileMode=wx.OPEN,
                                                fileMask="Hex files (*.hex)|*.hex|All files (*.*)|*.*")
        self.file_browse.SetBackgroundColour("light grey")

        self.grid.Add(self.file_browse, (1,1), span=(1,3), flag=wx.EXPAND)
        self.grid.Add(self.usb_prompt, (2,1),
                 flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        self.grid.Add(self.usb_ctrl, (2,2), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL)


        self.grid.Add(self.progress_prompt, (4,1), span=(1,2), flag=wx.EXPAND)
        self.grid.Add(self.gauge, (5,1), span=(1,3), flag=wx.EXPAND)
        
        self.grid.Add(self.help_text, (6,1), span=(2,2), flag=wx.EXPAND)
        
        self.grid.AddGrowableRow(7)
        self.grid.Add(self.cancel, (8,2), flag=wx.ALIGN_RIGHT | wx.BOTTOM)
        self.grid.Add(self.start, (8,3), flag=wx.ALIGN_LEFT | wx.BOTTOM)
        self.grid.Add((1,1), (9,2))

        self.SetSizer(self.grid)
        self.Layout()

        self.start.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.on_start, self.start)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel)

    def get_port(self):
        return self.usb_ctrl.GetValue()


    def on_cancel(self, event):
        self.EndModal(1)


    def on_start(self, event):
        # get the device
        device = self.usb_ctrl.GetValue()

        filename = self.file_browse.GetValue()
        if (not os.path.exists(filename)):
            self.help_text.SetLabel("Error - couldn't read file: %s" % (filename,))
            return
        
        file_handle = file(filename, 'rb')
        read_error, data_bytes = hex_to_bin(file_handle)
        file_handle.close()

        if (read_error):
            self.help_text.SetLabel("Error on reading intel hex file: " + read_error)
            return
            
        version = (0, 0)
        download_bytes = [0, 0, 0, 0]
        download_bytes[0], download_bytes[1] = tokens.word_to_bytes(len(data_bytes))
        download_bytes[2], download_bytes[3] = tokens.word_to_bytes(tokens.calculate_crc(data_bytes))
        download_bytes.extend(data_bytes)
        
        self.byte_count = len(download_bytes)
        self.gauge.SetRange(self.byte_count)
        
        # can't start twice so disable this button
        self.start.Disable()
        self.help_text.SetLabel("Starting download of %d bytes." % (self.byte_count,))
        self.Update()

        result = token_downloader.gui_serial("firmware", version, download_bytes,
                                             device, self.help_text, self.gauge)

        if (not result):
            self.start.Enable()

        else:
            self.gauge.SetValue(self.byte_count)
            self.gauge.Update()
            self.help_text.SetLabel("Downloading was successful!")
            self.start.Enable()

        self.Refresh()


def convert(binString, outFilePath):
    #print "Debug: in convert() with binString of length", len(binString)
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
        
    while (index < len(binString)):
        data = binString[index]
        #print "..debug: coding value", data
        # add start
        waveWriter.writeframes(createAudio(6))
        
        # now the actual data -- big endian or little endian
        mask = 1
        ones = 0
        while (mask <= 0x80):
            if (data & mask):
                waveWriter.writeframes(createAudio(2))
                ones += 1
            else:
                waveWriter.writeframes(createAudio(0))
            mask <<= 1

        # add parity
        # if (ones % 2 == 1):
        #     # odd so need to add a one
        #     waveWriter.writeframes(createAudio(2))
        # else:
        #     # even so add a zero
        #     waveWriter.writeframes(createAudio(0))

        # add stop - BBB Changed to 8 - differs from start 
        waveWriter.writeframes(createAudio(8))

        index += 1

    #added to end as well - to ensure entrie data is played. - ## BBB
    preamble = 0    
    while (preamble < 20):
        waveWriter.writeframes(createAudio(0))
        preamble += 1

def waveFileLenInSeconds(waveFilePath):
    waveReader = wave.open(waveFilePath, 'rb')
    rate = waveReader.getframerate()
    frames = waveReader.getnframes()
    seconds = (frames / rate) + 1
    waveReader.close()
    #print "waveFileLenInSeconds - rate:%d, frames:%d, seconds:%d" % (rate, frames, seconds)
    return seconds

    
def convertWithPause(binString, outFilePath, pauseMsecs, bytesBetweenPauses):
    #print "Debug: in convert() with binString of length", len(binString)
    waveWriter = wave.open(outFilePath, 'wb')
    waveWriter.setnchannels(2)
    waveWriter.setsampwidth(1)
    p = pyaudio.PyAudio()
    sample_rate = int(p.get_default_output_device_info()['defaultSampleRate'])
    logfile_path = os.path.join(tempfile.gettempdir(), "waver.log")
    with open(logfile_path, "a") as logfile:
        logfile.writelines("{}\r\n".format(datetime.datetime.now()))
        import unicodedata
        for k, v in p.get_default_output_device_info().items():
            try:
                logfile.writelines("{}: {}\r\n".format(k, v))
            except UnicodeError:
                v = unicodedata.normalize('NFKD', v).encode('ascii','ignore')
                logfile.writelines("{}: {}\r\n".format(k, v))
    p.terminate()
    waveWriter.setframerate(sample_rate)
    waveWriter.setcomptype("NONE", "")

    # now generate the file
    index = 0
    preamble = 0
    pauseCount = 0

    # write silence in the begining
    waveWriter.writeframes(createAudio(1000, sample_rate, True))

    while (preamble < 20):
        waveWriter.writeframes(createAudio(0, sample_rate))
        preamble += 1
        
    while (index < len(binString)):
        if (pauseCount == bytesBetweenPauses):
            # insert more preamble -- one preamble is 1ms
            #print "Debug -- pausing for", pauseMsecs, "msecs, after", index, "bytes"
            preamble = 0
            while (preamble < pauseMsecs):
                waveWriter.writeframes(createAudio(0, sample_rate))
                preamble += 1
            pauseCount = 0
        
        data = binString[index]
        #print "..debug: coding value", data
        # add start
        waveWriter.writeframes(createAudio(6, sample_rate))
        
        # now the actual data -- big endian or little endian
        mask = 1
        ones = 0
        while (mask <= 0x80):
            if (data & mask):
                waveWriter.writeframes(createAudio(2, sample_rate))
                ones += 1
            else:
                waveWriter.writeframes(createAudio(0, sample_rate))
            mask <<= 1

        # add parity
        # if (ones % 2 == 1):
        #     # odd so need to add a one
        #     waveWriter.writeframes(createAudio(2))
        # else:
        #     # even so add a zero
        #     waveWriter.writeframes(createAudio(0))

        # add stop - BBB Changed to 8 - differs from start 
        waveWriter.writeframes(createAudio(8, sample_rate))

        index += 1
        pauseCount += 1

    #added to end as well - to ensure entire data is played. - ## BBB
    preamble = 0    
    while (preamble < 20):
        waveWriter.writeframes(createAudio(0, sample_rate))
        preamble += 1

    # write silence in the end
    waveWriter.writeframes(createAudio(1000, sample_rate, True))

    waveWriter.close()
        
def createAudio(midQuantas, sample_rate, silence=False):
    if sample_rate == 44100:
        sample_count = 22
    elif sample_rate == 48000:
        sample_count = 24
    data = ""
    
    if not silence:
        # write fars
        count = 0
        while (count < sample_count):
            data += chr(255) + chr(0)
            count += 1

        # write nears
        count = 0
        while (count < sample_count):
            data += chr(0) + chr(255)
            count += 1

    if (midQuantas > 0):
        count = 0
        samples = midQuantas * sample_count
        while (count < samples):
            data += chr(128) + chr(128)
            count += 1

    return data
        
            
