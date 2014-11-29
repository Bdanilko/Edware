# * **************************************************************** **
#
# File: win_data.py
# Desc: Classes to facilitate messages between windows and classes
#       to enforce interfaces (interface mixin)
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
# Svn: $Id: win_data.py 52 2006-12-03 00:44:40Z briand $
# * **************************************************************** */


import pickle
import jsonpickle
import os
import os.path
import string
import sys
import re
import copy

import wx
import device_data
import bric_data
import program_data

V_TYPES = ["0-255", "+/- 32767"]

# Maximum variables of each type
# basic(8-bits, 16-bits), adv(8-bits, 16-bits)
var_limits = ((200, 13), (200, 13))

win_names = ['ppallete', 'pwork', 'var', # windows
             'detail', 'help',
             'splitter1', 'splitter2', 'status', 'frame'] # containers


class Temporary_data(object):
    def __init__(self):
       self.windows = {}
       self.program_mode = True
       self.first_mode = True

       self.selection_win = None
       self.selection_win_name = None
       self.selection_name = None
       self.selection_pos = -1

       self.config_move_data = None
       self.config_move_old_loc = -1

       self.dirty = False


class Persistent_data(object):
    def __init__(self):
        self.edison_mode = True
        self.version = 10            # Edison version 0 (10+0)

        self.advanced_mode = False

        self.configuration = {}
        self.config_ids = {}
        self.config_use = {}
        self.config_devices = {}
        self.config_orient = {}

        self.variables = {}
        self.var_ids = {}
        self.var_use = {}

        self.program = program_data.Program()


tdata = Temporary_data()
pdata = Persistent_data()

unused_events_set = False
unused_events = {}

def dump():
    print "Data:"
    print "Pdata Version:", pdata.version
    print "Advanced:", pdata.advanced_mode
    print "Edison:", pdata.edison_mode
    print "Configuration:", pdata.configuration
    print "Conf_ids:", pdata.config_ids
    print "Conf_use:", pdata.config_use
    print "Conf_orient:", pdata.config_orient
    print "Conf_move:", tdata.config_move_old_loc, tdata.config_move_data
    print
    print "Variables:", pdata.variables
    print "Var_ids:", pdata.var_ids
    print "Var_use:", pdata.var_use
    print
    print "Windows:", tdata.windows


def save(file_obj):
    #print "Pickling"
    pickle.dump(pdata, file_obj, 2)
    update_dirty(False)

    
# change some of the strings in the JSON data to be easier for the Apps
# (and to protect against changes in the class names)
# "py/tuple"                                  <--> "Tuple"
# "py/object":"gui.win_data.Persistent_data"  <--> "Object" : "Data"
# "py/object:" "gui_program_data.Bric"        <--> "Object" : "Bric"
# "py/object": "gui.program_data.Program"     <--> "Object" : "Program"

def convertPythonDataToJson(data):
    step1 = re.sub(r'"py/tuple":', r'"Tuple":', data)
    step2 = re.sub(r'"py/object": "gui.win_data.Persistent_data"', r'"Object": "Data"', step1)
    step3 = re.sub(r'"py/object": "gui.program_data.Bric"', r'"Object": "Bric"', step2)
    step4 = re.sub(r'"py/object": "gui.program_data.Program"', r'"Object": "Program"', step3)
    return step4
    
def convertJsonToPythonData(json):
    step1 = re.sub(r'"Tuple":', r'"py/tuple":', json)
    step2 = re.sub(r'"Object": "Data"', r'"py/object": "gui.win_data.Persistent_data"', step1)
    step3 = re.sub(r'"Object": "Bric"', r'"py/object": "gui.program_data.Bric"', step2)
    step4 = re.sub(r'"Object": "Program"', r'"py/object": "gui.program_data.Program"', step3)
    return step4

def saveEdisonAsJson(file_obj):
    # Grab a deepcopy as will be doing destructive changes
    test = copy.deepcopy(pdata)
    
    # remove values that don't change as they can be reconstructed
    del test.configuration
    del test.config_ids
    del test.config_use
    del test.config_orient
    del test.config_devices
    del test.advanced_mode

    encoding = jsonpickle.encode(test)
    fileData = convertPythonDataToJson(encoding)
    
    file_obj.write(fileData)
    update_dirty(False)

def convertKeysToInts(dict):
    fixed = {}
    for k in dict:
        fixed[int(k)] = dict[k]
    return fixed

