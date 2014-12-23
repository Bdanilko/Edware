# * **************************************************************** **
#
# File: paths.py
# Desc: Paths which handle being frozen or not
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
import os
import os.path

FROZEN = getattr(sys, 'frozen', False)

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

if FROZEN:
    RUN_DIR = sys._MEIPASS
else:
    RUN_DIR = os.getcwd()

# find the session writing directory
path = '~'
new_path = os.path.expanduser(path)
if (new_path == path):
    # didn't work, will have to just try to use the current directory
    STORE_DIR = '.'
else:
    STORE_DIR = new_path

print "Platform:", PLATFORM, ", Frozen:", FROZEN, ", Run_dir:", RUN_DIR, ", Store_dir:", STORE_DIR

def is_frozen():
    return FROZEN

def get_platform():
    return PLATFORM

def get_run_dir():
    return RUN_DIR

def get_store_dir():
    return STORE_DIR

def set_store_dir(newStoreDir):
    STORE_DIR = newStoreDir
