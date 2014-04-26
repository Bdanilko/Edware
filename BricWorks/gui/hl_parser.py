#!/usr/bin/env python


# * **************************************************************** **
#
# File: hl_parser.py
# Desc: high-level language parsing for the token assembler
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
# Svn: $Id: hl_parser.py 50 2006-12-02 01:10:37Z briand $
# * **************************************************************** */

import logging
import logging_utils

import string
import shlex

import tokens

device_types = {  #'not used':0,
                'digin':1, 'digout':2, 'analogin':3,
                'tracker':4, 'irtx':5, 'irrx':6, 'beeper':7, 'motor-a':8, 'motor-b':9,
                'led':0xa, 'bumper':0xb}

# Amount of ram to store the registers and work space for the interpreter
device_storage = {
    'digin':4+0, 'digout':5+0, 'analogin':2+0,
    'tracker':4+0, 'irtx':2+0, 'irrx':5+0, 'beeper':7+0,
    'motor-a':1+4, 'motor-b':1+4, 'led':2+0, 'bumper':1+0}

special_names = ['_index', '_devices', '_timers', '_cpu']
special_dtypes = ['index', 'devices', 'timers', 'cpu']


reset_devices = {'_index': ('index',12), '_devices':('devices', 13),
                 '_timers' : ('timers',14), '_cpu':('cpu', 15)}

reset_locations = {'c': ('index',12), 'd':('devices', 13),
                   'e' : ('timers',14), 'f':('cpu', 15)}

devices = {}

locations = {}

registers = {
                'digin' : {'status' : (0, 1), 'action':(1,1), 'pulsetime':(2,2)},
                'digout' : {'status' : (0,1), 'action':(1,1), 'output':(2,1), 'pulsetime':(3,2)},
                'analogin' : {'level' : (0,2)},
                'tracker' : {'status' : (0,1), 'output':(1,1), 'level':(2,2)},
                'beeper' : {'status':(0,1), 'action' : (1,1), 'freq' : (2,2),
                            'duration' : (4,2), 'tune' : (6,1)},
                'irtx' : {'action':(0,1), 'char':(1,1)},
                
                'irrx' : {'status' : (0,1), 'action':(1,1), 'check':(2,1), 'match':(3,1), 'char':(4,1)},
                'motor-a' : {'control':(0,1)},
                'motor-b' : {'control':(0,1)},
                
                'bumper' : {'status' : (0, 1)},
                'led' : {'status' : (0,1), 'output':(1,1)},


                'index' : {'action':(0,1), '8b1cursor':(1,1), '8b1step':(2,1),
                           '8b1window':(3,1), '8b2cursor':(4,1), '8b2step':(5,1),
                           '16b1cursor':(6,1), '16b1step':(7,1),
                           '16b1window':(8,2), '16b2cursor':(10,1), '16b2step':(11,1)},
                
                'devices' : {'status' : (0,1), 'action':(1,1), 'lcdaction':(2,1),
                             'serset1' : (3,1), 'serset2' : (4,1), 'serrx':(5,1),
                             'sertx':(6,1), 'lcdbyte':(7,1), 'lcdrp':(8,1),
                             'lcdcp':(9,1), 'lcdword':(10,2), 'random':(12,1),
                             'button':(13,1)},
                
                'timers' : {'status' : (0,1), 'action':(1,1), 'pause':(2,2),
                            'oneshot':(4,2), 'system':(6,4)},
                'cpu' : {'acc':(0,2), 'flags':(2,1), 'counter':(3,1),
                         'pc':(4,2), 'sp':(6,1), 'cow':(7,1)},
                }


import copy
def reset_devices_and_locations():
    global devices
    global locations
    devices.clear()
    locations.clear()
    devices = copy.deepcopy(reset_devices)
    locations = copy.deepcopy(reset_locations)

