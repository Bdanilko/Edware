#!/usr/bin/env python

# * **************************************************************** **
#
# File: pallete_win.py
# Desc: Base class for the pallete on the left side of the screen
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# Copyright 2006, 2014, 2015, 2016 Microbric Pty Ltd.
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

class Pallete_win(wx.ScrolledWindow):

    def __init__(self, parent, ID):
        #wx.Window.__init__(self, parent, ID, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        #wx.ScrolledWindow.__init__(self, parent, ID, style=wx.FULL_REPAINT_ON_RESIZE)
        wx.ScrolledWindow.__init__(self, parent, ID)
        self.groups = []
        self.group_bmaps = []
        self.group_expanded = []
        self.items = {}
        self.max_size = (120, 120)

        self.locations = []
        self.group_locations = []
        self.drag_image = None
        self.drag_name = None
        self.drag_bmap = None
        self.drag_start_pos = (0, 0)
        self.frame_rect = (0,0,0,0)

        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)

        #Do this in the child
        #self.Bind(wx.EVT_LEFT_UP, self.on_left_up)


        # the window resize event and idle events for managing the buffer
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_IDLE, self.on_idle)

        # and the refresh event
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)

    def on_enter(self, event):
        self.SetFocus()

    def update_frame_rect(self, rect):
        self.frame_rect = rect

    def enable_updates(self, flag=True):
        self.enable_updates = flag

    def add_group(self, group_name, exp_bmap, col_bmap):
        self.groups.append(group_name)
        self.group_bmaps.append((exp_bmap, col_bmap))
        self.group_expanded.append(True)

    def get_groups(self):
        return self.groups

    def add_item_bmap(self, group_name, name, bmap, sel_bmap=None, dis_bmap=None, id=-1, placement=0):
        """Add the bitmap to the pallete"""
        if (group_name not in self.groups):
            print "Error - group name (%s) not found" % (group_name)
            return

        if (group_name not in self.items):
            self.items[group_name] = []

        if (not sel_bmap):
            sel_bmap = bmap

        if (not dis_bmap):
            dis_bmap = bmap

        self.items[group_name].append((name, id, bmap, sel_bmap, dis_bmap, placement))

##    def add_item(self, group_name, name, image_fn, sel_image_fn=None, id=-1, placement=0):
##        """Add the bitmap to the pallete"""
##        if (group_name not in self.groups):
##            print "Error - group name (%s) not found" % (group_name)
##            return

##        if (group_name not in self.items):
##            self.items[group_name] = []

##        # load in the bitmaps
##        bmap = wx.Bitmap(image_fn, wx.BITMAP_TYPE_ANY)
##        if (sel_image_fn):
##            sel_bmap = wx.Bitmap(sel_image_fn, wx.BITMAP_TYPE_ANY)
##        else:
##            sel_bmap = bmap

