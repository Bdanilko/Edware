#!/usr/bin/env python

# * **************************************************************** **
#
# File: help_win.py
# Desc: Display help for selected bric or device
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

class Help_win(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.RAISED_BORDER)

        self.help_text = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.help_text.SetBackgroundColour("white")

        #self.SetVirtualSize((120, 100))
        #self.SetScrollRate(20, 20)
        
        box = wx.StaticBox(self, -1, 'Help')
        sboxsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sboxsizer.Add(self.help_text, 1, wx.EXPAND)

        self.SetSizer(sboxsizer)
    
    def set_text(self, help_text):
        #print "Set help text:", help_text
        new_help = help_text
        self.help_text.SetValue(new_help)
