#!/usr/bin/env python

# * **************************************************************** **
#
# File: program_pallete.py
# Desc: Use the pallete window for program tasks
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
# Svn: $Id: program_pallete.py 50 2006-12-02 01:10:37Z briand $
# * **************************************************************** */

import wx

import pallete_win
import win_data
import bric_data

class Program_pallete(pallete_win.Pallete_win):
    def __init__(self, parent):
        pallete_win.Pallete_win.__init__(self, parent, -1)
        self.name = 'ppallete'

        self.init_pallete()
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)

    def init_pallete(self):
        groups = bric_data.get_groups()
        for name, expbmap, colbmap in groups:
            self.add_group(name, expbmap, colbmap)

        brics = bric_data.get_brics()
        for name, group in brics:
            if (group != "Hide"):
                bmap = bric_data.get_bric_bmap(name)
                sel_bmap = bric_data.get_bric_bmap(name, bric_data.BRIC_SELECTED)
                dis_bmap = bric_data.get_bric_bmap(name, bric_data.BRIC_DISABLED)
                
                self.add_item_bmap(group, name, bmap, sel_bmap, dis_bmap)


    def on_left_down(self, event):
        # do main processing
        self.parent_on_left_down(event)

    def on_left_up(self, event):
        # do parent processing
        prev_id,bric_name,which_id = self.parent_on_left_up(event)
        if (prev_id >= 0):
            # it is a valid drop!
            new_id = win_data.program().add_new_bric(prev_id, which_id, bric_name)
            # set the selection
            win_data.selection_take('pwork', bric_name, new_id)

                
        # force the work area to redraw
        win_data.force_redraw('pwork')