def loadEdisonAsJson(file_obj, strict):
    global pdata
    program_version = pdata.version
    data = file_obj.read()
    
    jsonData = convertJsonToPythonData(data)
    #print "jsonData:", jsonData
    
    test = jsonpickle.decode(jsonData)
    #print "Decoded:", test

    if (strict and (test.version != pdata.version)):
        wx.MessageBox("Version of data in file '%s' doesn't match this version of Bricworks." % (file_obj.name,),
                      "Version Mismatch - can't load program",
                      wx.OK | wx.ICON_ERROR)
    else:
        if (test.version != pdata.version):
            result = wx.MessageBox("Version of data in file '%s' " % (file_obj.name,) +\
                                   "doesn't match this version of Bricworks. "  +\
                                   "You may try anyway, or CANCEL to abort the file open.",
                                   "Version Mismatch Warning",
                                   wx.OK | wx.CANCEL | wx.ICON_WARNING)
            if (result != wx.OK):
                return

        # fixup the integer keys
        #test.configuration = convertKeysToInts(test.configuration)
        #test.config_ids = convertKeysToInts(test.config_ids)
        #test.config_use = convertKeysToInts(test.config_use)
        test.program.brics = convertKeysToInts(test.program.brics)
        test.var_use = convertKeysToInts(test.var_use)


        pdata = test
        pdata.advanced_mode = False
        pdata.version = program_version
        pdata.configuration = {}
        pdata.config_ids = {}
        pdata.config_use = {}
        pdata.config_orient = {}
        pdata.config_devices = {}
        set_edison_configuration()

        update_dirty(False)
        
        #dump()
        #pdata.program.dump()

        # update the used events
        initialise_unused_events()

def clear_unused_events():
    global unused_events
    global unused_events_set
    unused_events = {}
    unused_events_set = False
    
def set_unused_events(events):
    global unused_events
    global unused_events_set
    unused_events = events
    unused_events_set = True
    #print
    #print "Set unused events:", events
    #print

def get_unused_events():
    return (unused_events_set, unused_events)

def initialise_unused_events():
    set_unused_events(tdata.windows['detail'].get_unused_events())

def load(file_obj, strict):
    global pdata
    program_version = pdata.version
    test = pickle.load(file_obj)

    if (strict and (test.version != pdata.version)):
        wx.MessageBox("Version of data in file '%s' doesn't match this version of Bricworks." % (file_obj.name,),
                      "Version Mismatch - can't load program",
                      wx.OK | wx.ICON_ERROR)
    else:
        if (test.version != pdata.version):
            result = wx.MessageBox("Version of data in file '%s' " % (file_obj.name,) +\
                                   "doesn't match this version of Bricworks. "  +\
                                   "You may try anyway, or CANCEL to abort the file open.",
                                   "Version Mismatch Warning",
                                   wx.OK | wx.CANCEL | wx.ICON_WARNING)
            if (result != wx.OK):
                return

        pdata = test

        update_dirty(False)
        dump()
        pdata.program.dump()

def is_data_dirty():
    return tdata.dirty

def update_dirty(dirty):
    if (tdata.dirty != dirty):
        tdata.dirty = dirty
        tdata.windows['frame'].change_dirty(dirty)
        status_dirty(dirty)


def clear_pdata():
    config_clear()
    vars_clear()
    pdata.program.clear()
    update_dirty(False)

def program():
    return pdata.program

def set_adv_mode(advanced):
    if (advanced != pdata.advanced_mode):
        pdata.advanced_mode = advanced
        update_dirty(True)

def get_adv_mode():
    return pdata.advanced_mode

def get_edison_mode():
    return pdata.edison_mode

def register_window(name, window):
    if (name not in win_names):
        print "Error - unknown name:", name
    else:
        tdata.windows[name] = window

def verify_registry():
    result = True
    for wn in win_names:
        if (wn not in tdata.windows):
            print "Error - window %s has not been registered"
            result = False
    return result

def force_redraw(name=None):
    if (name):
        if (name in tdata.windows):
            tdata.windows[name].Refresh()
    else:
        for name in tdata.windows:
            tdata.windows[name].Refresh()

def get_main_window_type():
    return 'program'

# def switch_to_config():
#     if (not tdata.program_mode and not tdata.first_mode):
#         return

#     tdata.program_mode = False
#     tdata.first_mode = False

#     sp = tdata.windows['splitter1']
#     sp3 = tdata.windows['splitter3']

#     if (sp.GetWindow1() == tdata.windows['ppallete']):
#         sp.ReplaceWindow(tdata.windows['ppallete'], tdata.windows['cpallete'])
#     if (sp3.GetWindow1() == tdata.windows['pwork']):
#         sp3.ReplaceWindow(tdata.windows['pwork'], tdata.windows['cwork'])

#     tdata.windows['pwork'].Hide()
#     tdata.windows['cwork'].Show()
#     tdata.windows['ppallete'].Hide()
#     tdata.windows['cpallete'].Show()

#     selection_drop_all()

# def switch_to_program():
#     if (tdata.program_mode and not tdata.first_mode):
#         return

#     tdata.program_mode = True
#     tdata.first_mode = False

#     sp = tdata.windows['splitter1']
#     sp3 = tdata.windows['splitter3']

