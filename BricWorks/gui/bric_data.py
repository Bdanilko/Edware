# * **************************************************************** **
#
# File: bric_data.py
# Desc: Data storage for bricss - bitmaps, help, etc.
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
# Svn: $Id: bric_data.py 50 2006-12-02 01:10:37Z briand $
# * **************************************************************** */

import os
import os.path
import ConfigParser

import wx
import wx.lib.imageutils

import win_data

BRIC_NORMAL = 0
BRIC_SELECTED = 1
BRIC_DISABLED = 2

# ----------------------

BRICS = "gui/brics"
BRIC_CONTROL = BRICS + "/control.ini"
BRICS_BIG = BRICS + "/big"
BRICS_SMALL = BRICS + "/small"


class Detail_parser(object):
    def __init__(self):
        pass

class Bric(Detail_parser):
    def __init__(self, cp_name, config_parser, basic=True):
        Detail_parser.__init__(self)
        self.cached_controls = False

        self.valid = False
        self.load(cp_name, config_parser, basic)

    def load(self, cp_name, cp, basic):
        try:
            self.helpfile = None
            if (cp.has_option(cp_name, 'helpfile')):
                self.helpfile = os.path.join(BRICS, cp.get(cp_name, 'helpfile'))

            self.name = cp.get(cp_name, 'name')
            self.group = cp.get(cp_name, 'group')
            self.help = cp.get(cp_name, 'help')
            if (self.help):
                self.help = self.help.replace('BLANKLINE', '')

            # get the bitmaps
            
            bmp = cp.get(cp_name, 'bmap')
            sbmp = cp.get(cp_name, 'selbmap')

            if (not sbmp):
                sbmp = "sel_"+bmp
                
            self.bmp = wx.Bitmap(os.path.join(BRICS, bmp), wx.BITMAP_TYPE_ANY)
            self.sbmp = wx.Bitmap(os.path.join(BRICS, sbmp), wx.BITMAP_TYPE_ANY)

            if (cp.has_option(cp_name, 'disbmap')):
                dbmp = cp.get(cp_name, 'disbmap')
                if (not dbmp):
                    dbmp = "dis_"+bmp
                self.dbmp = wx.Bitmap(os.path.join(BRICS, dbmp), wx.BITMAP_TYPE_ANY)
            else:
                image = wx.Image(os.path.join(BRICS, bmp))
                wx.lib.imageutils.grayOut(image)
                self.dbmp = wx.BitmapFromImage(image)

            # get the enabled function
            if (cp.has_option(cp_name, 'enable')):
                self.enable = enable_and_control_parser(cp.get(cp_name, 'enable'))
            else:
                self.enable = []

            self.valid = True
            
        except StandardError:
            raise
            self.valid = False
            print "Error loading", self.name

    def is_valid(self):
        return self.valid

    def clear_cache(self):
        self.cached = []

    def is_enabled(self, estr):
        
        if (self.enable[0] == 'D'):
            # check devices exist
            devices = self.enable[1:].split(';')

        
        result = eval(self.enable)
        return result
    
    def get_name_and_group(self):
        return (self.name, self.group)

    def get_bmap(self, version):
        if (version == BRIC_NORMAL):
            return self.bmp
        elif (version == BRIC_SELECTED):
            return self.sbmp
        elif (version == BRIC_DISABLED):
            return self.dbmp
        else:
            raise KeyError, "Bmap version out of range"

    def get_help(self):
        return self.help

    def get_detail(self):
        return self.detail

class Data(object):
    def __init__(self):
        self.groups = []
        self.brics = []
        self.bric_dict = {}

data = Data()


# ---------------------------------------------------------
# Bric data

# two sizes - big and not-big (small)
def load_brics(big = True):
    global data

    base = BRICS
        
    cp = ConfigParser.RawConfigParser()
    cp.read(BRIC_CONTROL)

    data.groups = []

    data.brics = []
    data.bric_dict.clear()

    # get the top bric number
    topBricNumber = cp.getint('control', 'highbric')
    
    # get the arrows
    larrow = cp.get('arrow', 'left')
    rarrow = cp.get('arrow', 'right')
    slarrow = cp.get('arrow', 'selleft')
    srarrow = cp.get('arrow', 'selright')

    if (not srarrow):
        srarrow = 'sel_'+rarrow
        
    if (not slarrow):
        slarrow = 'sel_'+larrow

    data.right_arrow = (wx.Bitmap(os.path.join(base, rarrow), wx.BITMAP_TYPE_ANY),
                       wx.Bitmap(os.path.join(base, srarrow), wx.BITMAP_TYPE_ANY))
    data.left_arrow = (wx.Bitmap(os.path.join(base, larrow), wx.BITMAP_TYPE_ANY),
                       wx.Bitmap(os.path.join(base, slarrow), wx.BITMAP_TYPE_ANY))

    # get the end bmap
    end_name = cp.get('end', 'bmap')
    end_sel = cp.get('end', 'selbmap')
    if (not end_sel):
        end_sel = 'sel_'+end_name

    data.end_bmaps = (wx.Bitmap(os.path.join(base, end_name), wx.BITMAP_TYPE_ANY),
                       wx.Bitmap(os.path.join(base, end_sel), wx.BITMAP_TYPE_ANY))
    
    b_name = 'new'
    bmp = cp.get(b_name, 'bmap')
    sbmp = cp.get(b_name, 'selbmap')
    if (not sbmp):
        sbmp = "sel_"+bmp

    data.new = (wx.Bitmap(os.path.join(base, bmp), wx.BITMAP_TYPE_ANY),
                wx.Bitmap(os.path.join(base, sbmp), wx.BITMAP_TYPE_ANY))

        
    group = 1
    while True:
        g_name = 'group%d' % (group)
        if (cp.has_section(g_name)):
            expname = cp.get(g_name, 'expbmap')
            colname = cp.get(g_name, 'colbmap')
            
            g_tuple = (cp.get(g_name, 'name'),
                       wx.Bitmap(os.path.join(base, expname), wx.BITMAP_TYPE_ANY),
                       wx.Bitmap(os.path.join(base, colname), wx.BITMAP_TYPE_ANY),)
            
            data.groups.append(g_tuple)
        else:
            break
        group += 1

    bric = 1
    while bric <= topBricNumber:
        b_name = 'bric%d' % (bric)
        if (cp.has_section(b_name)):
            new_bric = Bric(b_name, cp)
            
            if (new_bric.is_valid()):
                name_and_group = new_bric.get_name_and_group()
                data.brics.append(name_and_group)
                data.bric_dict[name_and_group[0]] = new_bric
        bric += 1

    # load ifs
    data.if_variants = {}

    get_if_variant(cp, "bumper")
    get_if_variant(cp, "analogin")
    get_if_variant(cp, "digin")
    get_if_variant(cp, "irrx")
    get_if_variant(cp, "tracker")

    # specials
    get_if_variant(cp, "button")
    get_if_variant(cp, "pulse")
    get_if_variant(cp, "light")
    get_if_variant(cp, "remote")
    get_if_variant(cp, "serial")
    get_if_variant(cp, "timer")
    get_if_variant(cp, "var")


