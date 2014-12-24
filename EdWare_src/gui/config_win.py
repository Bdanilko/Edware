#!/usr/bin/env python

# * **************************************************************** **
#
# File: config_win.py
# Desc: Display configuration details
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
import win_data

import sys
import wx.lib.mixins.listctrl  as  listmix
class Config_list(wx.ListCtrl): #, listmix.TextEditMixin):
    def __init__(self, parent,
                 style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL):
        wx.ListCtrl.__init__(self, parent, style=style)

        self.column_headers = ["Loc.", "Module", "Module Label"]
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

            # check to make sure none are too narrow
            for i in range(3):
                if (self.GetColumnWidth(i) < self.min_widths[i]):
                    self.SetColumnWidth(i, -2)



class Config_win(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.RAISED_BORDER)
        #self.SetBackgroundColour("red")
        self.list = Config_list(self)
        self.update_list()
        box = wx.StaticBox(self, -1, 'Module Configuration')
        sboxsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sboxsizer.Add(self.list, 1, wx.EXPAND)

        self.SetSizer(sboxsizer)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate)


    def update_list(self):
        cfg = win_data.config_get_all()
        self.list.DeleteAllItems()
        empty = True
        for i in range(12):
            if (cfg.has_key(i)):
                index = self.list.InsertStringItem(sys.maxint, "%02d" % i)
                self.list.SetStringItem(index, 1, cfg[i][0])
                self.list.SetStringItem(index, 2, cfg[i][1])
                empty = False

        self.list.resize_columns()

    def on_activate(self, event):
        # close a bric properties box so this change can be reflected in the box
        win_data.selection_drop_all()

        index = event.GetIndex()
        loc = self.list.GetItemText(index)
        loc_num = int(loc, 10)
        dtype,name = win_data.config_get(loc_num)
        data = (loc, dtype, name)

        dialog = Config_dialog(self, "Edit module name", data)

        #dialog.CenterOnScreen()
        result = dialog.ShowModal()
        if (result == wx.ID_OK):
           new_name = dialog.get_data()
           dialog.Destroy()

           # any change?
           if (new_name == data[2]):
               return

           error_message = ""
           # verify that the new name is not already used
           if ((len(new_name) > 0) and
               (new_name[0].isupper() or new_name[0].islower()) and
               (len(new_name) <= 16)):
               # good name - convert any whitespace to underscore
               # Don't want to use replace because I want to handle ALL whitespace characters
               name2 = ""
               for i in range(len(new_name)):
                   if (new_name[i].isspace()):
                       name2 += '_'
                   else:
                       name2 += new_name[i]
               new_name = name2

               if (win_data.config_name_already_used(loc_num, new_name)):
                   error_message = "The module name '%s' is already used" % (new_name,)

           else:
               error_message = "Module names must start with a character and are at most 16 characters long"



           if (error_message):
               wx.MessageBox(error_message, caption="Error editing module name.", style=wx.OK | wx.ICON_ERROR)
           else:

               win_data.config_change_name(loc_num, new_name)
               self.update_list()
               #self.Refresh()


        else:
            dialog.Destroy()



class Config_dialog(wx.Dialog):
    def __init__(self, parent, title, data):
        wx.Dialog.__init__(self, parent, title=title)
        self.data = data

        labels = []
        labels.append(wx.StaticText(self, -1, "Location:"))
        labels.append(wx.StaticText(self, -1, "Module:"))
        labels.append(wx.StaticText(self, -1, "Module Label:"))

        self.fields = []
        self.fields.append(wx.StaticText(self, -1, data[0], size=(150, -1)))
        self.fields.append(wx.StaticText(self, -1, data[1], size=(150, -1)))
        self.fields.append(wx.TextCtrl(self, -1, data[2], size=(150, -1)))

        grid = wx.FlexGridSizer(3, 2, 5, 5)
        for i in range(3):
            grid.Add(labels[i], flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL)
            grid.Add(self.fields[i])

        clr_button = wx.Button(self, wx.ID_CLEAR)
        ok_button = wx.Button(self, wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((10,10))
        sizer.Add(grid, 1)
        sizer.AddSpacer((20,20))

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(clr_button)
        buttons.AddSpacer((20,20), 1)
        buttons.Add(cancel_button)
        buttons.Add(ok_button)
        sizer.Add(buttons, 0, wx.BOTTOM | wx.EXPAND)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_BUTTON, self.on_clr_clicked, clr_button)


    def on_clr_clicked(self, event):
        self.fields[2].SetValue("")

    def get_data(self):
        return self.fields[2].GetValue()