##        self.items[group_name].append((name, id, bmap, sel_bmap, placement))


    def hit_test(self, pt):
        for rect,name,sel_bmap in self.locations:
            if (rect.InsideXY(pt.x, pt.y)):
                return (name, sel_bmap)

        return (None, None)



    # --------------- Event handlers --------------------------------

    def on_left_dclick(self, event):
        # if on a group then change it's state
        pt = self.CalcUnscrolledPosition(event.GetPosition())
        for rect, group in self.group_locations:
            if (rect.InsideXY(pt.x, pt.y)):
                # flip the state
                if (self.group_expanded[group]):
                    self.group_expanded[group] = False
                else:
                    self.group_expanded[group] = True

                self.Refresh(True)
                break

    def parent_on_left_down(self, event):
        # Make sure that we have the focus
        #self.SetFocus()

        pt = self.CalcUnscrolledPosition(event.GetPosition())
        self.drag_name, self.drag_bmap = self.hit_test(pt)
        if (self.drag_bmap):
            self.drag_start_pos = pt

            # select it too - other selections need to be removed
            win_data.selection_take(self.name, self.drag_name, -1)


    # called from child so they can do special processing if a DROP
    def parent_on_left_up(self, event):
        loc = -1
        extra = None
        if (self.drag_image):
            screen_pt = self.ClientToScreen(event.GetPosition())
            loc,update,extra = win_data.inform_work_of_centre_pt(screen_pt,
                                                                 self.drag_name,
                                                                 self.drag_image)

            self.drag_image.Hide()
            self.drag_image.EndDrag()
            self.drag_image = None
            self.drag_bmap = None

            self.SetCursor(wx.NullCursor)

            #print "Dropped at", screen_pt, "loc:", loc, "name:", self.drag_name

        # used by the child to do special processing
        return (loc, self.drag_name, extra)


    def on_mouse_motion(self, event):
        if (not self.drag_bmap or not event.Dragging() or not event.LeftIsDown()):
            return

        raw_pt = event.GetPosition()
        screen_pt = self.ClientToScreen(raw_pt)
        check_pt = self.CalcUnscrolledPosition(raw_pt)

        if (self.drag_bmap and not self.drag_image):
            tolerance = 4
            dx = abs(check_pt.x - self.drag_start_pos.x)
            dy = abs(check_pt.y - self.drag_start_pos.y)
            if (dx <= tolerance and dy <= tolerance):
                return

            # BED scale the image if it is program_pallete
            zoom = win_data.get_zoom(self.name)
            if (zoom != 1.0):
                image = self.drag_bmap.ConvertToImage()
                w = image.GetWidth() * zoom
                h = image.GetHeight() * zoom
                image.Rescale(w, h)
                self.drag_bmap = image.ConvertToBitmap()

            self.drag_image = wx.DragImage(self.drag_bmap, wx.StockCursor(wx.CURSOR_HAND))
            dev_x, dev_y = self.drag_bmap.GetSize()
            hotspot = (dev_x/2, dev_y/2)
            #print "on_mouse_motion: hotspot", hotspot
            self.drag_image.BeginDrag(hotspot, self, True, self.frame_rect)
            loc, update,extra = win_data.inform_work_of_centre_pt(screen_pt, self.drag_name,
                                                                  self.drag_image)
            self.drag_image.Show()
            self.drag_image.Move(raw_pt)
        else:
            loc, update,extra = win_data.inform_work_of_centre_pt(screen_pt, self.drag_name,
                                                                  self.drag_image)
            if (update):
                self.drag_image.Show()
            self.drag_image.Move(raw_pt)



    def on_size(self, event):
        #print "Size", event.GetSize()
        win_x, win_y = event.GetSize()

        if (win_x < 100):
            event.Skip(False)

        x_step = 20
        y_step = 20
        x_units = self.max_size[0]/x_step + 1
        y_units = self.max_size[1]/y_step + 1

        self.SetScrollbars(0, y_step, 0, y_units)

    def on_idle(self, event):
        #print "Idle"
        pass

    def on_paint(self, event):
        #print "Paint"
        dc = wx.PaintDC(self)
        self.DoPrepareDC(dc)
        x_size = dc.GetSize()[0]
        x = 5
        y = 5
        self.locations = []
        self.group_locations = []

        for i in range(len(self.groups)):
            if (self.group_expanded[i]):

                b = self.group_bmaps[i][0]
                dc.DrawBitmap(b, x, y, True)
                rect = wx.Rect(x,y,b.GetWidth(), b.GetHeight())
                self.group_locations.append((rect, i))

                y += self.group_bmaps[i][0].GetSize()[1] * 1.5

                for n,i,b,sb,db, p in self.items[self.groups[i]]:
                    if (not win_data.enabled_on_pallete(self.name, n)):
                        dc.DrawBitmap(db, x, y, True)
                    else:
                        if (win_data.selection_check(self.name, n, -1)):
                            dc.DrawBitmap(sb, x, y, True)
                        else:
                            dc.DrawBitmap(b, x, y, True)
                        rect = wx.Rect(x,y,b.GetWidth(), b.GetHeight())
                        self.locations.append((rect, n, sb))

                    y = y + b.GetHeight() + 5

                y = (y - 5) + (self.group_bmaps[i][0].GetHeight() * 0.5)

            else:
                b = self.group_bmaps[i][1]
                dc.DrawBitmap(b, x, y, True)
                rect = wx.Rect(x,y,b.GetWidth(), b.GetHeight())
                self.group_locations.append((rect, i))

                y += self.group_bmaps[i][1].GetSize()[1] * 1.5



        y += 24

        self.max_size = wx.Size(120, y)

        self.SetVirtualSize((120, y))



##class DragShape:
##    def __init__(self, bmp, fullscreen=False):
##        self.bmp = bmp
##        self.pos = (0,0)
##        self.shown = True
##        self.text = None
##        self.fullscreen = fullscreen

##    def HitTest(self, pt):
##        rect = self.GetRect()
##        return rect.InsideXY(pt.x, pt.y)

##    def GetRect(self):
##        return wx.Rect(self.pos[0], self.pos[1],
##                      self.bmp.GetWidth(), self.bmp.GetHeight())

##    def Draw(self, dc, op = wx.COPY):
##        if self.bmp.Ok():
##            memDC = wx.MemoryDC()
##            memDC.SelectObject(self.bmp)

##            dc.Blit(self.pos[0], self.pos[1],
##                    self.bmp.GetWidth(), self.bmp.GetHeight(),
##                    memDC, 0, 0, op, True)

##            return True
##        else:
##            return False
