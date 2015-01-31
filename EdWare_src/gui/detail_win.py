#!/usr/bin/env python

# * **************************************************************** **
#
# File: detail_win.py
# Desc: Display and edit selected bric details
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# Copyright 2006, 2014 Microbric Pty Ltd.
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

import wx

import bric_data
import win_data

from wx.lib.masked import NumCtrl

MOTOR_DISTANCE_ENABLED = False

# normally the module combo boxes are 150. But events are long strings
EVENT_COMBO_PIXELS = 200

CONSTANT = "<-Constant"
NO_VAR = "-No Variable-"
MOTHERBOARD = '*Motherboard*'

LCD_CLEAR_SCREEN = "Clear screen"
LCD_SCROLL_LINE = "Scroll line"

MAX_TUNE_STORE = 17

MATH_PLUS = "plus"
MATH_SUB = "minus"
MATH_MULT = "multiply"
MATH_NOT = "not (bitwise)"
MATH_DIV = "divide"
MATH_MOD = "modulus"
MATH_LSHIFT = "left shift"
MATH_RSHIFT = "right shift"
MATH_AND = "and (bitwise)"
MATH_OR = "or (bitwise)"
MATH_XOR = "xor (bitwise)"

MODULE_PROMPT = "Control:"

CONST_SIZE = (130,-1)
SAVE_LABEL = "Save changes"
CANCEL_LABEL = "Undo changes"
U_NAME = "0-255"
S_NAME = "+/- 32767"

#tone_notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
tone_notes = ["A (6th)", "A# (6th)", "B (6th)", "C", "C#", "D", "D#", "E", "F", "F#",
              "G", "G#", "A", "A#", "B", "C (8th)", "Rest"]
tone_durations = ["sixteenth", "eighth", "quarter", "half", "whole"]

TRACKER_0_STATUS = "On reflective surface"
TRACKER_1_STATUS = "On non-reflective surface"

#                           title,      (mod,bit),       if_variant
EVENT_DICT = {'Keypad': (
                  ('Triangle button pressed', ('_devices', 0), 'button'),
                  #('Square button pressed', ('_devices', 1), 'button'),
                  ('Round button pressed', ('_devices', 2), 'button'),),
              'Countdown timer': (
                  ('Timer finished', ('_timers', 0), 'timer'),),
              #'Left Drive' : (
              #    ('Left Strain detected', (None, 0), 'motor'),),
              'Drive' : (
                  ('Strain detected', (None, 0), 'motor'),),
              'Music' : (
                  ('Tune finished', (None, 0), 'timer'),),
              'Detect clap' : (
                  ('Clap detected', (None, 2), 'clap'),),
              'Data from another Edison': (
                  ('IR Character', (None, 0), 'irrx'),),
              'Detect obstacle' : (
                  ('Obstacle at front', (None,4), 'obstacle'),
                  ('Obstacle at left', (None,5), 'obstacle'),
                  ('Obstacle at right', (None,3), 'obstacle'),
                  ('Any Obstacle detected', (None,6), 'obstacle'),),
              'Data from TV remote': (
                  ('Match #0 remote code', (None, 1), 'remote'),
                  ('Match #1 remote code', (None, 1), 'remote'),
                  ('Match #2 remote code', (None, 1), 'remote'),
                  ('Match #3 remote code', (None, 1), 'remote'),
                  ('Match #4 remote code', (None, 1), 'remote'),
                  ('Match #5 remote code', (None, 1), 'remote'),
                  ('Match #6 remote code', (None, 1), 'remote'),
                  ('Match #7 remote code', (None, 1), 'remote'),
                  ('Match #8 remote code', (None, 1), 'remote'),
                  ('Any match remote code', (None, 1), 'remote'),),
              'Line Tracker' : (
                  (TRACKER_0_STATUS, (None, 1), 'tracker'),
                  (TRACKER_1_STATUS, (None, 1), 'tracker'),
                  ('Any change', (None, 1), 'tracker'),),
              }

EVENT_ALIASES = [(MOTHERBOARD, "Keypad"), (MOTHERBOARD, "Countdown timer"),
                 ("Right_Motor", "Drive"), ("SOUNDER1", "Music"), ("SOUNDER1", "Detect clap"),
                 ("IR_RECEIVER1", "Data from another Edison"), ("IR_RECEIVER1", "Detect obstacle"),
                 ("IR_RECEIVER1", "Data from TV remote"), ("LINE_TRACKER1", "Line Tracker") ]

INVALID_NEW_EVENTS = ['Match #0 remote code', 'Match #1 remote code',
                      'Match #2 remote code', 'Match #3 remote code',
                      'Match #4 remote code', 'Match #5 remote code',
                      'Match #6 remote code', 'Match #7 remote code',
                      'Match #8 remote code']

MOTOR_FWD = "Forward"
MOTOR_STP = "Stop"
MOTOR_BCK = "Backward"

MOTOR_P_RT = "Forward right"
MOTOR_P_LT = "Forward left"
MOTOR_P_BL = "Back left"
MOTOR_P_BR = "Back right"
MOTOR_P_SR = "Spin right"
MOTOR_P_SL = "Spin left"
MOTOR_P_RT_90 = "Turn right 90"
MOTOR_P_LT_90 = "Turn left 90"


MOTOR_CODE = {"F":0x80, "B":0x40, "S":0xc0, "FD":0xa0, "BD":0x60}
DIRECTION_CODE = {MOTOR_FWD:0x80, MOTOR_BCK:0x40, MOTOR_STP:0xC0}
DIRECTION_WITH_DIST_CODE = {MOTOR_FWD:0xa0, MOTOR_BCK:0x60, MOTOR_STP:0xC0}

class Detail_win(wx.ScrolledWindow):
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent, style=wx.RAISED_BORDER)

        self.SetScrollRate(20, 20)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.dirty = False
        self.cb_special = None
        self.module_name_conversions = []
        self.good_choices = []

        self.SetSizer(self.vbox)
        self.FitInside()
        self.detail_dict = {'Tone':self.tones_details, 'Beep':self.beep_details,
                            'Digital Out':self.digout_details, 'LED':self.digital_details,
                            'LineTracker':self.digital_details, 'Infrared Data Out':self.txir_details,
                            'Obstacle Detection':self.digital_details,
                            'Serial Data Out':self.txserial_details,
                            'Light Level':self.readlight_details,
                            'Read Distance':self.readdist_details,
                            'Line Tracker':self.readsmall_details,
                            'Bumper':self.readsmall_details, 'Infrared Data In':self.readsmall_details,
                            'Remote':self.readsmall_details, 'Analogue In':self.readsmall_details,
                            'Digital In':self.readsmall_details,
                            'Serial Data In':self.readinternal_details,
                            'Button':self.readinternal_details,
                            'Read Clap Detect':self.readsmall_details,
                            'Read Obstacle Detect':self.readsmall_details,
                            'Read Timer':self.readinternal_details,
                            'Set Timer':self.settimer_details,
                            'Pulse In':self.digpulse_details,
                            'Increment':self.incdec_details, 'Decrement':self.incdec_details,
                            'Set Memory':self.varset_details, 'Copy':self.varcopy_details,
                            'Maths Advanced':self.math_details, 'Maths Basic':self.math_details,
                            'Motor':self.motor_details, 'Motor Pair':self.motor_details,
                            'Write to LCD':self.lcd_details, 'Event':self.event_details,
                            'If':self.if_details, 'Loop':self.loop_details,
                            'Wait':self.wait_details, 'Advanced':self.cpu_details,
                            'Draw to LCD':self.lcddraw_details,
                            }

        self.convert_dict = {'Tone':self.tones_convert, 'Beep':self.beep_convert,
                             'Digital Out':self.digout_convert, 'LED': self.digital_convert,
                             'LineTracker':self.digital_convert, 'Infrared Data Out':self.txir_convert,
                             'Obstacle Detection':self.digital_convert,
                             'Serial Data Out':self.txserial_convert,
                             'Light Level':self.readlight_convert,
                             'Read Distance':self.readdist_convert,
                             'Line Tracker':self.readsmall_convert,
                             'Bumper':self.readsmall_convert, 'Infrared Data In':self.readsmall_convert,
                             'Remote':self.readsmall_convert, 'Analogue In':self.readsmall_convert,
                             'Digital In':self.readsmall_convert,
                             'Serial Data In':self.readinternal_convert,
                             'Button':self.readinternal_convert,
                             'Read Clap Detect':self.readsmall_convert,
                             'Read Obstacle Detect':self.readsmall_convert,
                             'Read Timer':self.readinternal_convert,
                             'Set Timer':self.settimer_convert,
                             'Pulse In':self.digpulse_convert,
                             'Increment':self.incdec_convert, 'Decrement':self.incdec_convert,
                             'Set Memory':self.varset_convert, 'Copy':self.varcopy_convert,
                             'Maths Advanced':self.math_convert, 'Maths Basic':self.math_convert,
                             'Motor':self.motor_convert, 'Motor Pair':self.motor_convert,
                             'Write to LCD':self.lcd_convert, 'Event':self.event_convert,
                             'If':self.if_convert, 'Loop':self.loop_convert,
                             'Wait':self.wait_convert, 'Advanced':self.cpu_convert,
                             'Draw to LCD':self.lcddraw_convert,
                             }




    def update_dirty(self, dirty):
        if (dirty != self.dirty):
            self.dirty = dirty

            # Update the win_data dirty flag if it's now dirty. Only edware.py will reset
            # this flag on saving.
            if (dirty):
                win_data.update_dirty(dirty)

    def switch_group(self, sel_group):
        self.sel_group = sel_group

        for grp, children in self.groups:
            if (grp == sel_group):
                for c in children:
                    c.Enable(True)
                    # check to see if it should be off
                    self.switch_constants(c)
            else:
                for c in children:
                    c.Enable(False)

        sel_group.SetValue(True)

    def switch_constants(self, obj=None):
        if (not self.vars):
            return

        if (obj):
            for var, cons in self.vars:
                if (var == obj):
                    cons.Enable(obj.GetValue() == CONSTANT)

        else:
            for var, cons in self.vars:
                cons.Enable(var.GetValue() == CONSTANT)

    def on_rb(self, event):
        self.switch_group(event.GetEventObject())
        self.update_dirty(True)

    def on_cb_vars(self, event):
        """Switch constants depending on variable"""
        self.switch_constants(event.GetEventObject())
        if (self.cb_special):
            self.cb_special()
        self.update_dirty(True)

    def on_cons_tc(self, event):
        self.update_dirty(True)

    def on_cons_cb(self, event):
        if (self.cb_special):
            self.cb_special()
        self.update_dirty(True)

    def on_click(self, event):
        # which button is it
        button = event.GetEventObject()
        label = button.GetLabel()
        if (label == SAVE_LABEL):
            self.save_changes()
        elif (label == CANCEL_LABEL):
            self.cancel_changes()
        else:
            pass

    def bind_event_handlers(self):
        if (self.vars and len(self.vars) > 0):
            for var, con in self.vars:
                self.Bind(wx.EVT_COMBOBOX, self.on_cb_vars, var)

        if (self.groups and len(self.groups)>1):
            for grp, children in self.groups:
                self.Bind(wx.EVT_RADIOBUTTON, self.on_rb, grp)

        if (self.cons_tc and len(self.cons_tc) > 0):
            for c in self.cons_tc:
                self.Bind(wx.EVT_TEXT, self.on_cons_tc, c)

        if (self.cons_cb and len(self.cons_cb) > 0):
            for c in self.cons_cb:
                self.Bind(wx.EVT_COMBOBOX, self.on_cons_cb, c)

##        if (len(self.buttons) > 0):
##            for b in self.buttons:
##                self.Bind(wx.EVT_BUTTON, self.on_click, b)
##                b.Enable(False)


    def set_details(self, name, bric_id):

        if (self.dirty):
            #print "Saving", bric_id
            self.save_changes()

            self.dirty = False

        self.cb_special = None
        self.bric_type = name
        self.bric_id = bric_id

        self.vbox.Clear(True)

        if (name in self.detail_dict):
            self.bric_id = bric_id
            #self.buttons = (wx.Button(self, -1, CANCEL_LABEL), wx.Button(self, -1, SAVE_LABEL))

            self.title = wx.StaticText(self, -1, "")
            self.old_data = win_data.program().get_bric_data(bric_id)