#     if (sp.GetWindow1() == tdata.windows['cpallete']):
#         sp.ReplaceWindow(tdata.windows['cpallete'], tdata.windows['ppallete'])
#     if (sp3.GetWindow1() == tdata.windows['cwork']):
#         sp3.ReplaceWindow(tdata.windows['cwork'], tdata.windows['pwork'])

#     tdata.windows['pwork'].Show()
#     tdata.windows['cwork'].Hide()
#     tdata.windows['ppallete'].Show()
#     tdata.windows['cpallete'].Hide()

#     selection_drop_all()

def inform_pallete_of_frame_rect(rect):
    tdata.windows['ppallete'].update_frame_rect(rect)

def inform_work_of_centre_pt(pt, name, drag_image):
    return tdata.windows['pwork'].update_move_centre_pt(pt, name, drag_image)

def make_var_and_config_update():
    # need to update the config and var windows
    #tdata.windows['config'].update_list()
    tdata.windows['var'].update_list()

def inform_help_win(help_text):
    tdata.windows['help'].set_text(help_text)

def add_variable():
    tdata.windows['var'].add_variable()

# ---------------------------------------------------------
# Configuration data

def config_clear():
    pdata.configuration.clear()
    pdata.config_ids.clear()
    pdata.config_use.clear()
    pdata.config_devices.clear()
    pdata.config_orient.clear()

    for d,t in device_data.get_devices():
        pdata.config_devices[d] = 0

    #print pdata.config_devices

def config_dirty(dirty):
    update_dirty(dirty)
    config_update_list()

def config_update_list():
    pass
    #tdata.windows['config'].update_list()

def config_add(location, dtype):
    if (config_check(location, dtype)):
        name = config_new_name(dtype)
        id = config_new_id()
        pdata.configuration[location] = (dtype, name)
        pdata.config_ids[location] = id
        pdata.config_use[id] = (location, 0)

        pdata.config_devices[dtype] += 1

        # Orientation is needed for the corners
        # BED - do a pop-up for this info
        if (location in [1, 4, 7, 10] and (dtype == "Motor A" or dtype == "Motor B")):
            pdata.config_orient[location] = get_orientation(location)

        config_dirty(True)
        return True
    else:
        return False

def config_new_name(dtype):
    num = 1
    for loc in pdata.configuration:
        if (pdata.configuration[loc][0] == dtype):
            num += 1
    name = "%s%d" % (dtype.upper(), num)
    return name.replace(' ', '_')

def config_new_id():
    if (pdata.config_use):
        return max(pdata.config_use.keys()) + 1
    else:
        return 1

def config_change_name(loc, new_name):
    new_name = new_name.replace(' ', '_')
    dtype, dump = pdata.configuration[loc]
    pdata.configuration[loc] = (dtype, new_name)
    config_dirty(True)

def config_id_from_name(name):
    for loc in pdata.configuration:
        if (pdata.configuration[loc][1] == name):
            return pdata.config_ids[loc]

    raise AssertionError, "Corrupted data"

def config_loc_from_name(name):
    for loc in pdata.configuration:
        if (pdata.configuration[loc][1] == name):
            return loc
    raise AssertionError, "Corrupted data"


def config_name_from_id(id):
    if (id in pdata.config_use):
        return pdata.configuration[pdata.config_use[id][0]][1]

    raise AssertionError, "Corrupted data"

def config_loc_from_id(id):
    if (id in pdata.config_use):
        return pdata.config_use[id][0]

    raise AssertionError, "Corrupted data"

def config_dtype_from_id(id):
    if (id in pdata.config_use):
        return pdata.configuration[pdata.config_use[id][0]][0]

    raise AssertionError, "Corrupted data"

def config_orient_from_loc(loc):
    if (loc in pdata.config_orient):
        return pdata.config_orient[loc]
    else:
        return 0

def config_in_move():
    return tdata.config_move_data >= 0

def config_move_start(old_loc):
    """Start a move operation"""
    tdata.config_move_data = pdata.configuration[old_loc]
    tdata.config_move_old_loc = old_loc
    del pdata.configuration[old_loc]
    config_update_list()

def config_move_to_trash():
    """Dump the move data if we can and return the status of the dump"""
    id = pdata.config_ids[tdata.config_move_old_loc]
    if (config_in_use(id)):
        return False

    pdata.config_devices[tdata.config_move_data[0]] -= 1
    del pdata.config_ids[tdata.config_move_old_loc]
    del pdata.config_use[id]

    # Orientation data is no longer needed for this location
    if (tdata.config_move_old_loc in pdata.config_orient):
        del pdata.config_orient[tdata.config_move_old_loc]

    tdata.config_move_old_loc = -1
    tdata.config_move_data = None


    config_dirty(True)
    return True

def config_move_abort():
    """Abort the move"""
    pdata.configuration[tdata.config_move_old_loc] = tdata.config_move_data
    tdata.config_move_old_loc = -1
    tdata.config_move_data = None

