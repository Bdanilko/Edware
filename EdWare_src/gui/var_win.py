#!/usr/bin/env python

# * **************************************************************** **
#
# File: var_win.py
# Desc: Display and edit variable details
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
# Svn: $Id: var_win.py 50 2006-12-02 01:10:37Z briand $
# * **************************************************************** */

import wx

import win_data


NEW_DATA = ("", "0-255", "1", "")
VALID_RANGES = ["0-255", "+/- 32767"]

import sys
class Var_list(wx.ListCtrl):
    def __init__(self, parent,
                 style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL):
        wx.ListCtrl.__init__(self, parent, style=style)

        #self.column_headers = ["Name", "Range", "Length", "Intial Value"]
        self.column_headers = ["Name", "Range", "Intial Value"]
        self.columns = len(self.column_headers)
        self.headers()
        self.calculate_mins()

    def headers(self):
        for i in range(self.columns):
            self.InsertColumn(i, self.column_headers[i])
            
        for i in range(self.columns):
            self.SetColumnWidth(i, -2)

        self.currentItem = 0

    def calculate_mins(self):
        self.min_widths = []
        for i in range(self.columns):
            self.min_widths.append(self.GetColumnWidth(i))
            
    def resize_columns(self):
        items = self.GetItemCount()
        if (items==0):
            self.SetColumnWidth(0, -2)
            self.SetColumnWidth(1, -2)
            self.SetColumnWidth(2, -2)
        else:
            self.SetColumnWidth(0, -1)
            self.SetColumnWidth(1, -1)
            self.SetColumnWidth(2, -1)

            #self.Refresh()
            
            # check to make sure none are too narrow
            for i in range(3):
                if (self.GetColumnWidth(i) < self.min_widths[i]):
                    self.SetColumnWidth(i, -2)
                    


class Var_win(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.RAISED_BORDER)
        #self.SetBackgroundColour("red")
        self.list = Var_list(self)
        self.update_list()
        
        box = wx.StaticBox(self, -1, 'Variables')
        sboxsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sboxsizer.Add(self.list, 1, wx.EXPAND)

        self.SetSizer(sboxsizer)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate)
        
       
    def update_list(self):
        self.list.DeleteAllItems()

        vars = win_data.vars_get_all()
        #print "Vars:", vars
        keys = vars.keys()
        keys.sort()
        #print "Keys:", keys
        if (keys):
            for k in keys:
                data = vars[k]
                index = self.list.InsertStringItem(sys.maxint, k)
                self.list.SetStringItem(index, 1, data[0])
                self.list.SetStringItem(index, 2, data[2])
                #self.list.SetStringItem(index, 3, data[2])
            
        # add a marker to allow for new variables
        index = self.list.InsertStringItem(sys.maxint, "<NEW>")
        self.list.SetStringItem(index, 1, "")
        self.list.SetStringItem(index, 2, "")
        item = self.list.GetItem(index)
        item.SetBackgroundColour("lightblue")
        self.list.SetItem(item)
                               
        self.list.resize_columns()


    def on_activate(self, event):
        index = event.GetIndex()
        if (index == (self.list.GetItemCount() - 1)):
            index =None
        self.add_variable(index)


    def add_variable(self, index = None):
        # close a bric properties box so this change can be reflected in the box
        win_data.selection_drop_all()
        
        key = None
        old_len = 0
        
        if (index != None):
            title = "Edit variable"
            key = self.list.GetItemText(index)
            var_data = win_data.vars_get(key)
            data = (key, var_data[0], var_data[1], var_data[2])
            old_len = int(var_data[1])
        else:
            title = "Add variable"
            data = NEW_DATA

        dialog = Var_dialog(self, title, data)

        #dialog.CenterOnScreen()
        result = dialog.ShowModal()
        if (result == wx.ID_OK):
           new_data = dialog.get_data()
           dialog.Destroy()

           # verify the edit was OK
           error_message = ""
           if (new_data[0] == ""):
               # verify that data[0] was not being used in the program
               if (win_data.vars_used_in_program(data[0])):
                   error_message = "Variable name '"+data[0]+"' is used in the program. "+\
                                   "Change the program before removing this variable."

           else:
               if (new_data[0] != data[0]):
                   if ((new_data[0][0].isupper() or new_data[0][0].islower()) and
                       (len(new_data[0]) <= 16)):
                       # good name - convert any whitespace to underscore
                       # Don't want to use replace because I want to handle ALL whitespace characters
                       name2 = ""
                       for i in range(len(new_data[0])):
                           if (new_data[0][i].isspace()):
                               name2 += '_'
                           else:
                               name2 += new_data[0][i]
                       new_data[0] = name2
                               
                       # verify that the new name is not already used
                       if (win_data.vars_exists(new_data[0])):
                           error_message = "Variable name '"+new_data[0]+"' is already used."

                   else:
                       error_message = "Variable names must start with a character and are at most 16 characters long"
                   
               if (new_data[1] not in VALID_RANGES):
                   # verify that range is valid
                   error_message = "Variable range must be one of: %s, %s" % \
                                   (VALID_RANGES[0], VALID_RANGES[1])

               # verify that initial value is reasonable (if used)
               if (not self.check_length_and_initial(new_data[1], new_data[2], new_data[3])):
                   error_message = "Variable length (%s) or initial value (%s) is not in the valid range." %\
                                   (new_data[2], new_data[3])
                   
               # and verify that there is size left
               if (win_data.vars_no_room_left(new_data[1], int(new_data[2]) - old_len)):
                   error_message = "Not enough room for %s more variable(s) of type %s." %\
                                   (new_data[2], new_data[1])

           if (error_message):
               wx.MessageBox(error_message, caption="Error editing variable.", style=wx.OK | wx.ICON_ERROR)
           else:
               if (key):
                   if (len(new_data[0]) > 0):
                       # is it a major change and in use?
                       #print "Key", key, data[1], new_data[1]
                       if (win_data.vars_used_in_program(key) and
                           (new_data[1] != data[1])):
                           
                           error_message="Error - Can not change the range of a variable that is " +\
                                         "being used in the program."
                           wx.MessageBox(error_message, caption="Can't change the range.", style=wx.OK | wx.ICON_ERROR)

                       else:
                           win_data.vars_change(key, new_data[0], new_data[1], new_data[2], new_data[3])
                           self.update_list()
                           
    
                   else:
                       if (not win_data.vars_remove(key)):
                           error_message="Can not delete the variable as it is used in the program.\n" +\
                                          "Delete it from the program before deleting it here."
                           wx.MessageBox(error_message, caption="Can't delete variable.", style=wx.OK | wx.ICON_ERROR)
                       else:
                           self.update_list()
                                   

               else:
                   if (len(new_data[0]) > 0):
                       win_data.vars_add(new_data[0], new_data[1], new_data[2], new_data[3])
                       self.update_list()

               #self.Refresh()
               

        else:
            dialog.Destroy()

        
    def check_length_and_initial(self, range, len_str, initial):
        if (not len_str):
            return False

        if (not len_str.isdigit()):
            return False

        length = int(len_str)
        
        if (not initial):
            return True

        splits = win_data.vars_split_initial(initial)
        
        if (len(splits) > length):
            return False

        if (len(splits) == 1 and range.startswith("0") and (len(splits[0])>2) and
            (splits[0][0] == '"' or splits[0][0] == "'") and
            (splits[0][0] == splits[0][-1]) and (len(splits[0])-2 <= length)):
            return True

        for s in splits:
            if (not s):
                continue
            
            if ((s[0] in "+-" and s[1:].isdigit()) or
                s.isdigit()):

                value = int(s)
                if (range.startswith("+/-")):
                    if (value < -32767 or value > 32767):
                        return False
                else:
                    if (value < 0 or value > 255):
                        return False

            else:
                return False
            
        return True

    