##            hbox = wx.BoxSizer(wx.HORIZONTAL)
##            hbox.Add(self.title, 0)
##            hbox.Add((5,5), 1, flag=wx.EXPAND)
##            for b in self.buttons:
##                hbox.Add(b, 0)
##            self.vbox.Add(hbox, flag=wx.EXPAND)
            self.vbox.Add(self.title, 0, wx.ALL|wx.EXPAND, 5)
            self.vbox.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)

            # set new details
            self.vbox.Add(self.detail_dict[name](bric_id, self.old_data), 0, wx.ALL|wx.EXPAND, 5)

            # start out not dirty
            self.update_dirty(False)

        self.SetVirtualSize(self.GetBestSize())
        self.FitInside()
        self.Layout()
        self.Refresh()


    def make_radio_buttons(self, choices):
        rb_list = []
        first = True
        for c in choices:
            if (first):
                rb_list.append(wx.RadioButton(self, -1, c, style=wx.RB_GROUP))
                first = False
            else:
                rb_list.append(wx.RadioButton(self, -1, c))

        return rb_list

    def make_combo(self, choices, add_const = False, size=(-1,-1), sort=True, add_no_var=False):
        if (sort):
            choices.sort()

        if (add_const):
            choices.insert(0, CONSTANT)

        if (add_no_var):
            choices.insert(0, NO_VAR)

        cb = wx.ComboBox(self, -1, choices[0], choices=choices,
                         style=wx.CB_READONLY, size=size)
        return cb



    def make_text_ctrl(self, default, size=(100,-1)):
        tc = wx.TextCtrl(self, -1, value=default, size=size)
        #tc = NumCtrl(self, -1, value=default, size=size, min=0, max=1000, limited=True)
        return tc

    def set_control_values(self, control_list, value_list):
        for i in range(len(control_list)):
            if (control_list[i]):
                #print "Setting:", value_list[i]
                control_list[i].SetValue(value_list[i])

    def add_with_prompt(self, grid, loc, prompt, controls, extra_info=None, ctrl_span=None, expand=True):
        flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL
        if (len(prompt)>0):
            grid.Add(wx.StaticText(self, -1, prompt), loc, flag=flag)
            loc = (loc[0], loc[1]+1)
        extra_loc = (loc[0]+1, loc[1])
        flag = wx.ALIGN_CENTRE_VERTICAL
        if (expand):
            flag |= wx.EXPAND
        for c in controls:
            if (ctrl_span):
                grid.Add(c, loc, flag=flag, span=ctrl_span)
            else:
                grid.Add(c, loc, flag=flag)

            loc = (loc[0], loc[1]+1)

        if (extra_info):
            grid.Add(wx.StaticText(self, -1, '(%s)' % (extra_info,)), extra_loc, span=(1,3), flag=flag)


    def make_headings(self, grid, loc):
        grid.Add(wx.StaticText(self, -1, "Constant"), loc, flag=wx.ALIGN_CENTRE)
        loc = (loc[0], loc[1]+1)
        grid.Add(wx.StaticText(self, -1, "Variable"), loc, flag=wx.ALIGN_CENTRE)


    def save_initial(self):
        data = self.conv_func(None, 'to_ids_add_refs', self.name, self.bric_id)
        #print "save_initial:", data
        win_data.program().set_bric_data(self.bric_id, data)
        self.dirty = False
        self.update_dirty(False)
        return data

    def check_constants(self):
        if (not self.cons_tc):
            return True

        # get the data
        data = []
        if (self.rbs):
            data.append(0)
            for i in range(len(self.rbs)):
                if (self.rbs[i].GetValue() == 1):
                    data[0] = i
                    break

        for ctrl in self.data_order:
            if (not ctrl):
                continue
            data.append(ctrl.GetValue())

        # add on the event or not field (not event is fine here)
        data.append(False)

        #print "Checking:", data

        check = self.conv_func(data, 'gen_code', self.name, self.bric_id)
        if (len(check) > 0):
            return True
        else:
            return False

    def save_changes(self):
        # check values first
        if (not self.check_constants()):
            return

        self.conv_func(self.old_data, 'rm_refs', self.name, self.bric_id)
        new_data = self.conv_func(None, 'to_ids_add_refs', self.name, self.bric_id)
        win_data.program().set_bric_data(self.bric_id, new_data)
        self.update_dirty(False)
        self.old_data = new_data
        #print "save_changes:", new_data

    def cancel_changes(self):
        """old_data is already in the correct format for saving, not displaying"""
        #print self.old_data
        values = self.conv_func(self.old_data, 'from_ids', self.name, self.bric_id)
        self.set_control_values(self.data_order, values)
        self.switch_constants()
        if (self.rbs):
            self.switch_group(self.rbs[values[0]])
        self.update_dirty(False)


    def remove_bric_refs(self, name, old_data):
        if (name in self.convert_dict):
            self.convert_dict[name](old_data, 'rm_refs', name, 0)


    def generate_code(self, bric_id, in_event=False):
        name = win_data.program().get_bric_name(bric_id)

        if (name in self.convert_dict):
            data = win_data.program().get_bric_data(bric_id)
            converted = self.convert_dict[name](data, 'from_ids', name, bric_id)
            converted.append(in_event)
            return self.convert_dict[name](converted, 'gen_code', name, bric_id)

        else:
            raise KeyError, "Unknown bric name: %s (id:%d)" % (name, bric_id)

# ------ Alias support so that modules can be presented with different names ---------
# ------ depending on the bric ------------------------------------------------------

    def module_apply_alias(self, module, aliasList):
        for l, r in aliasList:
            if (l == module):
                #print "Applying alias", l, "->", r
                return r
        return module

    def module_apply_aliases(self, moduleList, aliasList):
        newModuleList = []
        for mod in moduleList:
            converted = False
            for l, r in aliasList:
                if (l == mod):
                    #print "Applying alias", l, "->", r
                    newModuleList.append(r)
                    converted = True
            if (not converted):
                newModuleList.append()
        return newModuleList
        
    def module_remove_alias(self, alias, aliasList):
        for l, r in aliasList:
            if (r == alias):
                #print "Removing alias", r, "->", l
                return l
        return alias
    

# =======================================================================================
# ---------------------------- bric details ---------------------------------------------
# =======================================================================================


# ---------------------------- tones bric ---------------------------------------------

    def tones_details(self, bric_id, data):
        self.conv_func = self.tones_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)
        grid_line = 0
        
        rbs = self.make_radio_buttons(["Musical note", "Tune string"])
        modules = win_data.config_device_names('Sounder')
        mod_choice = self.make_combo(modules)


        note_and_dur = (self.make_combo(tone_notes, sort=False),
                        self.make_combo(tone_durations, sort=False))
        note_and_dur[0].SetValue("C")

        tune = (self.make_text_ctrl(""),)

        self.data_order = (None,mod_choice)+note_and_dur+tune
        self.groups = ((rbs[0], note_and_dur), (rbs[1], tune))
        self.vars = None
        self.cons_tc = (tune[0],)
        self.cons_cb = (mod_choice,)+note_and_dur
        self.rbs = rbs

        if (len(modules) < 2):
            mod_choice.Hide()
        else:
            self.add_with_prompt(grid, (grid_line,0), MODULE_PROMPT, (mod_choice,))
            grid_line += 1

        grid.Add(rbs[0], (grid_line,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (grid_line,1), "", note_and_dur)

        grid.Add(rbs[1], (grid_line+1,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (grid_line+1,1), "", tune, ctrl_span=(1,2))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
            self.switch_group(rbs[values[0]])
        else:
            self.switch_constants()
            self.switch_group(rbs[0])
            self.old_data = self.save_initial()

        return grid


    def tones_convert(self, input, command, name, bric_id):
        """Data: radio_button, module, note_cb, dur_cb, tune_const"""
        notes = "mMncCdDefFgGaAborR"

        if (command == 'from_ids'):
            output = [input[0], None, input[2], input[3], input[4]]
            # get names from ids
            # input[1] is the module id
            output[1] = win_data.config_name_from_id(input[1])

            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = [0]
            for i in range(len(self.rbs)):
                if (self.rbs[i].GetValue() == 1):
                    output[0] = i
                    break

            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # Validate values - change notes to codes
            # ??????

            # convert to ids
            output[1] = win_data.config_id_from_name(output[1])
            win_data.config_add_use(output[1])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[1])


        elif (command == 'gen_code'):
            mod = input[1]
            code_lines = []
            if (input[0] == 0):
                # a musical note
                note_code = 0
                for i in range(len(tone_notes)):
                    if (input[2] == tone_notes[i]):
                        note_code = i
                        break

                dur_code = 1
                for i in range(len(tone_durations)):
                    if (tone_durations[i] == input[3]):
                        dur_code = i+1
                        break

                code = "datb @_tune_store * "
                if (note_code > 15):
                    # Make it a rest
                    code += "%d " % ((0x80 + (dur_code << 4)),)
                else:
                    code += "%d " % (((dur_code << 4) + note_code),)
                code += "0"
                code_lines.append(code)
                code_lines.append("movb $0 %s" % (win_data.make_mod_reg(mod, 'tune'),))
                code_lines.append("bitset 0 %s" % (win_data.make_mod_reg(mod, 'action')))

            else:
                # convert the tunes into a string
                code = "datb @_tune_store * "
                pairs = len(input[4])/2
                if (pairs > MAX_TUNE_STORE-1):
                    win_data.constant_error("Too many tune notes/durations (max 16 pairs).")
                    return []

                for i in range(pairs):
                    note = input[4][i*2]
                    dur = input[4][i*2+1]
                    if (dur < '0' or dur > '7'):
                        dur_code = -1
                    else:
                        dur_code = int(dur)

                    note_code = notes.find(note)
                    if (note_code < 0 or note_code > 17 or dur_code < 0):
                        win_data.constant_error("Tune string is not valid. Check help for the format.")
                        return []
                    elif (dur_code == 0 or note_code > 15):
                        # Make it a rest
                        code += "%d " % ((0x80 + (dur_code << 4)),)
                    else:
                        code += "%d " % (((dur_code << 4) + note_code),)

                code += "0"
                code_lines.append(code)
                code_lines.append("movb $0 %s" % (win_data.make_mod_reg(mod, 'tune'),))
                code_lines.append("bitset 0 %s" % (win_data.make_mod_reg(mod, 'action')))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- beep bric ---------------------------------------------

    def beep_details(self, bric_id, data):
        self.conv_func = self.beep_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)
        self.prop_extra_text = bric_data.get_bric_prop_extra_text(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)
        grid_line = 0

        modules = win_data.config_device_names('Sounder')
        mod_choice = self.make_combo(modules)

        self.data_order = (mod_choice,)
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = (mod_choice,)
        self.rbs = None
        
        if (len(modules) < 2):
            mod_choice.Hide()
        else:
            self.add_with_prompt(grid, (grid_line,0), MODULE_PROMPT, (mod_choice,))
            grid_line += 1

        if (self.prop_extra_text):
            # create a multi-line text box
            grid.Add(wx.StaticText(self, -1, self.prop_extra_text), (grid_line+1, 0),
                     span=(2,2), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTRE_VERTICAL)
            
        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def beep_convert(self, input, command, name, bric_id):
        """Data: module"""

        if (command == 'from_ids'):
            output = [input[0]]
            output[0] = win_data.config_name_from_id(input[0])
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = win_data.config_id_from_name(output[0])
            win_data.config_add_use(output[0])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[0])

        elif (command == 'gen_code'):
            return ["bitset 2 %s" % (win_data.make_mod_reg(input[0], 'action'),)]

        else:
            raise SyntaxError, "Unknown command: " + command



# ---------------------------- digital, ctrlled, linetracker, onstacle detect brics ----------------------------------------

    def digital_details(self, bric_id, data):
        self.conv_func = self.digital_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)
        #print self.prop_title

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)
        grid_line = 0
        
        if (self.name == 'LED'):
            mod_type = 'LED'
            levels = ['On', 'Off']
            prompt = "LED Setting:"

        elif (self.name == "Obstacle Detection"):
            mod_type = 'IR Transmitter'
            levels = ['On', 'Off']
            prompt = "IR Transmitter obstacle detection:"
        else:
            mod_type = 'Line Tracker'
            levels = ['On', 'Off']
            prompt = "Line Tracker LED:"

        modules = win_data.config_device_names(mod_type)
        mod_choice = self.make_combo(modules)
        
        choices = win_data.vars_names(U_NAME)
        ctrl = (self.make_combo(levels),
                 self.make_combo(choices, add_const=True))

        self.data_order = (mod_choice,)+ctrl
        self.groups = None
        self.vars = ((ctrl[1], ctrl[0]),)
        self.cons_tc = None
        self.cons_cb = (ctrl[0], mod_choice)
        self.rbs = None

        if (len(modules) < 2):
            mod_choice.Hide()
        else:
            self.add_with_prompt(grid, (grid_line,0), MODULE_PROMPT, (mod_choice,))
            grid_line += 1

        self.make_headings(grid, (grid_line,1))
        grid_line += 1
        
        self.add_with_prompt(grid, (grid_line,0), prompt, ctrl)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
        else:
            self.switch_constants()
            self.old_data = self.save_initial()

        return grid


    def digital_convert(self, input, command, name, bric_id):
        """Data: module, output_level, var"""

        if (command == 'from_ids'):
            output= [win_data.config_name_from_id(input[0]), input[1], CONSTANT]
            if (input[2]):
                output[2] = win_data.vars_get_name(input[2])

            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = win_data.config_id_from_name(output[0])
            output[2] = win_data.vars_get_id(output[2])
            win_data.config_add_use(output[0])
            win_data.vars_add_use(output[2])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[0])
            win_data.vars_rm_use(input[2])

        elif (command == 'gen_code'):
            code_lines = []
            if (name == "Obstacle Detection"):
                output = "action"
            else:
                output = "output"

            #print "digital_convert - self.name:", self.name, "name:", name, " output:", output

            if (name == "Obstacle Detection"):
                bit = 1
                mask = 2
            else:
                bit = 0
                mask = 1

            if (input[2] == CONSTANT):
                if (input[1] == 'Off'):
                    code_lines.append("bitclr $%d %s" % (bit, win_data.make_mod_reg(input[0], output)))
                else:
                    code_lines.append("bitset $%d %s" % (bit, win_data.make_mod_reg(input[0], output)))

            else:
                labels = win_data.make_labels(bric_id, 0, 2)
                code_lines.append("movb @%s %%_cpu:acc" % (input[2]))
                code_lines.append("and $%d" % (mask,))
                code_lines.append("brz %s" % (labels[0],))  # branch if setting to 0
                # this code if setting to 1
                code_lines.append("bitset $%d %s" % (bit, win_data.make_mod_reg(input[0], output)))
                code_lines.append("bra %s" % (labels[1],))
                code_lines.append(labels[0])
                # handle setting to 0
                code_lines.append("bitclr $%d %s" % (bit, win_data.make_mod_reg(input[0], output)))
                code_lines.append(labels[1])

            if (name == "Obstacle Detection"):
                # clear the register bits as they are from a previous detection or program run
                code_lines.append("bitclr $3 %s" % (win_data.make_mod_reg("IR_RECEIVER1", 'status'),))
                code_lines.append("bitclr $4 %s" % (win_data.make_mod_reg("IR_RECEIVER1", 'status'),))
                code_lines.append("bitclr $5 %s" % (win_data.make_mod_reg("IR_RECEIVER1", 'status'),))
                code_lines.append("bitclr $6 %s" % (win_data.make_mod_reg("IR_RECEIVER1", 'status'),))
            
            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- CPU bric ----------------------------------------

    def cpu_details(self, bric_id, data):
        self.conv_func = self.cpu_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        sleep_choices = ['on inactivity', 'never']
        #stop_choices = ['warnings', 'errors']

        sleep = (self.make_combo(sleep_choices, sort=False, size=(150,-1)),)
        #stop = (self.make_combo(stop_choices, sort=False),)

        self.data_order = sleep
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = sleep
        self.rbs = None

        self.add_with_prompt(grid, (1,0), "Sleep:", sleep)
        #self.add_with_prompt(grid, (2,0), "Stop on:", stop)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def cpu_convert(self, input, command, name, bric_id):
        """Data: sleep"""

        if (command == 'from_ids'):
            return input

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            return

        elif (command == 'gen_code'):
            code_lines = []
            if (input[0] == 'never'):
                code_lines.append("bitset 2 %_timers:action")
            else:
                code_lines.append("bitclr 2 %_timers:action")