def config_move_end(new_loc):
    """Complete the move to the new_loc"""
    pdata.configuration[new_loc] = tdata.config_move_data

    id = pdata.config_ids[tdata.config_move_old_loc]
    del pdata.config_ids[tdata.config_move_old_loc]
    pdata.config_ids[new_loc] = id
    old_loc, ref_cnt = pdata.config_use[id]
    pdata.config_use[id] = (new_loc, ref_cnt)

    # Orientation data is no longer needed for this location
    if (tdata.config_move_old_loc in pdata.config_orient):
        del pdata.config_orient[tdata.config_move_old_loc]

    # Orientation is needed for the corners
    # BED - do a pop-up for this info
    dtype = pdata.configuration[new_loc][0]
    if (new_loc in [1, 4, 7, 10] and (dtype == "Motor A" or dtype == "Motor B")):
        pdata.config_orient[new_loc] = get_orientation(new_loc)

    tdata.config_move_old_loc = -1
    tdata.config_move_data = None
    config_dirty(True)

def config_get_all():
    return pdata.configuration

def config_get(loc):
    if (loc in pdata.configuration):
        return pdata.configuration[loc]
    else:
        return (None, None)

def config_get_id(loc):
    if (loc in pdata.config_ids):
        return pdata.config_ids[loc]
    else:
        return None

def config_in_use(id):
    if (pdata.config_use[id][1] > 0):
        return True
    else:
        return False

def config_add_use(id):
    loc, ref_cnt = pdata.config_use[id]
    pdata.config_use[id] = (loc, ref_cnt+1)
    config_dirty(True)


def config_rm_use(id):
    if (get_edison_mode()):
        return

    loc, ref_cnt = pdata.config_use[id]
    ref_cnt -= 1
    if (ref_cnt <= 0):
        ref_cnt = 0
        #print "Config id:", id, "is no longer in use"
    pdata.config_use[id] = (loc, ref_cnt)
    config_dirty(True)


def config_check(location, dtype):
    # not valid if occupied, second half of a wheel or tracker and loc not 0
    prev_loc = location - 1
    if (prev_loc < 0):
        prev_loc = 11
    next_loc = location + 1
    if (next_loc > 11):
        next_loc = 0

    if (location < 0 or location > 11):
        result = False
    elif (pdata.configuration.has_key(location)):
        result = False
    elif (dtype == "Analog In" and location in [2, 4, 8, 10]):
        result = False
    elif (dtype == "Line Tracker" and location != 0):
        result = False
##    *BED* -- motor can go at 11&0 so this is OK
##    elif ((location == 11) and
##          (dtype == "Motor A" or dtype == "Motor B")):
##        result = False
    elif (pdata.configuration.has_key(prev_loc) and
          (pdata.configuration[prev_loc][0] == "Motor A" or
           pdata.configuration[prev_loc][0] == "Motor B")):
        result = False
    elif ((dtype == "Motor A" or dtype == "Motor B") and
          pdata.configuration.has_key(next_loc)):
        result = False
    elif ((dtype == "Sounder") and (pdata.config_devices[dtype] > 0) and  (tdata.config_move_old_loc == -1)):
        # can only have 1 sounder, unless we are currently moving the sounder
        result = False

    else:
        result = True

    return result


def config_name_already_used(loc, name):
    for l in pdata.configuration:
        if (l == loc):
            continue
        if (pdata.configuration[l][1] == name):
            return True

    return False

def config_device_used(dtype):
    return pdata.config_devices[dtype] > 0

def config_device_names(dtype):
    if (config_device_used(dtype)):
        names = []
        for loc in pdata.configuration:
            if (pdata.configuration[loc][0] == dtype):
                names.append(pdata.configuration[loc][1])

        return names
    else:
        return []

def config_motor_pairs():
    pairs = []

    easy = ((2,9), (3, 8), (5, 0), (6, 11))
    for loc1, loc2 in easy:
        type1, name1 = config_get(loc1)
        if (type1 == 'Motor A' or type1 == 'Motor B'):
            type2, name2 = config_get(loc2)
            if (type2 == 'Motor A' or type2 == 'Motor B'):
                pairs.append(name1+'+'+name2)

    hard = ((1, 1, 4, -1), (4, 1, 7, -1), (7, 1, 10, -1), (10, 1, 1, -1))
    for loc1, or1, loc2, or2 in hard:
        type1, name1 = config_get(loc1)
        if ((type1 == 'Motor A' or type1 == 'Motor B') and
            config_orient_from_loc(loc1) == or1):
            type2, name2 = config_get(loc2)
            if ((type2 == 'Motor A' or type2 == 'Motor B') and
                config_orient_from_loc(loc2) == or2):
                pairs.append(name1+'+'+name2)

    return pairs