class Var_dialog(wx.Dialog):
    def __init__(self, parent, title, data=("", "", "1", "")):
        wx.Dialog.__init__(self, parent, title=title)
        self.data = data

        labels = []
        labels.append(wx.StaticText(self, -1, "Variable name:", ))
        labels.append(wx.StaticText(self, -1, "Variable range:"))
        #labels.append(wx.StaticText(self, -1, "Variable length:"))
        labels.append(wx.StaticText(self, -1, "Initial value (optional):"))

        self.fields = []
        self.fields.append(wx.TextCtrl(self, -1, data[0], size=(150, -1)))
        self.fields.append(wx.ComboBox(self, -1, data[1], choices=VALID_RANGES, size=(150,-1)))
        #self.fields.append(wx.TextCtrl(self, -1, data[2], size=(150, -1)))
        self.fields.append(wx.TextCtrl(self, -1, data[3], size=(150, -1)))

        grid = wx.FlexGridSizer(4, 2, 5, 5)
        for i in range(3):
            grid.Add(labels[i], flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL)
            grid.Add(self.fields[i])
        
        del_button = wx.Button(self, wx.ID_DELETE)
        ok_button = wx.Button(self, wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((10,10))
        sizer.Add(grid, 1)
        sizer.AddSpacer((20,20))
        
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(del_button)
        buttons.Add((20,20), 1)
        buttons.Add(cancel_button)
        buttons.Add(ok_button)
        sizer.Add(buttons, 0, wx.BOTTOM | wx.EXPAND)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_BUTTON, self.on_del_clicked, del_button)


    def on_del_clicked(self, event):
        self.clr_data()
        self.EndModal(wx.ID_OK)

    def clr_data(self):
        data = NEW_DATA
        
        self.fields[0].SetValue(data[0])
        self.fields[1].SetValue(data[1])
        self.fields[2].SetValue(data[3])
        

    def get_data(self):
        return [self.fields[0].GetValue(), self.fields[1].GetValue(),
                "1", self.fields[2].GetValue()]