def get_if_variant(cp, name):
    normal = cp.get('ifs', name)+'.png'
    selected = cp.get('ifs', name)+'_selected.png'

    data.if_variants[name] = (wx.Bitmap(os.path.join(BRICS, normal), wx.BITMAP_TYPE_ANY),
                              wx.Bitmap(os.path.join(BRICS, selected), wx.BITMAP_TYPE_ANY))


def get_if_bmap(name, selected=False):
    if (name not in data.if_variants):
        name = 'var'
        
    if (selected):
        return data.if_variants[name][1]
    else:
        return data.if_variants[name][0]
        
    
def get_groups():
    return data.groups

def get_brics():
    return data.brics

def get_bric_bmap(name, version=BRIC_NORMAL):
    return data.bric_dict[name].get_bmap(version)

def get_new_bmap(selected=False):
    if (selected):
        return data.new[1]
    else:
        return data.new[0]

def get_bric_help(name):
    return data.bric_dict[name].get_help()

def is_enabled(name):
    return enable_check(data.bric_dict[name].enable)

def is_control_enabled(ctrl_enable):
    return enable_check(ctrl_enable)


def get_bric_detail(name):
    return data.bric_dict[name].get_detail()


def get_arrow_bmap(right=True, sel=False):
    if (sel):
        which = 1
    else:
        which = 0
        
    if (right):
        return data.right_arrow[which]
    else:
        return data.left_arrow[which]

def get_end_bmap(sel=False):
    if (sel):
        which = 1
    else:
        which = 0
        
    if (right):
        return data.end_bmaps[which]
    else:
        return data.end_bmaps[which]
    

# ---------------------------------------------------------

def enable_and_control_parser(str):
    pieces = []
    i = 0
    while (i < len(str)):
        etype = str[i]
        args = []
        i += 1
        if (i < len(str) and
            str[i] == '('):
            # arguments for this one
            end = str.find(')',i)
            if (end <= 0):
                raise SyntaxError, "Error in enable_and_control_parser parsing "+str

            args = []
            for a in str[i+1:end].split(';'):
                args.append(arg_condition(a))
            
            i = end + 1
        pieces.append((etype, args))

    #print pieces
    return pieces

def arg_condition(arg):
    d = arg.strip()
    if (len(d) >= 2 and ((d[0] == '"' and d[-1] == '"') or
                         (d[0] == "'" and d[-1] == "'"))):
        d = d[1:-1]
    return d

def enable_check(enable_list):
    for etype, args in enable_list:
        #print etype,args
        if (etype == 'D'):
            found_one = False
            for d in args:
                if (win_data.config_device_used(d)):
                    found_one = True
                    break
            if (not found_one):
                return False
        elif (etype == 'A'):
            if (not win_data.get_adv_mode()):
                return False
        elif (etype == 'P'):
            if (not win_data.config_motor_pairs()):
                return False
        elif (etype == 'V'):
            if (not win_data.vars_defined()):
                return False
        elif (etype == 'U'):
            if (not win_data.vars_defined('0-255')):
                return False
        elif (etype == 'S'):
            if (not win_data.vars_defined('+/- 32767')):
                return False
        else:
            raise SyntaxError, 'Unknown enable type: ' + etype

    return True




# ---------------------------------------------------------

# Test
if (__name__ == '__main__'):
##    global BRICS, DEVICE_CONTROL, BRICS_BIG, BRICS_SMALL
##    BRICS = "brics"
##    BRIC_CONTROL = BRICS + "/control.ini"
##    BRICS_BIG = BRICS + "/big"
##    BRICS_SMALL = BRICS + "/small"

    enable_and_control_parser('AVD(Motor A;Motor B)U("this is fun")')
    #load_brics()
##    print data.groups
##    print data.brics
##    print data.bric_dict
    