def set_edison_configuration():
    config_clear()
    config_add(0,"Line Tracker")          # id=1
    config_add(1, "LED")                  # id=2
    config_add(3, "Motor A")              # id=3
    config_add(5, "IR Receiver")          # id=4
    config_add(6, "Sounder")              # id=5
    config_add(7, "IR Transmitter")       # id=6
    config_add(8, "Motor B")              # id=7
    config_add(11, "LED")                 # id=8

    config_change_name(3, "Right Motor")  # id=3
    config_change_name(8, "Left Motor")   # id=7

    config_change_name(1, "Right LED")    # id=2
    config_change_name(11, "Left LED")    # id=8

    # Mark in use so that can dispense with saving this info
    # in JSON
    config_add_use(config_get_id(0))
    config_add_use(config_get_id(1))
    config_add_use(config_get_id(3))
    config_add_use(config_get_id(5))
    config_add_use(config_get_id(6))
    config_add_use(config_get_id(7))
    config_add_use(config_get_id(8))
    config_add_use(config_get_id(11))

# ---------------------------------------------------------
# Variable data


def vars_clear():
    pdata.variables.clear()
    pdata.var_ids.clear()
    pdata.var_use.clear()

def vars_add(name, type, length, initial):
    id = vars_new_id()
    name = name.replace(' ', '_')
    pdata.variables[name] = (type, length, initial)
    pdata.var_ids[name] = id
    pdata.var_use[id] = (name, 0)
    update_dirty(True)
    force_redraw('ppallete')
    #print "Var added: %s (%s)" % (name, pdata.variables[name])

def vars_new_id():
    if (pdata.var_use):
        return max(pdata.var_use.keys()) + 1
    else:
        return 1

def vars_remove(name):
    if (vars_used_in_program(name)):
        return False
    else:
        id = pdata.var_ids[name]
        del pdata.variables[name]
        del pdata.var_ids[name]
        del pdata.var_use[id]
        update_dirty(True)
        force_redraw('ppallete')
        return True

def vars_change(old_name, new_name, new_type, new_length, new_initial):
    old_name = old_name.replace(' ', '_')
    new_name = new_name.replace(' ', '_')
    if (old_name != new_name):
        id = pdata.var_ids[old_name]
        pdata.var_ids[new_name] = id
        del pdata.var_ids[old_name]
        dump, ref_count = pdata.var_use[id]
        pdata.var_use[id] = (new_name, ref_count)
        del pdata.variables[old_name]

    pdata.variables[new_name] = (new_type, new_length, new_initial)
    update_dirty(True)
    force_redraw('ppallete')
    #print "Var changed: %s (%s)" % (new_name, pdata.variables[new_name])

def vars_get_all():
    return pdata.variables

def vars_get(name):
    if (name in pdata.variables):
        return pdata.variables[name]
    else:
        return None

def vars_exists(name):
    return name in pdata.variables

def vars_split_initial(in_str):
    in_str.strip()
    comps = []

    if ((len(in_str) >= 2) and
        (in_str[0] == '"' or in_str[0] == "'") and
        (in_str[0] == in_str[-1])):
        comps.append(in_str)
        return comps

    between_values = True
    cur = ""

    for s in in_str:
        if (between_values and s == ' '):
            continue

        between_values = False

        if (s == ',' or s == ' '):
            comps.append(cur)
            cur = ""
            if (s == ' '):
                between_values = True

        else:
            cur += s

    if (cur):
        comps.append(cur)

    return comps

def vars_get_id(name):
    if (name in pdata.var_ids):
        return pdata.var_ids[name]
    else:
        return None

def vars_get_name(id):
    if (id in pdata.var_use):
        return pdata.var_use[id][0]
    else:
        return None

def vars_get_type_from_name(name):
    if (name in pdata.variables):
        return pdata.variables[name][0]
    else:
        raise KeyError, "Unknown variable name"

def vars_get_type_letter_from_name(name):
    vtype = vars_get_type_from_name(name)
    if (vtype == V_TYPES[0]):
        return 'b'
    else:
        return 'w'

def vars_get_initial_from_name(name):
    if (name in pdata.variables):
        return pdata.variables[name][2]
    else:
        raise KeyError, "Unknown variable name"

def vars_in_use(id):
    if (pdata.var_use[id][1] > 0):
        return True
    else:
        return False

def vars_add_use(id):
    if (id):
        name, ref_cnt = pdata.var_use[id]
        pdata.var_use[id] = (name, ref_cnt+1)
        update_dirty(True)


def vars_rm_use(id):
    if (id):
        name, ref_cnt = pdata.var_use[id]
        ref_cnt -= 1
        if (ref_cnt <= 0):
            ref_cnt = 0
            #print "var_rm_use(%d) not in use" % (id,)
        pdata.var_use[id] = (name, ref_cnt)
        update_dirty(True)

def vars_used_in_program(name):
    id = vars_get_id(name)
    return vars_in_use(id)

