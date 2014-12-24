#!/usr/bin/env python

# * **************************************************************** **
#
# File: work_win.py
# Desc: Base class for the large work area on the right side of the screen
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

class Work_win(wx.ScrolledWindow):
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent, style=wx.RAISED_BORDER)
        self.SetBackgroundColour("white")
        self.SetVirtualSize((120, 120))
        self.SetScrollRate(20,20)
        self.exit = False

        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)

    def on_enter(self, event):
        self.SetFocus()
        
##    def on_enter(self, event):
##        #print "Enter window", event.GetPosition()
##        self.exit = False
##        event.Skip()
        
##    def on_exit(self, event):
##        #print "Exit window", event.GetPosition(), event.GetId(), event.GetTimestamp()
##        if (event.LeftIsDown()):
##            self.exit = True
##        event.Skip()