def dump_reg_help():
    """Dump locations, type names and register names as a help to programmers"""
    print "\nLocations:"
    print "  0-b : connectable module (use hex digit or name from DEVICE statement)"
    for i in 'cdef':
        name = locations[i][0]
        print "  %s   : special module %s (use hex digit or '%s')" % (i, name, name)

    print "\nDevice types (prefixed with device code):"
    olist = device_types.items()
    olist.sort(key=lambda p:p[1])
    count = 0
    print "  ",
    for name,num in olist:
        print "%d:%-10s " % (num, name),
        count += 1
        if (count >= 5):
            print "\n  ",
            count = 0
    if (count != 0): print

    print "\nRegister names (offset/bytes):"
    rorder = [name for (name, num) in olist]
    rorder.extend(special_dtypes)
    #print rorder

    for r in rorder:
        reg_dict = registers[r]
        rlist = reg_dict.items()
        rlist.sort(key=lambda p:p[1][0])
        #print rlist
        print "  %s" % (r),
        count = 10
        for (name, (offset, size)) in rlist:
            count += 1
            if count >= 4:
                print "\n    ",
                count = 0
            desc = "%s:(%s/%d)" % (name, string.hexdigits[offset], size),
            print "%-16s" % (desc),
            
        print
        print
        
                
err = None

def set_err_reporter(err_):
    global err
    err = err_

def add_device(loc, dtype, name=None):
    global devices
    global locations
    
    if (dtype not in device_types):
        err.report_error("Unknown device type: "+dtype)
        return False
    if (loc < 0 or loc > 11):
        err.report_error("Location (%d) outside of 0 to 11" % (loc))
        return False

    # location already used?
    loc_hex = string.hexdigits[loc]
    if (loc_hex in locations):
        err.report_error("Location (%d) is already used with a unit of type: " % (loc) +\
                         locations[loc_hex][0])
        return False

    if (name):
        name = name.lower()
        
    if (name in special_names):
        err.report_error("DEVICE name can not be one of the built-in names "+str(special_names))
        return False
    elif (name in devices):
        err.report_error("DEVICE name already used: "+name)
        return False
    
    # check the special ones - tracker and motors
    if (dtype == 'tracker' and loc != 0):
        err.report_error("A tracker device can only be located at 0, not location %d" % (loc))
        return False

    # motors need two spots
    if (dtype == 'motor-a' or dtype == 'motor-b'):
        if (loc == 11):
            motor_second_loc = 0
        else:
            motor_second_loc = loc+1
        motor_second_hex = string.hexdigits[motor_second_loc]
        if (motor_second_hex in locations):
            err.report_error("Motors require two locations yet the second location is already used with a "+\
                             locations[motor_second_hex][0])
            return False
        locations[motor_second_hex] = ('motor_second', motor_second_loc)

    locations[loc_hex] = (dtype, loc)

    # does it have a name?
    if (name):
        devices[name] = (dtype, loc)

    return True

def get_location_type_and_size(location):
    loc_hex = string.hexdigits[location]
    if (loc_hex in locations and locations[loc_hex][0] != 'motor_second'):
        dtype = locations[loc_hex][0]
        return (device_types[dtype], device_storage[dtype])
    else:
        return (0, 0)                   # Not used

def dump_devices():
    print "\nDevice mappings:"
    for i in range(12):
        loc_hex = string.hexdigits[i]
        if (loc_hex in locations):
            print "  %s - type:%s" % (loc_hex, locations[loc_hex][0]),
            for d in devices:
                if (devices[d][1] == i):
                    print ", name:%s" % (d),
                    break
            print
    

class word(object):
    def __init__(self, type, value):
        self.type_ = type
        self.value_ = value

    def type(self):
        return self.type_
    
    def val(self):
        return self.value_

    def num(self):
        return parse_bases(self.value_)

    def anum(self):
        if (self.type_ not in ["arg", "const"]):
            err.report_error("Expected an argument or constant!")
            return 0
        
        if (self.type_ == "const"):
            return self.value_
        else:
            return parse_bases(self.value_)

    def astr(self):
        if (self.type_ not in ["arg", "string"]):
            err.report_error("Expected an argument or string!")
            return ""
        elif (len(self.value_) > 0):
            if (self.value_[0] not in string.ascii_letters+'_'):
                err.report_error("Word should have been a valid name!")
                return ""
            else:
                return self.value_

    def amodreg(self):
        if (self.type_ not in ["arg", "modreg"]):
            err.report_error("Expected an argument or string!")
            return ""

        elif (self.type_ == "modreg"):
            return self.value_
        else:
            return parse_mod_reg(self.value_)
                  
    def __str__(self):
        return "{Word: %s,%s}" % (self.type_, self.value_)