def vars_no_room_left(vtype, vlen):
    vars_count = len(vars_names(vtype))

    if (get_adv_mode()):
        limits = var_limits[1]
    else:
        limits = var_limits[0]

    if (vtype == V_TYPES[0]):
        if (vars_count >= limits[0]):
            return True
    else:
        if (vars_count >= limits[1]):
            return True

    return False

def vars_stats():
    if (get_adv_mode()):
        limits = var_limits[1]
    else:
        limits = var_limits[0]

    counts = (len(vars_names(V_TYPES[0])),
              len(vars_names(V_TYPES[0])))

    return (V_TYPES, counts, limits)


def vars_defined(vtype = None):
    if (not vtype):
       return len(pdata.variables) > 0

    for name in pdata.variables:
        if (pdata.variables[name][0] == vtype):
            return True
    return False

def vars_names(vtype = None):
    names = []
    for name in pdata.variables:
        if (not vtype or pdata.variables[name][0] == vtype):
            names.append(name)

    return names

# ---------------------------------------------------------
# Program data

##class Bric(object):
##    def __init__(self, prev_id, name):
##        self.id = proc_new_id()
##        self.prev_id1 = prev_id
##        self.name = name
##        self.next_id1 = None
##        self.next_id2 = None
##        self.bric_data = None

##def prog_clear():
##    pass

##def prog_add_bric(prev_id, bric_name):
##    """ Returns the id of the new bric"""
##    new_bric = Bric(prev_id, bric_name)

##def proc_new_id():
##    pass


def remove_bric_refs(name, old_data):
    tdata.windows['detail'].remove_bric_refs(name, old_data)

def generate_code(bric_id):
    return tdata.windows['detail'].generate_code(bric_id)

def make_mod_reg(mod_name, reg_name):
    # replace spaces with _
    return "%%%s:%s" % (mod_name.replace(' ', '_'), reg_name)

def constant_error(err_string):
    err_string = "Restoring properties to previous values because:\n\n" + err_string
    wx.MessageBox(err_string, caption="Error in constant", style=wx.ICON_ERROR | wx.OK)

def conv_to_time(string_in):
    string_in = string_in.strip()
    try:
        time = int(float(string_in)*100)
    except:
        constant_error("Time value '%s' isn't valid." % (string_in,))
        return None

    if (time < 0):
        constant_error("Time can't be negative")
    elif (time > 32767):
        constant_error("Time value is greater then 327.67 seconds")
    else:
        return time

    return None

def conv_to_tx_char(string_in):
    if (len(string_in) > 1):
        if string_in.isspace():
            string_in = ' '
        else:
            string_in = string_in.strip()

    if (len(string_in) == 1):
        value = ord(string_in[0])

    elif ((len(string_in) == 4) and
          string_in.startswith("0x") and
          (string_in[2] in string.hexdigits) and
          (string_in[3] in string.hexdigits)):
        value = int(string_in[2:], 16)

    else:
        constant_error("Invalid transmit character: %s. Must be a character or 0xhh where h is a hex digit." % (string_in,))
        value = None

    return value

def conv_to_lcd_char(string_in):
    if (len(string_in) > 1):
        if string_in.isspace():
            string_in = ' '
        else:
            string_in = string_in.strip()

    if (len(string_in) == 1):
        value = ord(string_in[0].upper())

        if (value < ord(' ') or value > ord('Z')):
            constant_error("LCD character '%s' is out of range " % (string_in,) +\
                           "(upper-case, digits and some punctuation are valid)")
            value = None
    else:
        constant_error("There must be exactly one character")
        value = None

    return value

def conv_to_lcd_string(start, string_in):
    if (len(string_in) > 1):
        if string_in.isspace():
            string_in = ' '
        else:
            string_in = string_in.strip()

    string_in = string_in.upper()
    if (len(string_in) + start > 84):
        constant_error("LCD string would overflow the LCD screen")
        return None

    data = ""
    for i in range(len(string_in)):
        if (string_in[i] < ' ' or string_in[i]>'Z'):
            constant_error("LCD character '%s' is out of range " % (string_in[i],) +\
                           "(upper-case, digits and some punctuation are valid)")
            return None
        else:
            data += "%d " % (ord(string_in[i]),)

    return data



def conv_to_number(string_in, n_type, n_min=None, n_max=None):
    number = None
    if (len(string_in)<1):
        constant_error("Empty number")
        return None

    if (n_type == "b"):
        if (string_in.isdigit()):
            number = int(string_in)

        if (number != None and (number < 0 or number >255)):
            constant_error("Number %d is outside of the range: 0 -> 255" % (number,))
            return None

    elif (n_type == "w"):
        if (string_in[0] == '-'):
            if (string_in[1:].isdigit()):
                number = -1 * int(string_in[1:])
        elif (string_in[0] == '+'):
            if (string_in[1:].isdigit()):
                number = int(string_in[1:])
        else:
            if (string_in.isdigit()):
                number = int(string_in)

        if (number != None and (number < -32767 or number > 32767)):
            constant_error("Number %d is outside of the range: -32767 -> +32767" % (number,))
            return None
    else:
        number = None

    if (number == None):
        constant_error("Invalid number: "+string_in)

    if (number != None and n_min != None):
        if (number < n_min):
            constant_error("Number %s is less than minimum %s" % (number, n_min))
            number = None

    if (number != None and n_max != None):
        if (number > n_max):
            constant_error("Number %s is greater than maximum %s" % (number, n_max))
            number = None

    return number

