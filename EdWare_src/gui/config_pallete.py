# * **************************************************************** **
#
# File: config_pallete.py
# Desc: Use the pallete window for configuration tasks
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
# Svn: $Id: config_pallete.py 50 2006-12-02 01:10:37Z briand $
# * **************************************************************** */

import wx

import pallete_win
import win_data
import device_data


class Config_pallete(pallete_win.Pallete_win):
    def __init__(self, parent):
        pallete_win.Pallete_win.__init__(self, parent, -1)
        self.name = 'cpallete'
        
        self.init_pallete()
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        
    def init_pallete(self):
        groups = device_data.get_groups()
        for name, expbmap, colbmap in groups:
            self.add_group(name, expbmap, colbmap)

        devices = device_data.get_devices()
        for name, group in devices:
            bmap = device_data.get_device_bmap(name)
            sel_bmap = device_data.get_device_bmap(name, True)
            self.add_item_bmap(group, name, bmap, sel_bmap)
        

    def on_left_down(self, event):
        # do main processing
        self.parent_on_left_down(event)

        # Can't drag modules in basic (but want to be able to select for the help window)
        if (not win_data.get_adv_mode()):
            self.drag_name = None
            self.drag_bmap = None
        

    def on_left_up(self, event):
        # do parent processing
        loc,name,dummy = self.parent_on_left_up(event)
        if (loc >= 0):
            # it is a valid drop!
            win_data.config_add(loc, name)
            win_data.selection_take('cwork', name, loc)
            win_data.click_sound()


        # force the work area to redraw
        win_data.force_redraw('cwork')
        win_data.force_redraw('config')