def format_word_list(wlist):
    output = "["
    for w in wlist:
        output += str(w) + ", "
    if (wlist):
        output = output[:-2]
    output += "]"
    return output



# local utility functions

def parse_bases(snum, string=False):
    """detect the base and return a decimal equivalent"""
    if (snum.startswith("'") and snum.endswith("'")):
        # must be one ascii character
        num = ord(snum[1:-1])
    elif (string and snum.startswith('"') and snum.endswith('"')):
        err.report_error("Error - use single quotes for an ascii constant")
        return
    elif ((snum.endswith("/2"))):
        num = int(snum[:-2], 2)
    elif ((snum.endswith("/10"))):
        num = int(snum[:-3], 10)
    elif ((snum.endswith("/16"))):
        num = int(snum[:-3], 16)
    else:
        num = int(snum, 0)

    return num


def parse_mod_reg(smodreg):
    #print "parse_mod_reg():", smodreg
    #dump_devices()
    if ((len(smodreg) == 2) and
        (smodreg[0] in string.hexdigits) and
        (smodreg[1] in string.hexdigits)):
        num = int(smodreg, 16)
    else:
        if (':' in smodreg):
            part = smodreg.lower().split(':', 2)
            if (len(part) != 2):
                err.report_error("Invalid mod/reg syntax: "+smodreg)
                return ""
            if (part[0] in devices):
                dtype = devices[part[0]][0]
                loc = devices[part[0]][1]
            elif (part[0] in locations):
                dtype = locations[part[0]][0]
                loc = locations[part[0]][1]
            else:
                err.report_error("Didn't understand the module name/number: " + part[0])
                return ""

            # now the register name/number
            regs = registers[dtype]
            if (part[1] in regs):
                num = regs[part[1]][0] + (loc << 4)
            elif (part[1] in '0123456789abcdef'):
                num = int(part[1], 16) + (loc << 4)
            else:
                err.report_error("Didn't understand the register name/number: " + part[1])
                return ""
                
        else:
            err.report_error("Error - can't parse %s as a modreg" % (smodreg))
            return

    #print "modreg: %s -> %02x" % (smodreg, num)
    return num


def prechop_line(line):
    """Handle strings and comments"""
    in_string = ''
    in_escape = False
    components = []
    comp = ""
    
    for c in line:
        if (c == '\n'):
            break
        
        if (in_escape):
            comp += c
            in_escape = False
            
        elif (in_string and c == '\\'):
            in_escape = True
        
        elif (c == '#' and not in_string):
            # comment from here to end of line - bail out now
            break

        elif (not in_string and c in ['"']):
            in_string = c
            comp += c

        elif (in_string and c == in_string):
            in_string = ''
            comp += c

        elif (not in_string and c in [' ', '\t', ',']):
            if (comp):
                components.append(comp)
            comp = ''

        else:
            comp += c
        
    if (comp):
        components.append(comp)

    return components

        
    
def chop_line(line):
    """Filter out comments then create words from the line"""
            
##    segs_spaces = line.split()
##    segs = []
##    for ss in segs_spaces:
##        segs.extend(ss.split(","))

    segs = prechop_line(line)
    #print segs
    
    words = []
    for s in segs:
        # skip empty segs
        if not s:
            continue

        # terminate at a comment
        if (s.startswith('#')):
            break

        # lines can start with a label or operator
        if (s.startswith(":")):
            # a jump label
            words.append(word("label", s[1:]))

        elif (not words):
            # first one so must be the operator
            words.append(word("op", s))

        elif ((s.startswith('"') and s.endswith('"')) or
              (s.startswith("'") and s.endswith("'"))):
            if (len(s) <= 2):
                continue
            else:
                words.append(word("string", s[1:-1]))
                
        elif (s.startswith("$")):
            # should be a constant
            if (len(s) == 4 and s[1] == "'" and s[3] == "'"):
                num = ord(s[2])
            else:
                num = parse_bases(s[1:])
            words.append(word("const", num))

        elif (s.startswith("%")):
            # a module/register
            modreg = parse_mod_reg(s[1:])
            words.append(word("modreg", modreg))

        elif (s.startswith(":")):
            # a jump label
            words.append(word("label", s[1:]))

        elif (s.startswith("@")):
            # a variable name - add another element to the word
            words.append(word("var", s[1:]))
            
        else:
            words.append(word("arg", s))
            

    #print words
    return words
    