def make_label(bric_id, index):
    return ":Bric%d_%d" % (bric_id, index)

def make_labels(bric_id, start, number):
    result = []
    for i in range(number):
        result.append(make_label(bric_id, start+i))

    return result

def make_if_labels(bric_id):
    return (":Bric%d_If_True" % (bric_id,),
            ":Bric%d_If_False" % (bric_id,),
            ":Bric%d_If_Endif" % (bric_id,)
            )

def make_loop_labels(bric_id):
    return (":Bric%d_Loop_body" % (bric_id,),
            ":Bric%d_Loop_exit" % (bric_id,),
            ":Bric%d_Loop_check" % (bric_id,)
            )


device_dict = {"Line Tracker":"tracker",
               "Bump":"bumper",
               "LED":"led",
               "Motor A":"motor-a",
               "Motor B":"motor-b",
               "IR Receiver":"irrx",
               "IR Transmitter":"irtx",
               "Sounder":"beeper",
               "Digital In":"digin",
               "Digital Out":"digout",
               "Analog In":"analogin",
               }

def get_code_stream(bric_id, end_bric, in_event, code_lines):
    while (bric_id != end_bric):
        bric_name = pdata.program.get_bric_name(bric_id)
        if (bric_name == "Main"):
            bric_id = pdata.program.get_next_id(bric_id, 0)
            continue

        code_lines.append("")
        code_lines.append("# Bric id: %s, name: %s" % (bric_id, bric_name))
        #print "Code_lines:", code_lines
        #print "Window:", tdata.windows['detail']
        code_lines.extend(tdata.windows['detail'].generate_code(bric_id, in_event))

        if (bric_name == "If"):
            true_path = pdata.program.get_next_id(bric_id, 0)
            false_path = pdata.program.get_next_id(bric_id, 1)
            labels = make_if_labels(bric_id)

            # true branch
            code_lines.append(labels[0])
            get_code_stream(true_path, bric_id+1, in_event, code_lines)
            # go to end if
            code_lines.append("bra %s" % (labels[2],))

            # false branch
            code_lines.append(labels[1])
            get_code_stream(false_path, bric_id+1, in_event, code_lines)

            # endif
            code_lines.append(labels[2])
            bric_id += 1

        elif (bric_name == "Loop"):
            true_path = pdata.program.get_next_id(bric_id, 0)
            labels = make_loop_labels(bric_id)

            # start label (labels[2]) has been placed by loop bric

            # Loop body
            code_lines.append(labels[0])
            get_code_stream(true_path, bric_id+1, in_event, code_lines)

            # branch to the beginning and add the label for the end
            code_lines.append("bra %s" % (labels[2],))
            code_lines.append("%s" % (labels[1],))

            bric_id += 1

        bric_id = pdata.program.get_next_id(bric_id, 0)


def add_header_code(code_lines):
    code_lines.append("# Do not edit! Created automatically by Microbric Works.")
    code_lines.append("#")

    if (get_edison_mode()):
        code_lines.append("# Edison code")
        code_lines.append("VERSION 2,0")
    else:
        if (get_adv_mode()):
            code_lines.append("# Advanced code")
            code_lines.append("VERSION 1,0")
        else:
            code_lines.append("# Basic code")
            code_lines.append("VERSION 0,0")

    # IN EDISON - put the modules here for compiling, but don't download
    for i in range(12):
        mod_id = config_get_id(i)
        if (mod_id and config_in_use(mod_id)):
            code_lines.append("DEVICE %s, %d, %s" % (device_dict[config_dtype_from_id(mod_id)],
                                                     i,
                                                     config_name_from_id(mod_id).replace(' ', '_')))

    code_lines.append("BEGIN MAIN")

    # Have one extra for the null terminator
    code_lines.append("DATB _tune_store 0 17")

    code_lines.append("DATB _main_time_buffer * 8")
    code_lines.append("DATB _event_time_buffer * 8")


    for v_name in vars_names():
        if (vars_used_in_program(v_name)):
            v_type = vars_get_type_letter_from_name(v_name).upper()
            v_init = vars_get_initial_from_name(v_name)
            code_lines.append("DAT%s %s * 1 %s" % (v_type, v_name.replace(' ', '_'), v_init))



