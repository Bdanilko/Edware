# * **************************************************************** **
#
# File: device_data.py
# Desc: Data storage for devices - bitmaps, help, etc.
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
# Svn: $Id: device_data.py 50 2006-12-02 01:10:37Z briand $
# * **************************************************************** */

import os
import os.path
import ConfigParser

import wx
import paths

class Data(object):
    def __init__(self):
        self.mb_bmap = None
        self.mb_overlay = None
        self.overlays = []
        
        self.groups = []
        self.devices = []
        self.device_dict = {}
        self.fullsize_dict = {}

data = Data()


DEVICES = os.path.join(paths.get_run_dir(), "gui/devices")
DEVICE_CONTROL = DEVICES + "/control.ini"
DEVICES_BIG = DEVICES + "/big"
DEVICES_SMALL = DEVICES + "/small"

# ---------------------------------------------------------
# Device data

# two sizes - big and not-big (small)
def load_devices(big = True):
    global data
    if (big):
        base = DEVICES_BIG
    else:
        base = DEVICES_SMALL
    base = DEVICES
        
    cp = ConfigParser.RawConfigParser()
    cp.read(DEVICE_CONTROL)

    #data.mb_bmap = wx.Bitmap(os.path.join(base, cp.get('motherboard', 'bmap')), wx.BITMAP_TYPE_ANY)
    data.mb_bmap = ""
    data.groups = []
    data.devices = []
    data.device_dict.clear()
    data.fullsize_dict.clear()

    # do the overlays
    #data.mb_overlay = wx.Bitmap(os.path.join(base, cp.get('motherboard', 'overlay')), wx.BITMAP_TYPE_ANY)
    data.mb_overlay = ""
    data.overlays = []
    
    for i in range(12):
        name = "overlay%d" % (i,)
        #overlay = wx.Bitmap(os.path.join(base, cp.get('motherboard', name)), wx.BITMAP_TYPE_ANY)
        overlay = ""
        data.overlays.append(overlay)
        
    group = 1
    while True:
        g_name = 'group%d' % (group)
        if (cp.has_section(g_name)):
            expname = cp.get(g_name, 'expbmap')
            colname = cp.get(g_name, 'colbmap')
            
            # g_tuple = (cp.get(g_name, 'name'),
            #            wx.Bitmap(os.path.join(base, expname), wx.BITMAP_TYPE_ANY),
            #            wx.Bitmap(os.path.join(base, colname), wx.BITMAP_TYPE_ANY),)
            g_tuple = (cp.get(g_name, 'name'), "", "",)
            data.groups.append(g_tuple)
            
        else:
            break
        group += 1

    device = 1
    while True:
        d_name = 'device%d' % (device)
        if (cp.has_section(d_name)):
            helpfile = None
            if (cp.has_option(d_name, 'helpfile')):
                helpfile = os.path.join(DEVICES, cp.get(d_name, 'helpfile'))
            
            d_tuple = (cp.get(d_name, 'name'), cp.get(d_name, 'group'))
            data.devices.append(d_tuple)

            bmp_name = cp.get(d_name, 'bmap')
            sbmp_name = cp.get(d_name, 'selbmap')

            if (not sbmp_name):
                sbmp_name = "sel_"+bmp_name
                
            # bmp = wx.Bitmap(os.path.join(base, bmp_name), wx.BITMAP_TYPE_ANY)
            # sbmp = wx.Bitmap(os.path.join(base, sbmp_name), wx.BITMAP_TYPE_ANY)
            bmp = ""
            sbmp = ""

            data.device_dict[cp.get(d_name, 'name')] = (bmp, sbmp, cp.get(d_name, 'help'))

            fsnname = cp.get(d_name, 'fsnbmap')
            fssname = cp.get(d_name, 'fssbmap')
            if (not fsnname):
                fsnname = "fsn_"+bmp_name
            if (not fssname):
                fssname = "fss_"+bmp_name
                
            # f_tuple = (wx.Image(os.path.join(base, fsnname), wx.BITMAP_TYPE_ANY),
            #            wx.Image(os.path.join(base, fssname), wx.BITMAP_TYPE_ANY),)
            f_tuple = ("", "")

            if (cp.has_option(d_name, 'fsncorner')):
                crnname = cp.get(d_name, 'fsncorner')
                crsname = cp.get(d_name, 'fsscorner')
                cr2nname = cp.get(d_name, 'fsncorner2')
                cr2sname = cp.get(d_name, 'fsscorner2')
                # f_tuple = (wx.Image(os.path.join(base, fsnname), wx.BITMAP_TYPE_ANY),
                #            wx.Image(os.path.join(base, fssname), wx.BITMAP_TYPE_ANY),
                #            wx.Image(os.path.join(base, crnname), wx.BITMAP_TYPE_ANY),
                #            wx.Image(os.path.join(base, crsname), wx.BITMAP_TYPE_ANY),
                #            wx.Image(os.path.join(base, cr2nname), wx.BITMAP_TYPE_ANY),
                #            wx.Image(os.path.join(base, cr2sname), wx.BITMAP_TYPE_ANY),)
                f_tuple = ("", "", "", "", "", "")

            data.fullsize_dict[cp.get(d_name, 'name')] = f_tuple
            
        else:
            break
        device += 1


def get_groups():
    return data.groups

def get_devices():
    return data.devices

def get_mb_bmap():
    return data.mb_bmap

def get_overlay_bmap(selected=None):
    if (selected == None):
        return data.mb_overlay
    else:
        return data.overlays[selected]

def get_device_bmap(name, selected=False):
    #print "get_device_bmap:", name
    if (selected):
        #print "Getting selected", name
        return data.device_dict[name][1]
    else:
        return data.device_dict[name][0]

def get_fullsize_image(name, index):
    return data.fullsize_dict[name][index]

def get_device_size():
    return data.device_dict[data.devices[0][0]][0].GetSize()

def get_device_help(name):
    return data.device_dict[name][2]


# ---------------------------------------------------------
# Test
if (__name__ == '__main__'):
##    global DEVICES, DEVICE_CONTROL, DEVICES_BIG, DEVICES_SMALL
##    DEVICES = "devices"
##    DEVICE_CONTROL = DEVICES + "/control.ini"
##    DEVICES_BIG = DEVICES + "/big"
##    DEVICES_SMALL = DEVICES + "/small"
    
    load_devices()
    print data.groups
    print data.devices
    print data.device_dict
    
