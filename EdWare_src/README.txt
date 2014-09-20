# * **************************************************************** **
#
# File: README.txt
# Desc: Readme file
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
# Svn: $Id: README.txt 51 2006-12-02 01:14:52Z briand $
# * **************************************************************** */

29/Jun/2014 -- THIS FILE IS OUT OF DATE -- WILL BE UPDATED BEFORE EDWARE VERSION 1.0

Microbric Bric Works
---------------------
This program will enable you to:
- create programs for basic or advanced (firmware versions 0.0 and 1.0) robots
- download programs to the robot using the screen or a USB cable
- upgrade firmware in the robot


Open source
-----------
This program is released under the GNU General Public License version 2 (see the full 
in file gpl.txt) which allows (even encourages) you to learn from and modify
the source to suit your own needs. 

All of the licenses that govern other components of this program are included in this directory.

Building or Compiling
---------------------
You don't need to. Python is an interpreted language.

Installing
----------

For Windows:
------------
If this is the first time use the 'full' installer (e.g. bricworks-full-1.0.exe).
(while installing other components, the default answers to questions are usually fine) 

If this is a reinstall, or a new version, then just run the update installer
(e.g. bricworks-update-1.0.exe)

For Linux:
----------
The prerequisites MAY need to be installed first if they aren't already part of
your Linux distribution. Then the bricworks tarball can be untarred in a directory
and then your ready to go!
(by running bricworks.py in the directory where you untarred the tarball).

The prerequisties are:
Python (tested on version 2.4.3) - http://www.python.org
wxPyton (tested on version 2.6.3.2) - http://www.wxpython.org
pySerial (tested on version 2.2) - http://pyserial.sourceforge.net


Getting Source
--------------
Python, being interpreted, is its own source. You've got it already.
For other components you can either go to the web address in the about box,
or check the Microbric site (http://www.microbric.com/ai2)


Documentation
-------------
As this program was created under strict time and resources constraints, it was decided
to create more functionality at the expense of (almost all) documentation. This decision
was made slightly easier since all of the code is in Python which is relatively easy to
read.

The interface to the robot interpreter is documented though.

Whats in the files:

- bricworks.py
  Starts the main graphical program and handles the menu and toolbar.
  Can take an .mbw file as an argument which will cause it to open that file directly.

- tass.py
  A command line assembler which turns a higher level language into robot interpreter tokens.
  The file: token_assembler.txt in this directory describes the higher level language.
  The file: tokens1.html in this directory describes the interpreter tokens (though it is
  only 90% correct / implemented)!
  Try 'python tass.py --help'

- gui/token_assembler.py, gui/hl_parser.py, gui/token_downloader.py, gui/tokens.py
  gui/logging_uitls.py
  Files needed for assembling and downloading higher level language to the robot.

- gui/downloader.py
  Used for the interface between the graphical program and downloading to the robot.

- gui/comscan.py
  Used for finding all active serial ports for the cable downloader. This file is
  copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>. The license file is
  in this directory (bitpim_LICENSE.txt).

- gui/devices directory
  Contains all of the graphics for the modules and an ini file containing basic help.
  All files in this directory (like all others except comscan.py) are copyright 2006 Microbric Pty Ltd
  and released under the GNU General Public License version 2

- gui/brics directory
  Contains all of the graphics for the programming blocks and an ini file containing basic help.
  All files in this directory (like all others except comscan.py) are copyright 2006 Microbric Pty Ltd
  and released under the GNU General Public License version 2

- gui/about.py
  A basic about box.

- gui/bric_data.py, gui/device_data.py
  Loads up all of the graphics and help text for the modules and programming blocks.

- gui/var_win.py, gui/config_win.py, gui/help_win.py
  Controls the simple windows (var, modules, help) in the gui.

- gui/pallete_win.py, gui/config_pallete.py, gui/progam_pallete.py
  Controls the leftmost window and drops into the main work area.

- gui/work_win.py, gui/config_work.py, gui/program_work.py
  Controls the manipulation of the device configuration and the programs
  in the main window on the screen

- gui/win_data.py
  Keeps the main state of the program and configuration. Responsible for saving and
  loading programs.

- gui/program_data.py
  Keeps a full program and handles changes (additions/moves/deletes) of program blocks
  in the program. Also responsible for the really hairy code which lays out the nested
  ifs (wish I could have documented that, sigh!)


Enjoy,
Brian Danilko, Likeable Software, 19 October, 2006
brian@likeablesoftware.com