##            if (input[1] == 'errors'):
##                # Only stop on error, therefore continue on warnings
##                code_lines.append("movb $1 %_cpu:cow")
##            else:
##                code_lines.append("movb $0 %_cpu:cow")

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- TxIR bric ----------------------------------------

    def txir_details(self, bric_id, data):
        self.conv_func = self.txir_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)
        grid_line = 0
        
        mod_type = 'IR Transmitter'
        prompt = "Character to send:"

        modules = win_data.config_device_names(mod_type)
        mod_choice = self.make_combo(modules)

        choices = win_data.vars_names(U_NAME)
        ctrl = (self.make_text_ctrl("A"),
                 self.make_combo(choices, add_const=True))


        self.data_order = (mod_choice,)+ctrl
        self.groups = None
        self.vars = ((ctrl[1], ctrl[0]),)
        self.cons_tc = (ctrl[0],)
        self.cons_cb = (mod_choice,)
        self.rbs = None

        if (len(modules) < 2):
            mod_choice.Hide()
        else:
            self.add_with_prompt(grid, (grid_line,0), MODULE_PROMPT, (mod_choice,))
            grid_line += 1

        self.make_headings(grid, (grid_line,1))
        self.add_with_prompt(grid, (grid_line+1,0), prompt, ctrl)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
        else:
            self.switch_constants()
            self.old_data = self.save_initial()

        return grid


    def txir_convert(self, input, command, name, bric_id):
        """Data: module, char-cons, char-var"""

        if (command == 'from_ids'):
            output= [win_data.config_name_from_id(input[0]), input[1], CONSTANT]
            if (input[2]):
                output[2] = win_data.vars_get_name(input[2])

            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = win_data.config_id_from_name(output[0])
            output[2] = win_data.vars_get_id(output[2])
            win_data.config_add_use(output[0])
            win_data.vars_add_use(output[2])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[0])
            win_data.vars_rm_use(input[2])

        elif (command == 'gen_code'):
            code_lines = []
            if (input[2] == CONSTANT):
                character = win_data.conv_to_tx_char(input[1])

                if (character == None):
                    return []

                code_lines.append("movb $%s %s" % (character, win_data.make_mod_reg(input[0], 'char')))
            else:
                code_lines.append("movb @%s %s" % (input[2], win_data.make_mod_reg(input[0], 'char')))

            code_lines.append("bitset 0 %s" % (win_data.make_mod_reg(input[0], 'action')))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- Txserial bric ----------------------------------------

    def txserial_details(self, bric_id, data):
        self.conv_func = self.txserial_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        if (self.name == 'Serial Data Out'):
            prompt = "Character to send:"
        else:
            pass

        choices = win_data.vars_names(U_NAME)
        ctrl = (self.make_text_ctrl("A"),
                 self.make_combo(choices, add_const=True))


        self.data_order = ctrl
        self.groups = None
        self.vars = ((ctrl[1], ctrl[0]),)
        self.cons_tc = (ctrl[0],)
        self.cons_cb = None
        self.rbs = None

        self.make_headings(grid, (0,1))
        self.add_with_prompt(grid, (1,0), prompt, ctrl)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
        else:
            self.switch_constants()
            self.old_data = self.save_initial()

        return grid


    def txserial_convert(self, input, command, name, bric_id):
        """Data: char-const, char-var"""

        if (command == 'from_ids'):
            output= [input[0], CONSTANT]
            if (input[1]):
                output[1] = win_data.vars_get_name(input[1])

            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[1] = win_data.vars_get_id(output[1])
            win_data.vars_add_use(output[1])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.vars_rm_use(input[1])

        elif (command == 'gen_code'):
            code_lines = []
            if (input[1] == CONSTANT):
                character = win_data.conv_to_tx_char(input[0])
                if (character == None):
                    return []
                code_lines.append("movb $%s %%_devices:sertx" % (character,))
            else:
                code_lines.append("movb @%s %%_devices:sertx" % (input[1],))

            code_lines.append("bitset 5 %_devices:action")

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# --------------  Linestatus, Digital Level, bumperstatus, RxIR and Analog Level brics --------------------

    def readsmall_details(self, bric_id, data):
        self.conv_func = self.readsmall_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)
        grid_line = 0
        
        if (self.name == 'Digital In'):
            mod_type = 'Digital In'
            v_type = U_NAME
        elif (self.name == 'Bumper'):
            mod_type = 'Bump'
            v_type = U_NAME
        elif (self.name == 'Infrared Data In' or self.name == 'Remote'):
            mod_type = 'IR Receiver'
            v_type = U_NAME
        elif (self.name == 'Analogue In'):
            mod_type = 'Analog In'
            v_type = S_NAME
        elif (self.name == 'Light Level'):
            mod_type = 'Line Tracker'
            v_type = S_NAME
        elif (self.name == 'Read Clap Detect'):
            mod_type = 'Sounder'
            v_type = U_NAME
        elif (self.name == 'Read Obstacle Detect'):
            mod_type = 'IR Receiver'
            v_type = U_NAME
        else:
            # Line status
            mod_type = 'Line Tracker'
            v_type = U_NAME
            clearAfterReading = False

        modules = win_data.config_device_names(mod_type)
        mod_choice = self.make_combo(modules)

        choices = win_data.vars_names(v_type)
        ctrl = self.make_combo(choices, add_const=False)

        # debug
        #print "readsmall_details:", self.name, mod_type, modules

        self.data_order = (mod_choice, ctrl)
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = (mod_choice,ctrl)
        self.rbs = None

        if (len(modules) < 2):
            mod_choice.Hide()
        else:
            self.add_with_prompt(grid, (grid_line,0), MODULE_PROMPT, (mod_choice,))
            grid_line += 1

        self.add_with_prompt(grid, (grid_line,0), "Variable to read into:", (ctrl,))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def readsmall_convert(self, input, command, name, bric_id):
        """Data: mod, var"""

        if (command == 'from_ids'):
            output= [win_data.config_name_from_id(input[0]), win_data.vars_get_name(input[1])]
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = win_data.config_id_from_name(output[0])
            output[1] = win_data.vars_get_id(output[1])
            win_data.config_add_use(output[0])
            win_data.vars_add_use(output[1])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[0])
            win_data.vars_rm_use(input[1])

        elif (command == 'gen_code'):
            code_lines = []
            if (name == 'Digital In'):
                #code_lines.append("movb %s @%s" % (win_data.make_mod_reg(input[0], 'status'), input[1]))
                # if we have math then do the below
                code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(input[0], 'status'),))
                code_lines.append("and $1")
                code_lines.append("movb %%_cpu:acc @%s" % (input[1]))

            elif (name == 'Bumper'):
                #code_lines.append("movb %s @%s" % (win_data.make_mod_reg(input[0], 'status'), input[1]))
                # if we have math then do the below
                code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(input[0], 'status'),))
                code_lines.append("and $1")
                code_lines.append("movb %%_cpu:acc @%s" % (input[1]))

            elif (name == 'Infrared Data In'):
                # read the actual character in (which may be 0)
                code_lines.append("movb %s @%s" % (win_data.make_mod_reg(input[0], 'char'), input[1]))

                # clear the data so that the next read won't return the same data
                code_lines.append("movb $0 %s" % (win_data.make_mod_reg(input[0], 'char')))

                # Have to clear the status bit for IR received
                code_lines.append("bitclr $0 %s" % (win_data.make_mod_reg(input[0], 'status'),))

            elif (name == 'Remote'):
                # read the match (which may be 0)
                code_lines.append("movb %s @%s" % (win_data.make_mod_reg(input[0], 'match'), input[1]))

                # clear the data so that the next read won't return the same data
                code_lines.append("movb $0 %s" % (win_data.make_mod_reg(input[0], 'match')))

                # Have to clear the status bit for the remote match
                code_lines.append("bitclr $1 %s" % (win_data.make_mod_reg(input[0], 'status'),))

            elif (name == 'Analogue In'):
                code_lines.append("movw %s @%s" % (win_data.make_mod_reg(input[0], 'level'), input[1]))

            elif (name == 'Light Level'):
                code_lines.append("movw %s @%s" % (win_data.make_mod_reg(input[0], 'level'), input[1]))

            elif (name == 'Read Clap Detect'):
                code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(input[0], 'status'),))

                # clear the register bits now that we've captured them
                code_lines.append("bitclr $2 %s" % (win_data.make_mod_reg(input[0], 'status'),))

                code_lines.append("and $4")
                code_lines.append("movb %%_cpu:acc @%s" % (input[1]))

            elif (name == 'Read Obstacle Detect'):
                code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(input[0], 'status'),))

                # clear the register bits now that we've captured them
                code_lines.append("bitclr $3 %s" % (win_data.make_mod_reg(input[0], 'status'),))
                code_lines.append("bitclr $4 %s" % (win_data.make_mod_reg(input[0], 'status'),))
                code_lines.append("bitclr $5 %s" % (win_data.make_mod_reg(input[0], 'status'),))
                code_lines.append("bitclr $6 %s" % (win_data.make_mod_reg(input[0], 'status'),))

                code_lines.append("and $78/16")
                code_lines.append("movb %%_cpu:acc @%s" % (input[1]))

                ## alternate implementation
                #code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(input[0], 'status'),))
                ## move into variable before anding so can use for clearing too
                #code_lines.append("movb %%_cpu:acc @%s" % (input[1]))
                #code_lines.append("and $87/16")
                ## save the cleared data back into the register
                #code_lines.append("movb %%_cpu:acc %s" % (win_data.make_mod_reg(input[0], 'status'),))

                ## get the original value back, and 'and' it
                #code_lines.append("movb  @%s %%_cpu:acc" % (input[1]))
                #code_lines.append("and $78/16")
                #code_lines.append("movb %%_cpu:acc @%s" % (input[1]))

            else:
                # line tracker
                #code_lines.append("movb %s @%s" % (win_data.make_mod_reg(input[0], 'status'), input[1]))
                # if we have math then do the below
                code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(input[0], 'status'),))
                code_lines.append("and $1")
                code_lines.append("movb %%_cpu:acc @%s" % (input[1]))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command

# -------------- Read Light details  --------------------

    def readlight_details(self, bric_id, data):
        self.conv_func = self.readlight_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)
        self.module_aliases = [("Left_LED", "Left light level"), ("Right_LED", "Right light level"),
                               ("LINE_TRACKER1", "Line light level")]

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        modules = win_data.config_device_names("LED")
        modules.extend(win_data.config_device_names('Line Tracker'))

        # convert to use aliases
        modules = self.module_apply_aliases(modules, self.module_aliases)
        
        mod_choice = self.make_combo(modules)

        choices = win_data.vars_names(S_NAME)
        ctrl = self.make_combo(choices, add_const=False)

        self.data_order = (mod_choice, ctrl)
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = (mod_choice,ctrl)
        self.rbs = None

        self.add_with_prompt(grid, (0,0), "Sense:", (mod_choice,))
        self.add_with_prompt(grid, (1,0), "Variable to read into:", (ctrl,))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def readlight_convert(self, input, command, name, bric_id):
        """Data: mod, var"""
        #print "readlight_convert", bric_id, command, name, input

        if (command == 'from_ids'):
            output= [win_data.config_name_from_id(input[0]), win_data.vars_get_name(input[1])]
            output[0] = self.module_apply_alias(output[0], self.module_aliases)
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = self.module_remove_alias(output[0], self.module_aliases)
            output[0] = win_data.config_id_from_name(output[0])
            output[1] = win_data.vars_get_id(output[1])
            win_data.config_add_use(output[0])
            win_data.vars_add_use(output[1])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[0])
            win_data.vars_rm_use(input[1])

        elif (command == 'gen_code'):
            code_lines = []
            input[0] = self.module_remove_alias(input[0], self.module_aliases)
            code_lines.append("movw %s @%s" % (win_data.make_mod_reg(input[0], 'lightlevel'), input[1]))
            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command

# -------------- Read Motor distance details  --------------------

            
    def readdist_details(self, bric_id, data):
        #print "readdist_details", bric_id, data
        self.conv_func = self.readdist_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)
        self.module_aliases = [("Left_Motor", "Left drive"), ("Right_Motor", "Right drive")]
                                  
        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        modules = []
        modules.extend(win_data.config_device_names('Motor A'))
        modules.extend(win_data.config_device_names('Motor B'))

        # convert to use aliases
        modules = self.module_apply_aliases(modules, self.module_aliases)

        mod_choice = self.make_combo(modules)

        choices = win_data.vars_names(S_NAME)
        ctrl = self.make_combo(choices, add_const=False)

        self.data_order = (mod_choice, ctrl)
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = (mod_choice,ctrl)
        self.rbs = None

        self.add_with_prompt(grid, (0,0), "Read distance from:", (mod_choice,))
        self.add_with_prompt(grid, (1,0), "Variable to read into:", (ctrl,))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def readdist_convert(self, input, command, name, bric_id):
        """Data: mod, var"""
        #print "readdist_convert", bric_id, command, name, input

        if (command == 'from_ids'):
            output= [win_data.config_name_from_id(input[0]), win_data.vars_get_name(input[1])]
            output[0] = self.module_apply_alias(output[0], self.module_aliases)
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = self.module_remove_alias(output[0], self.module_aliases)
            output[0] = win_data.config_id_from_name(output[0])
            output[1] = win_data.vars_get_id(output[1])
            win_data.config_add_use(output[0])
            win_data.vars_add_use(output[1])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[0])
            win_data.vars_rm_use(input[1])

        elif (command == 'gen_code'):
            code_lines = []
            code_lines.append("movw %s @%s" % (win_data.make_mod_reg(input[0], 'distance'), input[1]))
            return code_lines
        else:
            raise SyntaxError, "Unknown command: " + command