def get_all_code(file_handle=None):
    code_lines = []
    # place devices, version, etc
    # put in buffers for timers
    add_header_code(code_lines)

    stream = 0
    while (stream < pdata.program.get_stream_count()):
        if (stream > 0):
            # Event handler
            in_event = True
        else:
            in_event = False

        get_code_stream(pdata.program.get_stream_id(stream), -1, in_event, code_lines)
        code_lines.append("stop")
        if (not in_event):
            code_lines.append("END MAIN")
        else:
            code_lines.append("END EVENT")

        stream += 1

    code_lines.append("FINISH")
    if (not file_handle):
        print "\nCode:\n", code_lines
    else:
        for line in code_lines:
            file_handle.write(line+'\n')

# ------------------- Selection -----------------------------------
#

click_wav = None

def click_sound():
    global click_wav
    if (sys.platform=='win32' or
        sys.platform.startswith('linux') or
        sys.platform=='darwin'):
        try:
            if (not click_wav):
                click_wav = wx.Sound()
                click_wav.Create("Click.wav")

            click_wav.Play(flags=wx.SOUND_ASYNC)
        except:
            pass


def selection_take(win_name, name_data, pos_data):
    # remove selection from the current window
    last_win = tdata.selection_win

    # update help
    if (win_name == 'ppallete' or win_name == 'pwork'):
        tdata.windows['help'].set_text(bric_data.get_bric_help(name_data))
        if (win_name == 'pwork'):
            tdata.windows['detail'].set_details(name_data, pos_data)
            if (name_data != ""):
                click_sound()
        else:
            tdata.windows['detail'].set_details("", -1)

    else:
        tdata.windows['detail'].set_details("", -1)


    tdata.selection_win = tdata.windows[win_name]
    tdata.selection_win_name = win_name
    tdata.selection_name = name_data
    tdata.selection_pos = pos_data

    if (last_win and (last_win != tdata.selection_win)):
        # Refresh the old window so that it updates the lack of a selection
        last_win.Refresh()

    # Update the new window
    tdata.selection_win.Refresh(True)


def selection_drop_all():
    last_win = tdata.selection_win

    tdata.selection_win = None
    tdata.selection_win_name = None
    tdata.selection_name = None
    tdata.selection_pos = -1

    # update help
    tdata.windows['help'].set_text("")
    tdata.windows['detail'].set_details("", -1)

    if (last_win):
        # Refresh the old window so that it updates the lack of a selection
        last_win.Refresh()


def selection_check(win_name, name_data, pos_data):
    if ((tdata.selection_win_name == win_name) and
        (not name_data or (tdata.selection_name == name_data)) and
        ((pos_data == -1) or (tdata.selection_pos == pos_data))):
        return True
    else:
        return False

# ------------------- Zoom -----------------------------------
#

def set_zoom(zoom):
    tdata.windows['pwork'].set_zoom(zoom)
    #tdata.windows['cwork'].set_zoom(zoom)

def adjust_zoom(dir):
    tdata.windows['pwork'].adjust_zoom(dir)
    #tdata.windows['cwork'].adjust_zoom(dir)

def get_zoom(win_name):
    if (win_name == 'ppallete'):
        return tdata.windows['pwork'].get_zoom()
    #elif (win_name == 'cpallete'):
    #    return tdata.windows['cwork'].get_zoom()
    else:
        return 1.0


# ------------------- Status -----------------------------------
#

status_dirty_store = False
status_file_store = ""

def status_info(text):
    tdata.windows['status'].SetStatusText(text, 0)

def status_dirty(dirty=True):
    global status_dirty_store
    status_dirty_store = dirty
    status_file(status_file_store)

def status_file(file_name):
    global status_file_store
    status_file_store = file_name

    if (status_dirty_store):
        mod = "*"
    else:
        mod = " "

    tdata.windows['status'].SetStatusText("%s File: %s" % (mod, file_name), 2)

def status_space(used, total):
    #tdata.windows['status'].SetStatusText("Memory - Used:%d Total:%d" % (used, total), 1)
    pass


def enabled_on_pallete(win_name, name_data):
    if (win_name == 'ppallete'):
        return bric_data.is_enabled(name_data)
    elif (win_name == 'cpallete'):
        return True
    else:
        return False

# -------------------------- Orientation dialog ---------------------------------

def get_orientation(location):
    message = ""
    message += "You are placing a motor at the (%d, %d) corner.\n" % (location, location+1)
    message += "Do you want the corner piece around the corner (at location %d)?\n" % (location+1,)

    result = wx.MessageBox(message, caption="Corner motor orientation.", style=wx.YES_NO | wx.ICON_QUESTION)
    if (result == wx.YES):
        return 1
    else:
        return -1


def get_ok_to_delete(drop_type):
    message = "Do you want to delete the "+drop_type+" icon?\n"
    #message += "If you press YES the "+drop_type+" will be deleted, NO cancels the delete"

    result = wx.MessageBox(message, caption="Delete check", style=wx.YES_NO | wx.ICON_QUESTION)
    if (result == wx.YES):
        return True
    else:
        return False