# ----------------- Rxserial and button brics ----------------------------------------

    def readinternal_details(self, bric_id, data):
        self.conv_func = self.readinternal_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        if (self.name == 'Serial Data In'):
            extra = 'Last character received'
            v_type = U_NAME
        elif (self.name == 'Read Timer'):
            extra = 'Timer value'
            v_type = S_NAME
        else:
            extra = 'Button pressed'
            v_type = U_NAME

        choices = win_data.vars_names(v_type)
        ctrl = self.make_combo(choices, add_const=False)

        self.data_order = (ctrl,)
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = (ctrl,)
        self.rbs = None

        self.add_with_prompt(grid, (0,0), "Variable to read into:", (ctrl,), extra_info=extra)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def readinternal_convert(self, input, command, name, bric_id):
        """Data: var"""

        if (command == 'from_ids'):
            output= [win_data.vars_get_name(input[0])]
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = win_data.vars_get_id(output[0])
            win_data.vars_add_use(output[0])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.vars_rm_use(input[0])

        elif (command == 'gen_code'):
            code_lines = []
            if (name == 'Serial Data In'):
                code_lines.append("movb %%_devices:serrx @%s" % (input[0],))

            elif (name == 'Read Timer'):
                code_lines.append("movw %%_timers:oneshot @%s" % (input[0],))

            else:
                # Button
                code_lines.append("movb %%_devices:button @%s" % (input[0],))
                code_lines.append("movb $0 %_devices:button")

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- Set Timer bric ----------------------------------------

    def settimer_details(self, bric_id, data):
        self.conv_func = self.settimer_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        if (self.name == 'Set Timer'):
            prompt = "Seconds:"
            extra_info = "Range is 0.00 to 327.67 seconds."
        else:
            pass

        choices = win_data.vars_names(S_NAME)
        ctrl = (self.make_text_ctrl("0"),
                 self.make_combo(choices, add_const=True))

        self.data_order = ctrl
        self.groups = None
        self.vars = ((ctrl[1], ctrl[0]),)
        self.cons_tc = (ctrl[0],)
        self.cons_cb = None
        self.rbs = None

        self.make_headings(grid, (0,1))
        self.add_with_prompt(grid, (1,0), prompt, ctrl, extra_info=extra_info)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
        else:
            self.switch_constants()
            self.old_data = self.save_initial()

        return grid


    def settimer_convert(self, input, command, name, bric_id):
        """Data: output_time, var"""

        if (command == 'from_ids'):
            output= [input[0], CONSTANT]
            if (input[1]):
                output[1] = win_data.vars_get_name(input[1])

            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[1] = win_data.vars_get_id(output[1])
            win_data.vars_add_use(output[1])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.vars_rm_use(input[1])

        elif (command == 'gen_code'):
            code_lines = []
            if (input[1] == CONSTANT):
                time = win_data.conv_to_time(input[0])
                if (time == None):
                    return []

                code_lines.append("movw $%d %%_timers:oneshot" % (time,))
            else:
                code_lines.append("movw @%s %%_timers:oneshot" % (input[1],))

            code_lines.append("bitset 0 %_timers:action")

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# --------------  Digital Pulse brics --------------------

    def digpulse_details(self, bric_id, data):
        self.conv_func = self.digpulse_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        modules = win_data.config_device_names('Digital In')
        mod_choice = self.make_combo(modules)

        choices = win_data.vars_names(S_NAME)

        wait = (self.make_text_ctrl("0"),
                 self.make_combo(choices, add_const=True))

        choices = win_data.vars_names(S_NAME)
        ctrl = (wx.StaticText(self, -1, ""),
            self.make_combo(choices, add_const=False))


        self.data_order = (mod_choice,)+wait+(ctrl[1],)
        self.groups = None
        self.vars = ((wait[1],wait[0]),)
        self.cons_tc = (wait[0],)
        self.cons_cb = (mod_choice, ctrl[1])
        self.rbs = None

        self.add_with_prompt(grid, (0,0), MODULE_PROMPT, (mod_choice,))
        self.make_headings(grid, (1,1))
        self.add_with_prompt(grid, (2,0), "Max time to wait:", wait)
        self.add_with_prompt(grid, (3,0), "Variable for pulse time:", ctrl,
                             extra_info="Range for times is 0.00 to 327.67")

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
        else:
            self.switch_constants()
            self.old_data = self.save_initial()

        return grid


    def digpulse_convert(self, input, command, name, bric_id):
        """Data: module, wait, var, read_var"""

        if (command == 'from_ids'):
            output= [win_data.config_name_from_id(input[0]), input[1],
                     CONSTANT, win_data.vars_get_name(input[3])]
            if (input[2]):
                output[2] = win_data.vars_get_name(input[2])

            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = win_data.config_id_from_name(output[0])
            output[2] = win_data.vars_get_id(output[2])
            output[3] = win_data.vars_get_id(output[3])

            win_data.config_add_use(output[0])
            win_data.vars_add_use(output[2])
            win_data.vars_add_use(output[3])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[0])
            win_data.vars_rm_use(input[2])
            win_data.vars_rm_use(input[3])

        elif (command == 'gen_code'):
            code_lines = []
            if (input[2] == CONSTANT):
                time = win_data.conv_to_time(input[1])
                if (time == None):
                    return []

                code_lines.append("movw $%d %s" % (time, win_data.make_mod_reg(input[0], 'pulsetime')))
            else:
                code_lines.append("movw @%s %s" % (input[2], win_data.make_mod_reg(input[0], 'pulsetime')))

            # trigger the capture
            code_lines.append("bitset 0 %s" % (win_data.make_mod_reg(input[0], 'action'),))

            # code to wait around for the end of the capture
            labels = win_data.make_labels(bric_id, 0, 3)
            code_lines.append(labels[0])
            code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(input[0], 'status'),))
            code_lines.append("andb $0x08")
            code_lines.append("brz %s" % (labels[0],))
            # capture finished
            code_lines.append("bitclr 3 %s" % (win_data.make_mod_reg(input[0], 'status'),))
            code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(input[0], 'status'),))
            code_lines.append("andb $0x02")
            code_lines.append("brnz %s" % (labels[1],))
            # capture failed
            code_lines.append("movw $-1 @%s" % (input[3],))
            code_lines.append("bra %s" % (labels[2],))
            code_lines.append(labels[1])
            # good capture
            code_lines.append("movw %s @%s" % (win_data.make_mod_reg(input[0], 'pulsetime'),input[3]))
            code_lines.append(labels[2])

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command

# ---------------------------- digital out Bric ----------------------------------------

    def digout_details(self, bric_id, data):
        self.conv_func = self.digout_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        rbs = self.make_radio_buttons(["Level", "Pulse"])

        modules = win_data.config_device_names("Digital Out")
        mod_choice = self.make_combo(modules)

        level_choices = win_data.vars_names(U_NAME)
        pulse_choices = win_data.vars_names(S_NAME)

        levels = ['Low', 'High']
        ctrl = (self.make_combo(levels),
                 self.make_combo(level_choices, add_const=True))

        pulse = (self.make_text_ctrl("0"),
                 self.make_combo(pulse_choices, add_const=True))

        self.data_order = (None,mod_choice)+ctrl+pulse
        self.groups = ((rbs[0], ctrl), (rbs[1], pulse))
        self.vars = ((ctrl[1], ctrl[0]), (pulse[1], pulse[0]))
        self.cons_tc = (pulse[0],)
        self.cons_cb = (ctrl[0], mod_choice)
        self.rbs = rbs

        self.add_with_prompt(grid, (0,1), MODULE_PROMPT, (mod_choice,))
        self.make_headings(grid, (1,2))

        grid.Add(rbs[0], (2,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (2,1), "Output Level:", ctrl)

        grid.Add(rbs[1], (4,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (4,1), "Duration:", pulse)

        self.bind_event_handlers()


        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
            self.switch_group(rbs[values[0]])
        else:
            self.switch_constants()
            self.switch_group(rbs[0])
            self.old_data = self.save_initial()

        return grid


    def digout_convert(self, input, command, name, bric_id):
        """Data: rb, module, output_level, var, time-cons, time-var"""

        vars = [(0, 3), (1, 5)]
        if (command == 'from_ids'):
            output= [input[0], win_data.config_name_from_id(input[1]), input[2], CONSTANT,
                     input[4], CONSTANT]

            for rb, index in vars:
                if (output[0] == rb):
                    if (input[index]):
                        output[index] = win_data.vars_get_name(input[index])

            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = [0]
            for i in range(len(self.rbs)):
                if (self.rbs[i].GetValue() == 1):
                    output[0] = i
                    break

            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[1] = win_data.config_id_from_name(output[1])
            win_data.config_add_use(output[1])
            for rb, index in vars:
                if (output[0] == rb):
                    output[index] = win_data.vars_get_id(output[index])
                    win_data.vars_add_use(output[index])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[1])
            for rb, index in vars:
                if (input[0] == rb):
                    win_data.vars_rm_use(input[index])

        elif (command == 'gen_code'):
            code_lines = []
            if (input[0] == 0):
                # level control
                value = 1
                if (input[3] == CONSTANT):
                    if (input[2] == 'Low'):
                        value = 0

                    code_lines.append("movb $%d %s" % (value, (win_data.make_mod_reg(input[1], 'output'))))
                else:
                    code_lines.append("movb @%s %s" % (input[3], (win_data.make_mod_reg(input[1], 'output'))))
            else:
                # pulse
                if (input[5] == CONSTANT):
                    time = win_data.conv_to_time(input[4])
                    if (time == None):
                        return []

                    code_lines.append("movw $%d %s" % (time, (win_data.make_mod_reg(input[1], 'pulsetime'))))
                else:
                    code_lines.append("movw @%s %s" % (input[5], (win_data.make_mod_reg(input[1], 'pulsetime'))))

                code_lines.append("bitset 0 %s" % (win_data.make_mod_reg(input[1], 'action')))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- Inc and Dec brics ----------------------------------------

    def incdec_details(self, bric_id, data):
        self.conv_func = self.incdec_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        if (self.name == 'Increment'):
            prompt = "Plus 1 to variable"
        else:
            prompt = "Minus 1 from variable"

        choices = win_data.vars_names()
        ctrl = self.make_combo(choices, add_const=False)

        self.data_order = (ctrl,)
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = (ctrl,)
        self.rbs = None

        self.add_with_prompt(grid, (0,0), prompt, (ctrl,))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def incdec_convert(self, input, command, name, bric_id):
        """Data: var"""

        if (command == 'from_ids'):
            output= [win_data.vars_get_name(input[0])]
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = win_data.vars_get_id(output[0])
            win_data.vars_add_use(output[0])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.vars_rm_use(input[0])

        elif (command == 'gen_code'):
            code_lines = []
            size = win_data.vars_get_type_letter_from_name(input[0])
            if (name == 'Increment'):
                code_lines.append("inc%s @%s" % (size, input[0]))
            else:
                code_lines.append("dec%s @%s" % (size, input[0]))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command



# ---------------------------- Variable Set bric ----------------------------------------

    def varset_details(self, bric_id, data):
        self.conv_func = self.varset_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        choices = win_data.vars_names()
        value = self.make_text_ctrl("0")
        var = self.make_combo(choices, add_const=False)

        self.data_order = (value, var)
        self.groups = None
        self.vars = None
        self.cons_tc = (value,)
        self.cons_cb = (var,)
        self.rbs = None

        self.add_with_prompt(grid, (0,0), "Value:", (value,))
        self.add_with_prompt(grid, (1,0), "Variable to set:", (var,))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def varset_convert(self, input, command, name, bric_id):
        """Data: value, var"""

        if (command == 'from_ids'):
            output= [input[0], win_data.vars_get_name(input[1])]
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[1] = win_data.vars_get_id(output[1])
            win_data.vars_add_use(output[1])
            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.vars_rm_use(input[1])

        elif (command == 'gen_code'):
            code_lines = []
            size = win_data.vars_get_type_letter_from_name(input[1])
            number = win_data.conv_to_number(input[0], size)
            if (number == None):
                return []
            code_lines.append("mov%s $%s @%s" % (size, input[0], input[1]))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- Variable Copy bric ----------------------------------------

    def varcopy_details(self, bric_id, data):
        self.conv_func = self.varcopy_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        choices = win_data.vars_names()
        copy_from = self.make_combo(choices, add_const=False)
        copy_to = self.make_combo(choices, add_const=False)

        self.data_order = (copy_from, copy_to)
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = (copy_from, copy_to)
        self.rbs = None

        self.add_with_prompt(grid, (0,0), "Copy data from variable:", (copy_from,))
        self.add_with_prompt(grid, (1,0), "Copy data to variable:", (copy_to,))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def varcopy_convert(self, input, command, name, bric_id):
        """Data: var, var"""

        if (command == 'from_ids'):
            output= [win_data.vars_get_name(input[0]), win_data.vars_get_name(input[1])]
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # convert to ids
            output[0] = win_data.vars_get_id(output[0])
            output[1] = win_data.vars_get_id(output[1])
            win_data.vars_add_use(output[0])
            win_data.vars_add_use(output[1])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.vars_rm_use(input[0])
            win_data.vars_rm_use(input[1])

        elif (command == 'gen_code'):
            code_lines = []
            size0 = win_data.vars_get_type_letter_from_name(input[0])
            size1 = win_data.vars_get_type_letter_from_name(input[1])

            if (size0 == size1):
                code_lines.append("mov%s @%s @%s" % (size0, input[0], input[1]))
            elif (size0 == 'b'):
                # 16bit to 8bit
                code_lines.append("movb @%s %%_cpu:acc" % (input[0],))
                code_lines.append("conv")
                code_lines.append("movw %%_cpu:acc @%s" % (input[1],))
            else:
                # 8bit to 16bit
                code_lines.append("movw @%s %%_cpu:acc" % (input[0],))
                code_lines.append("convl")
                code_lines.append("movb %%_cpu:acc @%s" % (input[1],))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- Motor Pairs, Motors brics ----------------------------------------

    def motor_pair_directions(self, motors, command):
        locs = (win_data.config_loc_from_name(motors[0]),
                win_data.config_loc_from_name(motors[1]))
        dtypes = (win_data.config_get(locs[0])[0],
                  win_data.config_get(locs[1])[0])

        dirs = [0,0]
        codes = [0,0]
        right_most = -1

        for i in range(len(locs)):
            if (dtypes[i] == "Motor A"):
                if (locs[i] in [2, 3, 4, 5, 6]):
                    dirs[i] = 1
                    right_most = i
                elif (locs[i] in [8, 9, 10, 11, 0]):
                    dirs[i] = -1
                elif (locs[i] == 1):
                    dirs[i] = -1 * win_data.config_orient_from_loc(1)
                else:
                    dirs[i] = win_data.config_orient_from_loc(locs[i])

            else:
                if (locs[i] in [2, 3, 4, 5, 6]):
                    dirs[i] = -1
                    right_most = i
                elif (locs[i] in [8, 9, 10, 11, 0]):
                    dirs[i] = 1
                elif (locs[i] == 1):
                    dirs[i] = win_data.config_orient_from_loc(i)
                else:
                    dirs[i] = -1 * win_data.config_orient_from_loc(locs[i])

        if (right_most < 0):
            # must be a corner case
            if (locs[0] == 1 and win_data.config_orient_from_loc(1) == -1):
                right_most = 0
            elif (locs[0] == 7 and win_data.config_orient_from_loc(1) == 1):
                right_most = 0
            elif (locs[1] == 1 and win_data.config_orient_from_loc(1) == 1):
                right_most = 1
            else:
                #elif (locs[1] == 7 and win_data.config_orient_from_loc(1) == 1):
                right_most = 1

        #print "Motor pairs: %s locs:%s dirs:%s" % (motors, locs, dirs)

        left_most = 0
        if (right_most == 0):
            left_most = 1


        # dirs now has -1 or 1 for each motor
        if (command == MOTOR_STP):
            codes = [MOTOR_CODE["S"], MOTOR_CODE["S"]]
        elif (command == MOTOR_FWD):
            for i in (0, 1):
                if (dirs[i] == 1):
                    codes[i] = MOTOR_CODE["F"]
                else:
                    codes[i] = MOTOR_CODE["B"]

        elif (command == MOTOR_BCK):
            for i in (0, 1):
                if (dirs[i] == 1):
                    codes[i] = MOTOR_CODE["B"]
                else:
                    codes[i] = MOTOR_CODE["F"]

        elif (command == MOTOR_P_RT):
            codes[right_most] = MOTOR_CODE["S"]
            if (dirs[left_most] == 1):
                codes[left_most] = MOTOR_CODE["F"]
            else:
                codes[left_most] = MOTOR_CODE["B"]

        elif (command == MOTOR_P_SR):
            if (dirs[left_most] == 1):
                codes[left_most] = MOTOR_CODE["F"]
                codes[right_most] = MOTOR_CODE["B"]
            else:
                codes[left_most] = MOTOR_CODE["B"]
                codes[right_most] = MOTOR_CODE["F"]

        elif (command == MOTOR_P_LT):
            codes[left_most] = MOTOR_CODE["S"]
            if (dirs[right_most] == 1):
                codes[right_most] = MOTOR_CODE["F"]
            else:
                codes[right_most] = MOTOR_CODE["B"]

        elif (command == MOTOR_P_SL):
            if (dirs[right_most] == 1):
                codes[right_most] = MOTOR_CODE["F"]
                codes[left_most] = MOTOR_CODE["B"]
            else:
                codes[right_most] = MOTOR_CODE["B"]
                codes[left_most] = MOTOR_CODE["F"]

        elif (command == MOTOR_P_BR):
            codes[right_most] = MOTOR_CODE["S"]
            if (dirs[left_most] == 1):
                codes[left_most] = MOTOR_CODE["B"]
            else:
                codes[left_most] = MOTOR_CODE["F"]

        elif (command == MOTOR_P_BL):
            codes[left_most] = MOTOR_CODE["S"]
            if (dirs[right_most] == 1):
                codes[right_most] = MOTOR_CODE["B"]
            else:
                codes[right_most] = MOTOR_CODE["F"]

        elif (command == MOTOR_P_RT_90):
            if (dirs[left_most] == 1):
                codes[left_most] = MOTOR_CODE["FD"]
                codes[right_most] = MOTOR_CODE["BD"]
            else:
                codes[left_most] = MOTOR_CODE["BD"]
                codes[right_most] = MOTOR_CODE["FD"]

        elif (command == MOTOR_P_LT_90):
            if (dirs[right_most] == 1):
                codes[right_most] = MOTOR_CODE["FD"]
                codes[left_most] = MOTOR_CODE["BD"]
            else:
                codes[right_most] = MOTOR_CODE["BD"]
                codes[left_most] = MOTOR_CODE["FD"]


        #print "Motorpairdir", motors[left_most], motors[right_most], dirs, command, codes
        return codes

    def motor_special_cb_change(self):
        # a combo box has changed
        # If direction isn't stop or coast and it's not done with a variable then
        # possibly enable the distance cbs
        dirs = self.cb_special_vars[0]
        dist_units = self.cb_special_vars[1]
        dist_value = self.cb_special_vars[2]

        if (dirs[0].GetValue() in (MOTOR_STP, MOTOR_P_RT_90, MOTOR_P_LT_90)) and (dirs[1].GetValue() == CONSTANT):
            dist_units[0].Enable(False)
            dist_value[0].Enable(False)
            dist_value[1].Enable(False)
        else:
            dist_units[0].Enable(True)
            e1,e2 = True, False
            if (dist_units[0].GetValue().startswith("Unlimited")):
                e1,e2 = False, False
                dist_value[1].SetValue(CONSTANT)
            elif (dist_units[0].GetValue().startswith("Raw")):
                e1,e2 = True, True
            else:
                dist_value[1].SetValue(CONSTANT)

            dist_value[0].Enable(e1)
            dist_value[1].Enable(e2)


    def motor_details(self, bric_id, data):
        self.conv_func = self.motor_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(7, 5)
        grid_line = 0

        if (self.name == 'Motor Pair'):
            modules = win_data.config_motor_pairs()
            directions = [MOTOR_FWD, MOTOR_BCK,
                          MOTOR_P_RT, #MOTOR_P_RT_90,
                          MOTOR_P_LT, #MOTOR_P_LT_90,
                          MOTOR_P_SR, MOTOR_P_SL,
                          MOTOR_P_BR, MOTOR_P_BL,
                          MOTOR_STP]
        else:
            modules = []
            modules.extend(win_data.config_device_names('Motor A'))
            modules.extend(win_data.config_device_names('Motor B'))
            directions = [MOTOR_FWD, MOTOR_BCK, MOTOR_STP]

        #print modules
        mod_choice = self.make_combo(modules)

        d_choices = win_data.vars_names(U_NAME)
        s_choices = win_data.vars_names(U_NAME)
        dist_choices = win_data.vars_names(S_NAME)

        speeds = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

        #distance_units = ["unlimited", "mm", "inch", "degree", "raw"]
        distance_units = ["Unlimited - Forever",
                          "Millimetres - in 2.5mm steps",
                          "Inches - in inch steps",
                          "Degrees - in 7.5 degree steps",
                          "Raw - in 1/48th of rotation"]

        dirs = (self.make_combo(directions, sort=False),
                 self.make_combo(d_choices, add_const=True))
        speed = (self.make_combo(speeds, sort=False),
                 self.make_combo(s_choices, add_const=True))
        dist_units = (self.make_combo(distance_units, sort=False),)
        dist_value = (self.make_text_ctrl("0"),
                      self.make_combo(dist_choices, add_const=True))

        # Can't control a motor pair direction from a variable (too complex)
        if (self.name == 'Motor Pair'):
            dirs[1].Enable(False)

        self.data_order = (mod_choice,)+dirs+speed+dist_units+dist_value
        self.groups = None
        self.vars = ((dirs[1], dirs[0]),(speed[1], speed[0]), (dist_value[1], dist_value[0]))
        self.cons_tc = (dist_value[1],)
        self.cons_cb = (mod_choice, dirs[0], speed[0], dist_units[0])
        self.cb_special_vars = ((dirs),(dist_units), (dist_value))
        self.cb_special = self.motor_special_cb_change
        self.rbs = None

        if (len(modules) < 2):
            mod_choice.Hide()
        else:
            self.add_with_prompt(grid, (grid_line,0), MODULE_PROMPT, (mod_choice,))
            grid_line += 1

        self.make_headings(grid, (grid_line,1))
        self.add_with_prompt(grid, (grid_line+1,0), "Direction:", dirs)
        self.add_with_prompt(grid, (grid_line+2,0), "Speed:", speed)
        
        if (MOTOR_DISTANCE_ENABLED):
            self.add_with_prompt(grid, (grid_line+3,0), "Distance:", dist_units, ctrl_span=(1,2))
            self.add_with_prompt(grid, (grid_line+4,0), "Distance:", dist_value)
        else:
            dist_units[0].Hide()
            dist_value[0].Hide()
            dist_value[1].Hide()

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
        else:
            self.switch_constants()
            self.old_data = self.save_initial()
            #print self.old_data
        self.cb_special()
        return grid


    def single_motor_distance(self, input, single, code_lines):
        if ((input[5].startswith("Unlimited")) or ((input[2] == CONSTANT) and
                                          (input[1] in (MOTOR_STP,)))):
            # use the unlimited version of the direction
            distance_cmd = False
        else:
            # set up the distance register
            distance_cmd = True

            if (input[7] == CONSTANT):
                dist = win_data.conv_to_number(input[6], 'w', 0, 32000)
                rotations = 0
                if (dist == None):
                    return []
                if (input[5].startswith("Millimetre")):
                    # each rotation is 2.5mm
                    # round to the nearest integer
                    rotations = int((dist / 2.5) + 0.5)

                elif (input[5].startswith("Inch")):
                    # an inch is 25.4mm, which is pretty close
                    # to 10 rotation.
                    rotations = dist * 10
                elif (input[5].startswith("Degrees")):
                    # each rotation is 7.5 degrees
                    # round to the nearest integer
                    rotations = int((dist / 7.5) + 0.5)
                elif (input[5].startswith("Raw")):
                    # the number goes through un-changed
                    rotations = dist
                else:
                    rotations = dist

                code_lines.append("movw $%s %s" % (rotations,win_data.make_mod_reg(input[0], 'distance')))
            else:
                # this must be raw, as raw is the only one allowed
                # with variables
                code_lines.append("movw $%s %s" % (input[7],win_data.make_mod_reg(input[0], 'distance')))

        if (single):
            if (input[2] == CONSTANT):
                if (distance_cmd):
                    dir = DIRECTION_WITH_DIST_CODE[input[1]]
                else:
                    dir = DIRECTION_CODE[input[1]]
                code_lines.append("movb $%s %%_cpu:acc" % (dir,))
            else:
                code_lines.append("movb @%s %%_cpu:acc" % (input[2],))

        return distance_cmd

    def motor_convert(self, input, command, name, bric_id):
        """Data: mod, dir_cons, var, speed_cons, var, dist_unit, dist_cons, var, [, other motor mod]"""

        if (command == 'from_ids'):
            output= [win_data.config_name_from_id(input[0]), input[1], CONSTANT, input[3], CONSTANT,
                     input[5], input[6], CONSTANT]

            if (name == 'Motor Pair'):
                output[0] += '+'+win_data.config_name_from_id(input[8])

            for index in [2, 4, 7]:
                if (input[index]):
                    output[index] = win_data.vars_get_name(input[index])

            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # debug
            #print "to_ids_add_refs - output1", output

            if (name == 'Motor Pair'):
                motors = output[0].split('+')
                output[0] = win_data.config_id_from_name(motors[0])
                output.append(win_data.config_id_from_name(motors[1]))
                win_data.config_add_use(output[8])

            else:
                output[0] = win_data.config_id_from_name(output[0])

            output[2] = win_data.vars_get_id(output[2])
            output[4] = win_data.vars_get_id(output[4])
            output[7] = win_data.vars_get_id(output[7])

            # debug
            #print "to_ids_add_refs - output2", output

            win_data.config_add_use(output[0])
            win_data.vars_add_use(output[2])
            win_data.vars_add_use(output[4])
            win_data.vars_add_use(output[7])

            # debug
            #print "to_ids_add_refs - output3", output

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.config_rm_use(input[0])
            if (len(input) == 9):
                win_data.config_rm_use(input[8])

            win_data.vars_rm_use(input[2])
            win_data.vars_rm_use(input[4])
            win_data.vars_rm_use(input[7])

        elif (command == 'gen_code'):
            #"""Data: mod, dir_cons, var, speed_cons, var, dist_unit, dist_cons, var, [, other motor mod]"""
            code_lines = []
            if (name == "Motor Pair"):
                motors = input[0].split('+')
                s_dirs = self.motor_pair_directions(motors, input[1])
                command = input[1]
                for i in (0, 1):
                    if (s_dirs[i] == 0):
                        # This should not happen!
                        print "ERROR -- motor pair didn't give a command for every command!"
                        continue

                    if ((s_dirs[i] & 0x20) == 0x20):
                        # rt/left 90% - so rotation by 12 revolutions
                        code_lines.append("movw $%s %s" % (12,win_data.make_mod_reg(motors[i], 'distance')))
                        code_lines.append("movb $%s %s" % (s_dirs[i] ,win_data.make_mod_reg(motors[i], 'control')))

                    else:
                        # not right or left by 90%!

                        new_input = input
                        new_input[0] = motors[i]
                        new_input[1] = s_dirs[i]

                        dist = self.single_motor_distance(new_input, False, code_lines)
                        if (dist):
                            s_dirs[i] |= 0x20

                        # Set up control
                        code_lines.append("movb $%d %%_cpu:acc" % (s_dirs[i],))

                        if (input[4] == CONSTANT):
                            number = win_data.conv_to_number(input[3], 'b', 0, 10)
                            if (number == None):
                                return []
                            if (number != 0):
                                code_lines.append("or $%s" % (number,))
                        else:
                            code_lines.append("or @%s" % (input[4],))

                        code_lines.append("movb %%_cpu:acc %s" % (win_data.make_mod_reg(motors[i], 'control'),))

            else:
                # single motor
                self.single_motor_distance(input, True, code_lines)

                # BED - don't shift because the basic interpreter doesn't have room
                # for the shift. Document for the user instead.
                #code_lines.append("shlb $6")

                if (input[4] == CONSTANT):
                    number = win_data.conv_to_number(input[3], 'b', 0, 10)
                    if (number == None):
                        return []

                    if (number != 0):
                        code_lines.append("or $%s" % (number,))
                else:
                    code_lines.append("or @%s" % (input[4],))

                code_lines.append("movb %%_cpu:acc %s" % (win_data.make_mod_reg(input[0], 'control'),))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command

# ---------------------------- Signed Math and Unsigned Math brics ----------------------------------------

    def math_details(self, bric_id, data):
        self.conv_func = self.math_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        basic_ops = [MATH_PLUS, MATH_SUB, MATH_MULT, MATH_NOT]
        shift_ops = [MATH_DIV, MATH_MOD, MATH_LSHIFT, MATH_RSHIFT]
        logical_ops = [MATH_AND, MATH_OR, MATH_XOR]

        if (self.name == 'Maths Basic'):
            main_choices = win_data.vars_names(U_NAME)
            basic_choices = win_data.vars_names(U_NAME)
            shift_choices = win_data.vars_names(U_NAME)
            buttons = ["Basic", "Divide", "Logical"]
        else:
            main_choices = win_data.vars_names(S_NAME)
            basic_choices = win_data.vars_names(S_NAME)
            shift_choices = win_data.vars_names(S_NAME)
            buttons = ["Basic", "Divide"]

        rbs = self.make_radio_buttons(buttons)

        main_var=(self.make_combo(main_choices),)

        basic_op=(self.make_combo(basic_ops, sort=False),)
        basic_arg=(self.make_text_ctrl("0"),
                   self.make_combo(basic_choices, add_const=True))

        shift_op=(self.make_combo(shift_ops, sort=False),)
        shift_arg=(self.make_text_ctrl("0"),
                   self.make_combo(shift_choices, add_const=True))

        if (self.name == 'Maths Basic'):
            small_choices = win_data.vars_names(U_NAME)
            logical_op=(self.make_combo(logical_ops, sort=False),)
            logical_arg=(self.make_text_ctrl("0"),
                         self.make_combo(small_choices, add_const=True))

        self.data_order = (None,)+main_var+basic_op+basic_arg+shift_op+shift_arg
        self.groups = ((rbs[0], (basic_op+basic_arg)),(rbs[1], (shift_op+shift_arg)))
        self.vars = ((basic_arg[1], basic_arg[0]), (shift_arg[1], shift_arg[0]))
        self.cons_tc = (main_var[0], basic_arg[0], shift_arg[0])
        self.cons_cb = (basic_op[0], shift_op[0])
        self.rbs = rbs

        if (self.name == 'Maths Basic'):
            self.data_order = self.data_order + logical_op+logical_arg
            self.groups = self.groups+((rbs[2], (logical_op+logical_arg)),)
            self.vars = self.vars + ((logical_arg[1], logical_arg[0]),)
            self.cons_tc = self.cons_tc + (logical_arg[0],)
            self.cons_cb = self.cons_cb + (logical_op[0],)

##        print self.data_order
##        print self.groups
##        print self.vars
##        print self.cons_tc
##        print self.rbs

        self.add_with_prompt(grid, (0,1), "Variable:", main_var, ctrl_span=(1,2), expand=False)

        grid.Add(rbs[0], (1,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (1,1), "Operation:", basic_op)
        self.add_with_prompt(grid, (2,1), "Argument:", basic_arg)

        grid.Add(rbs[1], (3,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (3,1), "Operation:", shift_op)
        self.add_with_prompt(grid, (4,1), "Argument:", shift_arg)

        if (self.name == 'Maths Basic'):
            grid.Add(rbs[2], (5,0), flag=wx.ALIGN_CENTRE_VERTICAL)
            self.add_with_prompt(grid, (5,1), "Operation:", logical_op)
            self.add_with_prompt(grid, (6,1), "Argument:", logical_arg)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
            self.switch_group(rbs[values[0]])

        else:
            self.switch_constants()
            self.switch_group(rbs[0])
            self.old_data = self.save_initial()

        return grid


    def math_convert(self, input, command, name, bric_id):
        """Data: rb, main_var, basic_op, b_cons, b_var, shift_op, s_cons, s_var
        and with Unsigned Math add: logical_op, l_cons, l_var"""
        #print "math_convert():", input, command

        if (command == 'from_ids'):
            output= [input[0], win_data.vars_get_name(input[1]),
                     input[2], input[3], CONSTANT, input[5], input[6], CONSTANT]
            vars = [(0,4), (1,7)]

            if (name == 'Maths Basic'):
                output.extend([input[8], input[9], CONSTANT])
                vars.append((2,10))

            #print "vars", vars
            for rb, index in vars:
                #print "rb, index, output[0]", rb, index, output[0]
                if (output[0] == rb):
                    if (input[index]):
                        #print "Getting index:", index
                        output[index] = win_data.vars_get_name(input[index])

            #print output
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = [0]
            for i in range(len(self.rbs)):
                if (self.rbs[i].GetValue() == 1):
                    output[0] = i
                    break

            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            output[1] = win_data.vars_get_id(output[1])
            win_data.vars_add_use(output[1])

            vars = [(0,4), (1,7), (2,10)]
            for rb, index in vars:
                if (output[0] == rb):
                    output[index] = win_data.vars_get_id(output[index])
                    win_data.vars_add_use(output[index])

            #print output
            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            win_data.vars_rm_use(input[1])
            vars = [(0,4), (1,7), (2,10)]
            for rb, index in vars:
                if (input[0] == rb):
                    win_data.vars_rm_use(input[index])

        elif (command == 'gen_code'):
##            """Data: rb, main_var, basic_op, b_cons, b_var, shift_op, s_cons, s_var
##            and with Unsigned Math add: logical_op, l_cons, l_var"""

            op_dict = {MATH_PLUS:"add", MATH_SUB:"sub", MATH_MULT:"mul", MATH_NOT:"not",
                       MATH_DIV:"div", MATH_MOD:"mod", MATH_LSHIFT:"shl", MATH_RSHIFT:"shr",
                       MATH_AND:"and", MATH_OR:"or", MATH_XOR:"xor",
                       }

            code_lines = []
            size = win_data.vars_get_type_letter_from_name(input[1])
            code_lines.append("mov%s @%s %%_cpu:acc" % (size, input[1]))

            if (input[0] == 0):
                # Basic ops - plus, minus, mult, not
                if (input[4] == CONSTANT):
                    if (input[2] == MATH_NOT):
                        # ignore the constant for not
                        code_lines.append("not%s" % (size,))
                    else:
                        number = win_data.conv_to_number(input[3], size)
                        if (number == None):
                            return []
                        code_lines.append("%s%s $%s" % (op_dict[input[2]], size, number))
                else:
                    if (input[2] == MATH_NOT):
                        # ignore the constant for not
                        code_lines.append("not%s" % (size,))
                    else:
                        code_lines.append("%s%s @%s" % (op_dict[input[2]], size, input[4]))

            elif (input[0] == 1):
                # shift ops - div, mod, left shift, right shift
                if (input[7] == CONSTANT):
                    number = win_data.conv_to_number(input[6], size)
                    if (number == None):
                        return []
                    code_lines.append("%s%s $%s" % (op_dict[input[5]], size, number))
                else:
                    code_lines.append("%s%s @%s" % (op_dict[input[5]], size, input[7]))

            else:
                # logical ops - and, or, xor
                if (input[10] == CONSTANT):
                    number = win_data.conv_to_number(input[9], 'b')
                    if (number == None):
                        return []
                    code_lines.append("%s $%s" % (op_dict[input[8]], number))
                else:
                    code_lines.append("%s @%s" % (op_dict[input[8]], input[10]))


            code_lines.append("mov%s %%_cpu:acc @%s" % (size, input[1]))
            return code_lines


        else:
            raise SyntaxError, "Unknown command: " + command

# ---------------------------- LCD bric ----------------------------------------

    def lcd_details(self, bric_id, data):
        self.conv_func = self.lcd_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        rbs = self.make_radio_buttons(["ASCII","String", "Number", "Cursor", "Control"])
        controls = [LCD_CLEAR_SCREEN, LCD_SCROLL_LINE]
        ascii_vars = win_data.vars_names(U_NAME)
        other_vars = win_data.vars_names()

        ascii = (self.make_text_ctrl("A"),
                 self.make_combo(ascii_vars, add_const=True))


        string = (self.make_text_ctrl("HELLO WORLD"),)
        string_cursor = (self.make_text_ctrl("0"), self.make_text_ctrl("0"))

        number = (wx.StaticText(self, -1, ""), self.make_combo(other_vars, add_no_var=True),)

        cursor = (self.make_text_ctrl("0"), self.make_text_ctrl("0"))

        control = (self.make_combo(controls),)

        self.data_order = (None,)+ascii+string+(number[1],)+cursor+control+string_cursor
        self.groups = ((rbs[0], ascii), (rbs[1], string+string_cursor), (rbs[2], (number[1],)),
                       (rbs[3], cursor), (rbs[4], control))
        self.vars = ((ascii[1], ascii[0]),)
        self.cons_tc = (ascii[0], string[0], string_cursor[0], string_cursor[1], cursor[0], cursor[1])
        self.cons_cb = (number[1], control[0])
        self.rbs = rbs

        self.make_headings(grid, (0,2))

        # BED - swapped order without changing _convert!

        grid.Add(rbs[1], (1,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (1,1), "String:", string)
        self.add_with_prompt(grid, (2,1), "Row / Column:", string_cursor)

        grid.Add(rbs[0], (3,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (3,1), "Character:", ascii)

        grid.Add(rbs[2], (4,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (4,1), "Number:", number)

        grid.Add(rbs[3], (5,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (5,1), "Row / Column:", cursor)

        grid.Add(rbs[4], (6,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (6,1), "Command:", control)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
            self.switch_constants()
            self.switch_group(rbs[values[0]])
        else:
            self.switch_constants()
            # BED because of swap above
            self.switch_group(rbs[1])
            self.old_data = self.save_initial()

        return grid


    def lcd_convert(self, input, command, name, bric_id):
        """Data: radio_button, as-cons, as-var, string-cons,
        num-var, row-cons, col-cons, cmd-cons, row-string, col-string"""

        if (command == 'from_ids'):
            output = [input[0], input[1], CONSTANT, input[3], NO_VAR, input[5],
                      input[6], input[7], input[8], input[9]]

            if (input[0] == 0):
                # ascii-var
                if (input[2]):
                    output[2] = win_data.vars_get_name(input[2])
            elif (input[0] == 2):
                # number-var
                if (input[4]):
                    output[4] = win_data.vars_get_name(input[4])
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = [0]
            for i in range(len(self.rbs)):
                if (self.rbs[i].GetValue() == 1):
                    output[0] = i
                    break

            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # Validate values - change notes to codes
            # ??????

            # convert to ids

            if (output[0] == 0):
                # ascii-var
                output[2] = win_data.vars_get_id(output[2])
                win_data.vars_add_use(output[2])
            elif (output[0] == 2):
                # number-var
                if (output[4] == NO_VAR):
                    output[4] = None
                else:
                    output[4] = win_data.vars_get_id(output[4])
                    win_data.vars_add_use(output[4])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            if (input[0] == 0):
                # ascii-var
                win_data.vars_rm_use(input[2])
            elif (input[0] == 2):
                # number-var
                if (input[4]):
                    win_data.vars_rm_use(input[4])

        elif (command == 'gen_code'):
            code_lines = []
            if (input[0] == 0):
                # output an ascii value/variable
                if (input[2] == CONSTANT):
                    character = win_data.conv_to_lcd_char(input[1])
                    if (character == None):
                        return []
                    code_lines.append("movb $%s %%_devices:lcdbyte" % (character,))
                else:
                    code_lines.append("movb @%s %%_devices:lcdbyte" % (input[2],))

                code_lines.append("bitset 3 %_devices:action")

            elif (input[0] == 1):
                # a constant string with cursor location as a constant
                row = win_data.conv_to_number(input[8], 'b', 0, 5)
                if (row != None):
                    col = win_data.conv_to_number(input[9], 'b', 0, 13)
                    if (col == None):
                        return []
                else:
                    return []

                num_str = win_data.conv_to_lcd_string(row*col, input[3])
                if (num_str == None):
                    return []

                code_lines.append("DATA %s %s * %s" % (row,col,num_str))

            elif (input[0] == 2):
                # a number
                if (input[4] == NO_VAR):
                    # nothing to add because no real var here
                    code_lines.append("# No variable to display")
                else:
                    size = win_data.vars_get_type_letter_from_name(input[4])
                    if (size == 'b'):
                        code_lines.append("movb @%s %%_devices:lcdbyte" % (input[4],))
                        code_lines.append("bitset 2 %_devices:action")
                    else:
                        code_lines.append("movw @%s %%_devices:lcdword" % (input[4],))
                        code_lines.append("bitset 0 %_devices:action")

            elif (input[0] == 3):
                # update cursor
                row = win_data.conv_to_number(input[5], 'b', 0, 5)
                if (row != None):
                    col = win_data.conv_to_number(input[6], 'b', 0, 13)
                    if (col == None):
                        return []
                else:
                    return []
                code_lines.append("movb $%s %%_devices:lcdrp" % (row,))
                code_lines.append("movb $%s %%_devices:lcdcp" % (col,))

            else:
                # control
                if (input[7] == LCD_CLEAR_SCREEN):
                    bit = 4
                else:
                    bit = 3

                code_lines.append("bitset %d %%_devices:lcdaction" % (bit,))


            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command

# ---------------------------- LCD draw bric ----------------------------------------

    def lcddraw_details(self, bric_id, data):
        self.conv_func = self.lcddraw_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)



        settings = ["Light", "Dark"]
        state = (self.make_combo(settings),)
        cursor = (self.make_text_ctrl("0"), self.make_text_ctrl("0"))

        self.data_order = state+cursor
        self.groups = None
        self.vars = None
        self.cons_tc = cursor
        self.cons_cb = (state[0],)
        self.rbs = None

        self.add_with_prompt(grid, (1,1), "Set pixel to:", state)
        self.add_with_prompt(grid, (2,1), "At row / column:", cursor)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            self.set_control_values(self.data_order, values)
        else:
            self.old_data = self.save_initial()

        return grid


    def lcddraw_convert(self, input, command, name, bric_id):
        """Data: pixel, row-cons, col-cons"""

        if (command == 'from_ids'):
            output = [input[0], input[1], input[2]]
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            return output

        elif (command == 'rm_refs'):
            pass

        elif (command == 'gen_code'):
            code_lines = []
            row = win_data.conv_to_number(input[1], 'b', 0, 47)
            if (row != None):
                col = win_data.conv_to_number(input[2], 'b', 0, 83)
                if (col == None):
                    return []
            else:
                return []
            code_lines.append("movb $%s %%_devices:lcdrp" % (row,))
            code_lines.append("movb $%s %%_devices:lcdcp" % (col,))

            if (input[0] == "Light"):
                code_lines.append("bitset 1 %_devices:lcdaction")
            else:
                code_lines.append("bitset 0 %_devices:lcdaction")


            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


# ---------------------------- Event/Wait/If/Loop Brics ----------------------------------------

    def get_event_modules(self):
        #modules = [MOTHERBOARD]
        #for mod in ['Motor A', 'Motor B', 'Sounder', 'IR Receiver', 'Line Tracker']:
        #    modules.extend(win_data.config_device_names(mod))

        #return modules
        return EVENT_DICT.keys()

    def get_event_choices(self, name):
        # if (name == MOTHERBOARD):
        #     dtype = MOTHERBOARD
        # else:
        #     id = win_data.config_id_from_name(name)
        #     dtype = win_data.config_dtype_from_id(id)

        # return EVENT_DICT[dtype]
        return EVENT_DICT[name]

    def do_event_change(self, value):
        if (not self.event_choice):
            #print "No event choice yet"
            return

        # Load up event choice
        events = self.get_event_choices(value)
        self.event_choice.Clear()
        for title, stuff, if_variant in events:
            if (title in self.bad_events):
                continue
            if (self.good_choices and self.good_choices.has_key(value)):
                if (title not in self.good_choices[value]):
                    continue
            self.event_choice.Append(title)
        self.event_choice.SetSelection(0)

    def on_event_mod_change(self, event):
        value = event.GetEventObject().GetValue()
        self.do_event_change(value)
        self.update_dirty(True)
        if (self.cb_special):
            self.cb_special()

    def create_compare_code(self, code_lines, input, label):
        if (input == '='):
            code_lines.append("bre %s" % (label,))
        elif (input == '!='):
            code_lines.append("brne %s" % (label,))
        elif (input == '<'):
            code_lines.append("brl %s" % (label,))
        elif (input == '<='):
            code_lines.append("brle %s" % (label,))
        elif (input == '>'):
            code_lines.append("brgr %s" % (label,))
        else:
            #elif (input == '>=')
            code_lines.append("brge %s" % (label,))

        return

    def find_if_variant(self, module, event):
        events = self.get_event_choices(module)

        for title, details, if_variant in events:
            if (title == event):
                mod, bit = details
                break

        if (bit == -1):
            raise KeyError, "%s not a valid event in module %s" % (input[1], input[0])

        return if_variant

    def create_event_code(self, code_lines, mod_alias, event, label):
        match = None
        value = None
        bit = -1
        mod = None
        clear_status = True

        #print "create_event_code - mod_alias:", mod_alias, " event:", event
        
        module = self.module_remove_alias(mod_alias, EVENT_ALIASES)
        events = self.get_event_choices(mod_alias)

        for title, details, if_variant in events:
            if (title == event):
                mod, bit = details
                break

        if (bit == -1):
            raise KeyError, "%s not a valid event in module %s" % (input[1], input[0])

        if (not mod):
            mod = module

        code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(mod, 'status'),))
        if (event == 'Pressed'):
            mask = 0x01
            value = 0x01
            clear_status = False
        elif (event == 'Released'):
            mask = 0x01
            value = 0x00
            clear_status = False
        elif (event == TRACKER_1_STATUS):
            mask = 0x01
            value = 0x01
            clear_status = False
        elif (event == TRACKER_0_STATUS):
            mask = 0x01
            value = 0x00
            clear_status = False
        elif (event.startswith('Match #')):
            mask = 0x02
            match = int(event[7])
            #print "Matching IR code:", match
            # any match is handled without any special case
        else:
            mask = 1 << int(bit)

        code_lines.append("and $%s" % (mask,))

        if (value != None):
            code_lines.append("cmpb $%s" % (value,))
            code_lines.append('brne %s' % (label,))
        else:
            code_lines.append("brz %s" % (label,))

        # clear the bit
        if (clear_status):
            code_lines.append("bitclr $%s %s" % (bit, win_data.make_mod_reg(mod, 'status')))

        if (match):
            code_lines.append("movb %s %%_cpu:acc" % (win_data.make_mod_reg(mod, 'match'),))
            code_lines.append("cmpb $%s" % (match,))
            code_lines.append('brne %s' % (label,))

        #print "if_variant:", if_variant
        return if_variant

    def create_event_header(self, code_lines, module, event):
        match = None
        value = None
        bit = -1
        mod = None

        mod_alias = self.find_alias_from_event(event)
        events = self.get_event_choices(mod_alias)

        for title, details, if_variant in events:
            if (title == event):
                mod, bit = details
                break

        if (bit == -1):
            raise KeyError, "%s not a valid event in module %s" % (input[1], input[0])

        if (not mod):
            mod = module

        if (event == 'Pressed'):
            mask = 0x81
            value = mask
        elif (event == 'Released'):
            mask = 0x81
            value = 0x80
        elif (event == TRACKER_1_STATUS):
            mask = 0x03
            value = mask
        elif (event == TRACKER_0_STATUS):
            mask = 0x03
            value = 0x02
        else:
            mask = 1 << int(bit)
            value = mask

        code_lines.append("BEGIN EVENT %s, %s, %s" % (win_data.make_mod_reg(mod, 'status'),
                                                          mask, value))
        code_lines.append("bitclr $%s %s" % (bit, win_data.make_mod_reg(mod, 'status')))


    def find_alias_from_event(self, event):
        modules = self.get_event_modules()
        for m in modules:
            choices = self.get_event_choices(m)
            for c in choices:
                if (c[0] == event):
                    return m

        raise SyntaxError, "bad event: " + event

        
    def get_unused_event_choices(self, selected_bric_id = None):
        stream = 1                       # start at the first event
        used_choices = []
        while (stream < win_data.program().get_stream_count()):
            stream_id = win_data.program().get_stream_id(stream)
            bric_data = win_data.program().get_bric_data(stream_id)
            if (stream_id != selected_bric_id):
                used_choices.append(bric_data[1])
            stream += 1
        #print "Used choices:", used_choices

        unused_choices = []
        modules = self.get_event_modules()
        for m in modules:
            choices = self.get_event_choices(m)
            #print m, choices
            # now remove any that are an bad_events or used_events
            for c in choices:
                #print c[0], self.bad_events, used_choices
                if ((c[0] not in self.bad_events) and
                    (c[0] not in used_choices)):
                    unused_choices.append(c[0])

        #print unused_events
        return unused_choices

    def get_unused_events(self, selected_bric_id = None):
        unused_choices = self.get_unused_event_choices(selected_bric_id)
        #print "unused_choices", unused_choices
        unused_events = {}

        modules = self.get_event_modules()
        for uc in unused_choices:
            for m in modules:
                choices = self.get_event_choices(m)
                for c in choices:
                    if (uc == c[0]):
                        if (m in unused_events):
                            unused_events[m].append(uc)
                        else:
                            unused_events[m] = [uc]
                        break
                    
        #print "Unused events:", unused_events
        return unused_events
        
    
    def event_details(self, bric_id, data):
        #print "event_details:", data
        self.conv_func = self.event_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.bad_events = INVALID_NEW_EVENTS

        self.good_choices = self.get_unused_events(bric_id)
        print "good_choices:", self.good_choices
        
        self.prop_title = bric_data.get_bric_prop_title(self.name)
        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        modules = self.good_choices.keys()
        mod_choice = self.make_combo(modules, size=(EVENT_COMBO_PIXELS,-1))
        self.event_choice = wx.ComboBox(self, -1, "", style=wx.CB_READONLY, size=(EVENT_COMBO_PIXELS,-1))

        self.Bind(wx.EVT_COMBOBOX, self.on_event_mod_change, mod_choice)

        self.data_order = (mod_choice, self.event_choice)
        self.groups = None
        self.vars = None
        self.cons_tc = None
        self.cons_cb = (self.event_choice,)
        self.rbs = None

        grid.Add(wx.StaticText(self, -1, "Event happens:"), (0,1), flag=wx.ALIGN_LEFT)

        self.add_with_prompt(grid, (1,1), "", (mod_choice,))
        self.add_with_prompt(grid, (1,2), "", (self.event_choice,))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            mod_alias = self.find_alias_from_event(values[1])
            mod_choice.SetValue(mod_alias)
            self.do_event_change(mod_alias)
            self.event_choice.SetValue(values[1])


        else:
            mod_choice.SetValue(self.good_choices.keys()[0])
            self.do_event_change(self.good_choices.keys()[0])
            self.old_data = self.save_initial()

        win_data.set_unused_events(self.get_unused_events())
        
        # refresh the programming pallete
        win_data.force_redraw("ppallete")
        
        return grid


    def event_convert(self, input, command, name, bric_id):
        """Data: module, event  (note: module can be MOTHERBOARD)"""
        #print "event_convert:", command, ", input:", input
        if (command == 'from_ids'):
            # get module alias from event
            mod_alias = self.find_alias_from_event(input[1])
            module = self.module_remove_alias(mod_alias, EVENT_ALIASES)
            
            output = [module, input[1]]
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = []
            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())
            
            # Validate values - change notes to codes
            # ??????
            #print output

            # convert to ids
            output[0] = self.module_remove_alias(output[0], EVENT_ALIASES)

            #print output
            
            if (output[0] == MOTHERBOARD):
                output[0] = None
            else:
                output[0] = win_data.config_id_from_name(output[0])
                win_data.config_add_use(output[0])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            if (input[0]):
                win_data.config_rm_use(input[0])

        elif (command == 'gen_code'):
            code_lines = []
            self.create_event_header(code_lines, input[0], input[1])

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


    # ----- wait brics ---------------------------------
    def wait_details(self, bric_id, data):
        self.conv_func = self.wait_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.bad_events = []

        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        rbs = self.make_radio_buttons(["Seconds pass", "Event happens"])

        modules = self.get_event_modules()
        mod_choice = self.make_combo(modules, size=(EVENT_COMBO_PIXELS, -1))
        self.event_choice = wx.ComboBox(self, -1, "", style=wx.CB_READONLY, size=(EVENT_COMBO_PIXELS,-1))

        self.Bind(wx.EVT_COMBOBOX, self.on_event_mod_change, mod_choice)

        choices = win_data.vars_names(S_NAME)
        time = (self.make_text_ctrl("0"),
                self.make_combo(choices, add_const=True))


        self.data_order = (None,)+time+(mod_choice, self.event_choice)
        self.groups = ((rbs[0], time), (rbs[1], (mod_choice, self.event_choice)))
        self.vars = ((time[1], time[0]),)
        self.cons_tc = (time[0],)
        self.cons_cb = (self.event_choice,)
        self.rbs = rbs

        grid.Add(wx.StaticText(self, -1, "Wait Until:"), (0,1), flag=wx.ALIGN_LEFT)

        grid.Add(rbs[0], (1,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (1,1), "", time)

        grid.Add(rbs[1], (2,0), flag=wx.ALIGN_CENTRE_VERTICAL)

        self.add_with_prompt(grid, (2,1), "", (mod_choice,))
        self.add_with_prompt(grid, (2,2), "", (self.event_choice,))

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            mod_alias = self.find_alias_from_event(values[4])
            mod_choice.SetValue(mod_alias)
            self.do_event_change(mod_alias)
            self.event_choice.SetValue(values[4])
            self.set_control_values(self.data_order[:3], values[:3])

            self.switch_constants()
            self.switch_group(rbs[values[0]])

        else:
            mod_choice.SetValue("Keypad")
            self.do_event_change("Keypad")
            self.switch_constants()
            self.switch_group(rbs[0])

            self.old_data = self.save_initial()

        return grid

    def wait_convert(self, input, command, name, bric_id):
        """Data: rb, time-cons, time-var, module, event  (note: module can be MOTHERBOARD)"""

        #print "wait_convert cmd:", command, ", input:", input
        if (command == 'from_ids'):
            mod_alias = self.find_alias_from_event(input[4])
            module = self.module_remove_alias(mod_alias, EVENT_ALIASES)
            output = [input[0], input[1], CONSTANT, module, input[4]]

            if (input[0] == 0):
                if (input[2]):
                    output[2] = win_data.vars_get_name(input[2])
            else:
                if (input[3]):
                    output[3] = module
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = [0]
            for i in range(len(self.rbs)):
                if (self.rbs[i].GetValue() == 1):
                    output[0] = i
                    break

            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # Validate values - change notes to codes
            # ??????

            # convert to ids
            output[3] = self.module_remove_alias(output[3], EVENT_ALIASES)

            if (output[0] == 0):
                output[2] = win_data.vars_get_id(output[2])
                win_data.vars_add_use(output[2])
            else:
                if (output[3] == MOTHERBOARD):
                    output[3] = None
                else:
                    output[3] = win_data.config_id_from_name(output[3])
                    win_data.config_add_use(output[3])

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            #print "rm_refs:", input[3]
            if (input[0] == 0):
                win_data.vars_rm_use(input[2])
            else:
                if (input[3]):
                    win_data.config_rm_use(input[3])

        elif (command == 'gen_code'):
            #"""Data: rb, time-cons, time-var, module, event, in_event"""
            code_lines = []

            if (input[0] == 0):
                # pause for a time
                if (input[5]):
                    time_buff = "_event_time_buffer"
                else:
                    time_buff = "_main_time_buffer"

                if (input[2] == CONSTANT):
                    #code_lines.append("movw $%s %%_timers:pause" % (input[1],))
                    time = win_data.conv_to_time(input[1])
                    if (time == None):
                        return []

                    code_lines.append("movtime $%d @%s" % (time, time_buff))
                else:
                    code_lines.append("movtime @%s @%s" % (input[2], time_buff))

                #code_lines.append("bitset $1 %_timers:action")

                label = win_data.make_label(bric_id, 0)
                code_lines.append(label)
                code_lines.append("cmptime @%s" % (time_buff,))
                code_lines.append("brle %s" % (label,))

            else:
                # wait on an event
                label = win_data.make_label(bric_id, 0)
                code_lines.append(label)
                # if test fails then keep checking
                mod_alias = self.find_alias_from_event(input[4])
                self.create_event_code(code_lines, mod_alias, input[4], label)

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


    # ----- Loop brics ---------------------------------

    def loop_details(self, bric_id, data):
        self.conv_func = self.loop_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.bad_events = []

        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        rbs = self.make_radio_buttons(["Test passes", "Event happens", "Loop forever"])

        modules = self.get_event_modules()
        mod_choice = self.make_combo(modules, size=(EVENT_COMBO_PIXELS, -1))
        self.event_choice = wx.ComboBox(self, -1, "", style=wx.CB_READONLY, size=(EVENT_COMBO_PIXELS,-1))

        self.Bind(wx.EVT_COMBOBOX, self.on_event_mod_change, mod_choice)

        choices = win_data.vars_names()
        ops = ['=', '!=', '<', '>', '<=', '>=']

        test = (self.make_combo(choices, add_no_var=True),
                self.make_combo(ops, add_const=False, sort=False, size=(50, -1)),
                self.make_text_ctrl("0"))

        self.data_order = (None,)+test+(mod_choice, self.event_choice)
        self.groups = ((rbs[0], test), (rbs[1], (mod_choice, self.event_choice)), (rbs[2], ()),)
        self.vars = None
        self.cons_tc = (test[2],)
        self.cons_cb = (self.event_choice, test[0], test[1])
        self.rbs = rbs

        grid.Add(wx.StaticText(self, -1, "Loop UNTIL:"), (0,1), flag=wx.ALIGN_LEFT)

        # BED - moved the order without changing the tables so that I didn't have
        # to change the _convert function

        grid.Add(rbs[2], (1,0), flag=wx.ALIGN_CENTRE_VERTICAL)

        grid.Add(rbs[0], (2,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (2,1), "", test)

        grid.Add(rbs[1], (3,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (3,1), "", (mod_choice,))
        self.add_with_prompt(grid, (3,2), "", (self.event_choice,), ctrl_span=(1,2))


        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            mod_alias = self.find_alias_from_event(values[5])
            mod_choice.SetValue(mod_alias)
            self.do_event_change(mod_alias)
            self.set_control_values(self.data_order[:4], values[:4])
            self.event_choice.SetValue(values[5])
            self.switch_group(rbs[values[0]])

        else:
            mod_choice.SetValue("Keypad")
            self.do_event_change("Keypad")
            # special set to loop forever
            self.switch_group(rbs[2])

            self.old_data = self.save_initial()

        return grid

    def loop_convert(self, input, command, name, bric_id):
        """Data: rb, test-var, test-op, test-cons, module, event, in-event, end-of-loopif"""

        if (command == 'from_ids'):
            mod_alias = self.find_alias_from_event(input[5])
            module = self.module_remove_alias(mod_alias, EVENT_ALIASES)
            output = [input[0], NO_VAR, input[2], input[3], module, input[5]]

            if (input[0] == 0):
                if (input[1]):
                    output[1] = win_data.vars_get_name(input[1])
            elif (input[0] == 1):
                if (input[4]):
                    output[4] = module
            else:
                pass
            #print output
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = [0]
            for i in range(len(self.rbs)):
                if (self.rbs[i].GetValue() == 1):
                    output[0] = i
                    break

            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # Validate values - change notes to codes
            # ??????

            # convert to ids
            output[4] = self.module_remove_alias(output[4], EVENT_ALIASES)
            if (output[0] == 0):
                if (output[1] == NO_VAR):
                    output[1] = None
                else:
                    output[1] = win_data.vars_get_id(output[1])
                    win_data.vars_add_use(output[1])
            elif (output[0] == 1):
                if (output[4] == MOTHERBOARD):
                    output[4] = None
                else:
                    output[4] = win_data.config_id_from_name(output[4])
                    win_data.config_add_use(output[4])
            else:
                pass

            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            if (input[0] == 0):
                if (input[1]):
                    win_data.vars_rm_use(input[1])
            elif (input[0] == 1):
                if (input[4]):
                    win_data.config_rm_use(input[4])
            else:
                pass

        elif (command == 'gen_code'):
            #"""Data: rb, test-var, test-op, test-cons, module, event, in-event, end-of-loopif

            code_lines = []

            labels = win_data.make_loop_labels(bric_id)
            # labels are: body, exit, check

            # Start of the check so that we can retest after executing it
            code_lines.append("%s" % (labels[2],))

            if (input[0] == 0):
                # if the test isn't real (no var) then go directly to false
                if (input[1] == NO_VAR):
                    code_lines.append("bra %s" % (labels[1],))
                else:
                    # do a test for the beginning of the loop/if
                    size = win_data.vars_get_type_letter_from_name(input[1])
                    number = win_data.conv_to_number(input[3], size)
                    if (number == None):
                        return []

                    code_lines.append("mov%s $%s %%_cpu:acc" % (size, number))
                    code_lines.append("cmp%s @%s" % (size, input[1]))

                    # if test passes then leave loop
                    self.create_compare_code(code_lines, input[2], labels[1])

                    # Test failed, fall through to the body
                    #code_lines.append("bra %s" % (labels[0],))

            elif (input[0] == 1):

                # if test fails then go to the body
                mod_alias = self.find_alias_from_event(input[5])
                self.create_event_code(code_lines, mod_alias, input[5], labels[0])

                # if it passes then exit the loop
                code_lines.append("bra %s" % (labels[1],))


            else:
                # loop forever
                code_lines.append("bra %s" % (labels[0],))

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command


    # ----- If brics ---------------------------------
    def if_details(self, bric_id, data):
        self.conv_func = self.if_convert
        self.dirty = False
        self.name = win_data.program().get_bric_name(bric_id)
        self.bricId = bric_id
        self.bad_events = []

        self.prop_title = bric_data.get_bric_prop_title(self.name)

        values = None
        if (self.prop_title):
            self.title.SetLabel(self.prop_title)
        else:
            self.title.SetLabel("%s - properties:" % (self.name))

        grid = wx.GridBagSizer(5, 5)

        rbs = self.make_radio_buttons(["Test passes", "Event happens"])

        modules = self.get_event_modules()
        mod_choice = self.make_combo(modules, size=(EVENT_COMBO_PIXELS,-1))
        self.event_choice = wx.ComboBox(self, -1, "", style=wx.CB_READONLY, size=(EVENT_COMBO_PIXELS,-1))

        self.Bind(wx.EVT_COMBOBOX, self.on_event_mod_change, mod_choice)

        choices = win_data.vars_names()
        ops = ['=', '!=', '<', '>', '<=', '>=']

        test = (self.make_combo(choices, add_no_var=True),
                self.make_combo(ops, add_const=False, sort=False, size=(50, -1)),
                self.make_text_ctrl("0"))

        self.data_order = (None,)+test+(mod_choice, self.event_choice)
        self.groups = ((rbs[0], test), (rbs[1], (mod_choice, self.event_choice)))
        self.vars = None
        self.cons_tc = (test[2],)
        self.cons_cb = (self.event_choice, test[0], test[1])
        self.rbs = rbs

        self.cb_special = self.if_special_cb_change

        grid.Add(wx.StaticText(self, -1, "Take the top (True) branch if:"), (0,1),
                 span=(1,2), flag=wx.ALIGN_LEFT)

        grid.Add(rbs[0], (1,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (1,1), "", test)

        grid.Add(rbs[1], (2,0), flag=wx.ALIGN_CENTRE_VERTICAL)
        self.add_with_prompt(grid, (2,1), "", (mod_choice,))
        self.add_with_prompt(grid, (2,2), "", (self.event_choice,), ctrl_span=(1,2))

        grid.Add(wx.StaticText(self, -1, "Else take the bottom (False) branch."), (3,1),
                 span=(1,2), flag=wx.ALIGN_LEFT)

        self.bind_event_handlers()

        if (data):
            self.old_data = data
            values = self.conv_func(data, 'from_ids', self.name, bric_id)
            mod_alias = self.find_alias_from_event(values[5])
            mod_choice.SetValue(mod_alias)
            self.do_event_change(mod_alias)
            self.set_control_values(self.data_order[:4], values[:4])
            self.event_choice.SetValue(values[5])
            self.switch_group(rbs[values[0]])

        else:
            mod_choice.SetValue("Keypad")
            self.do_event_change("Keypad")
            self.switch_group(rbs[0])
            win_data.program().set_bric_if_variant(bric_id, "var")


            self.old_data = self.save_initial()

        self.cb_special()
        return grid

    def if_special_cb_change(self):
        # a combo box has changed
        # make sure the correct if-variant is selected
        #print "In if_special"
        ifVar = "var"
        if (self.rbs[1].GetValue() == 1):
            module = self.groups[1][1][0].GetValue()
            # BED this should work with the mod_aliases
            event = self.event_choice.GetValue()
            #print "Mod:", module, "Event:", event
            ifVar = self.find_if_variant(module, event)

        #print "ifVar:", ifVar
        win_data.program().set_bric_if_variant(self.bricId, ifVar)
        win_data.force_redraw("pwork")

    def if_convert(self, input, command, name, bric_id):
        """Data: rb, test-var, test-op, test-cons, module, event, in-event, end-of-loopif"""

        if (command == 'from_ids'):
            mod_alias = self.find_alias_from_event(input[5])
            module = self.module_remove_alias(mod_alias, EVENT_ALIASES)
            output = [input[0], NO_VAR, input[2], input[3], module, input[5]]

            if (input[0] == 0):
                if (input[1]):
                    output[1] = win_data.vars_get_name(input[1])
            else:
                if (input[4]):
                    output[4] = win_data.config_name_from_id(input[4])
            #print "if_convert:", output
            return output

        elif (command == 'to_ids_add_refs'):
            # get the data
            output = [0]
            for i in range(len(self.rbs)):
                if (self.rbs[i].GetValue() == 1):
                    output[0] = i
                    break

            for ctrl in self.data_order:
                if (not ctrl):
                    continue
                output.append(ctrl.GetValue())

            # Validate values - change notes to codes
            # ??????

            # convert to ids
            output[4] = self.module_remove_alias(output[4], EVENT_ALIASES)
            if (output[0] == 0):
                if (output[1] == NO_VAR):
                    output[1] = None
                else:
                    output[1] = win_data.vars_get_id(output[1])
                    win_data.vars_add_use(output[1])
            else:
                if (output[4] == MOTHERBOARD):
                    output[4] = None
                else:
                    output[4] = win_data.config_id_from_name(output[4])
                    win_data.config_add_use(output[4])

            #print "if_to_ids:", output
            return output

        elif (command == 'rm_refs'):
            """Input is the stored data, with refs"""
            if (input[0] == 0):
                if (input[1]):
                    win_data.vars_rm_use(input[1])
            else:
                if (input[4]):
                    win_data.config_rm_use(input[4])

        elif (command == 'gen_code'):
            #"""Data: rb, test-var, test-op, test-cons, module, event, in-event, end-of-loopif

            code_lines = []

            labels = win_data.make_if_labels(bric_id)
            # labels are: true, false, endif


            if (input[0] == 0):
                # if the test isn't real (no var) then go directly to false
                if (input[1] == NO_VAR):
                    code_lines.append("bra %s" % (labels[1],))
                    win_data.program().set_bric_if_variant(bric_id, "var")

                else:
                    # do a test for the beginning of the loop/if
                    size = win_data.vars_get_type_letter_from_name(input[1])
                    number = win_data.conv_to_number(input[3], size)
                    if (number == None):
                        return []

                    code_lines.append("mov%s $%s %%_cpu:acc" % (size, number))
                    code_lines.append("cmp%s @%s" % (size, input[1]))

                    self.create_compare_code(code_lines, input[2], labels[0])

                    # Test failed, go false or terminate loop
                    code_lines.append("bra %s" % (labels[1],))

                    win_data.program().set_bric_if_variant(bric_id, "var")

            else:
                # check an event
                mod_alias = self.find_alias_from_event(input[5])
                if_variant = self.create_event_code(code_lines, mod_alias, input[5], labels[1])

                # test passed
                code_lines.append("bra %s" % (labels[0],))

                win_data.program().set_bric_if_variant(bric_id, if_variant)

            return code_lines

        else:
            raise SyntaxError, "Unknown command: " + command
