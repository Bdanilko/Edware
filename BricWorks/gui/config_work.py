#!/usr/bin/env python

# * **************************************************************** **
#
# File: config_work.py
# Desc: Use the work window for configuration tasks
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
# Svn: $Id: config_work.py 50 2006-12-02 01:10:37Z briand $
# * **************************************************************** */

import wx

import work_win
import win_data
import device_data

##zones = [wx.Rect(150, 50, 300, 100),    # top
##         wx.Rect(450, 150, 100, 300),   # right
##         wx.Rect(150, 450, 300, 100),   # bottom
##         wx.Rect(50, 150, 100, 300),    # left
##         ]

##zone_detail = [
##    (wx.Rect(150, 50, 100, 100), 11, wx.Rect(195, 145, 10, 10)),
##    (wx.Rect(250, 50, 100, 100), 0, wx.Rect(295, 145, 10, 10)),
##    (wx.Rect(350, 50, 100, 100), 1, wx.Rect(395, 145, 10, 10)),
##    (wx.Rect(450, 150, 100, 100), 2, wx.Rect(445, 195, 10, 10)),
##    (wx.Rect(450, 250, 100, 100), 3, wx.Rect(445, 295, 10, 10)),
##    (wx.Rect(450, 350, 100, 100), 4, wx.Rect(445, 395, 10, 10)),
##    (wx.Rect(350, 450, 100, 100), 5, wx.Rect(395, 445, 10, 10)),
##    (wx.Rect(250, 450, 100, 100), 6, wx.Rect(295, 445, 10, 10)),
##    (wx.Rect(150, 450, 100, 100), 7, wx.Rect(195, 445, 10, 10)),
##    (wx.Rect(50, 350, 100, 100), 8, wx.Rect(145, 395, 10, 10)),
##    (wx.Rect(50, 250, 100, 100), 9, wx.Rect(145, 295, 10, 10)),
##    (wx.Rect(50, 150, 100, 100), 10, wx.Rect(145, 195, 10, 10)),
##    ]

##locations = [(250, 50), (350, 50),      # 0, 1
##             (450, 150), (450, 250), (450, 350), # 2, 3, 4
##             (350, 450), (250, 450), (150, 450), # 5, 6, 7
##             (50, 350), (50, 250), (50, 150), # 8, 9, 10
##             (150, 50),                 # 11
##             ]

##window_size = (600, 600)



class Config_work(work_win.Work_win):
    def __init__(self, parent, frame):
        work_win.Work_win.__init__(self, parent)

        
        self.locations_empty = []
        self.locations_full = []
        
        self.size = None
        self.zoom = 1.0
        self.setup_zones_and_locations()
        
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.drag_loc = -1
        self.drag_image = None
        self.drag_start = (-1, None)    # Remember in case we need to put it back
        self.drag_start_pos = None
        
        self.zone_hit = -1
        self.zone_good = -1
        self.zone_rect = None
        
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)


    def setup_zones_and_locations(self):
        mb_x,mb_y = device_data.get_mb_bmap().GetSize()
##        if (self.zoom != 1.0):
##            mb_x *= self.zoom
##            mb_y *= self.zoom
        
        dev_x,dev_y = (mb_x/3,mb_y/3)
        mb_l = mb_x
        mb_r = mb_x * 2
        mb_t = mb_y
        mb_b = mb_y * 2

        self.mb_origin = [mb_l, mb_t]
        self.mb_size = (mb_x, mb_y)
        self.hit_size = (dev_x, dev_y)
        self.window_size = (mb_x*3, mb_y*3)

        self.centres = [(mb_l+(mb_x/2), mb_b),      # 0
                   (mb_l+(dev_x/2), mb_b),          # 1
                   (mb_l, mb_b - (dev_y/2)),        # 2
                   (mb_l, mb_b - (mb_y/2)),         # 3
                   (mb_l, mb_t + (dev_y/2)),        # 4
                   (mb_l+(dev_x/2), mb_t),          # 5
                   (mb_l+(mb_x/2), mb_t),           # 6
                   (mb_r-(dev_x/2), mb_t),          # 7
                   (mb_r, mb_t+(dev_y/2)),          # 8
                   (mb_r, mb_t+(mb_y/2)),           # 9
                   (mb_r, mb_b-(dev_y/2)),          # 10
                   (mb_r-(dev_x/2), mb_b),          # 11
                   ]


    def on_move(self, event):
        self.on_size(event)
        
    def on_size(self, event):
        # send the new size to the program pallete
        self.size = self.GetClientSize()
        upper_left = self.GetClientAreaOrigin()
        #print size, upper_left, self.ClientToScreen(upper_left), self.GetClientRect()
        upper_left = self.ClientToScreen(upper_left)
        rect = wx.Rect(upper_left[0], upper_left[1], self.size[0], self.size[1])
        #print "Config Work:", rect

        event.Skip()

    def set_zoom(self, zoom):
        if (zoom != self.zoom):
            self.zoom = zoom
            self.Refresh(True)
            
    def adjust_zoom(self, dir):
        if (dir == 0):
            self.zoom = 1.0
        elif (dir < 0 and self.zoom > 0.3):
            self.zoom -= 0.1
        elif (dir > 0 and self.zoom < 3.0):
            self.zoom += 0.1
        self.Refresh(True)

    def get_zoom(self):
        return self.zoom


    def on_paint(self, event):
        dc = wx.PaintDC(self)
        self.DoPrepareDC(dc)

        dc.SetBackground(wx.Brush("white", wx.SOLID))
        dc.SetUserScale(self.zoom, self.zoom)
        dc.Clear()
        
        # paint mb first
        mb = device_data.get_mb_bmap()
        dc.DrawBitmap(mb, self.mb_origin[0], self.mb_origin[1], True)

        self.locations_full = []
        self.locations_empty = []
        
        overlay = None
        # now the current configuration
        cfg = win_data.config_get_all()
        for i in range(12):
            if (cfg.has_key(i)):
                dtype = cfg[i][0]
                orient = 0
                
                if (i in [1, 4, 7, 10] and (dtype == "Motor A" or dtype == "Motor B")):
                    orient = win_data.config_orient_from_loc(i)
                    if (orient == 1):
                        image_index_base = 2
                    else:
                        image_index_base = 4
                else:
                    image_index_base = 0

                    
                if (win_data.selection_check('cwork', None, i)):
                    overlay = device_data.get_overlay_bmap(i)
                    image = device_data.get_fullsize_image(dtype, image_index_base + 1)
                else:
                    image = device_data.get_fullsize_image(dtype, image_index_base)

            else:
                dtype = None
                image = None
                offset = (0, 0)
                size = self.hit_size
                
                    
            x,y = self.centres[i]
            if (i in [5, 6, 7]):
                if (image):
                    # no rotation needed
                    b = wx.BitmapFromImage(image)
                    size = b.GetSize()
                    offset = (0, 10)

                if (dtype == 'Motor A'):
                    if (i == 7  and orient < 0):
                        b = wx.BitmapFromImage(image.Rotate90(clockwise=True))
                        size = b.GetSize()
                        x,y = self.centres[8]
                        x = x - offset[1]-90
                        y = y + size[1] - self.hit_size[1]*4
                    else:
                        x = x - self.hit_size[0]/2
                        if (i == 7):
                            y = y -size[1]+offset[1]+90
                        else:
                            y = y - size[1] + offset[1]
                    
                elif (dtype == 'Motor B'):
                    if (i == 7  and orient < 0):
                        b = wx.BitmapFromImage(image.Rotate90(clockwise=True))
                        size = b.GetSize()
                        x,y = self.centres[8]
                        x = x - offset[1]-90
                        y = y + size[1] - self.hit_size[1]*4.5
                    else:
                        x = x - size[0] + self.hit_size[0]*1.5
                        if (i == 7):
                            y = y -size[1]+offset[1]+90
                        else:
                            y = y - size[1] + offset[1]
                    
                else:
                    x = x - (size[0]/2) + offset[0]
                    y = y - (size[1]) + offset[1]

            elif (i in [2, 3, 4]):
                if (image):
                    # -90 rotation needed
                    b = wx.BitmapFromImage(image.Rotate90(clockwise=False))
                    size = b.GetSize()
                    offset = (10, 0)

                if (dtype == 'Motor A'):
                    if (i == 4  and orient < 0):
                        b = wx.BitmapFromImage(image)
                        size = b.GetSize()
                        x,y = self.centres[5]
                        x = x - self.hit_size[0]*1.5
                        y = y - size[1] + self.hit_size[1]*1 +offset[1]
                    else:

                        y = y - size[1] + self.hit_size[1]/2
                        if (i == 4):
                            x = x -size[0]+offset[0]+90
                        else:
                            x = x - size[0]+offset[0]
                        
                elif (dtype == 'Motor B'):
                    if (i == 4  and orient < 0):
                        b = wx.BitmapFromImage(image)
                        size = b.GetSize()
                        x,y = self.centres[5]
                        x = x - self.hit_size[0]*2
                        y = y - size[1] + self.hit_size[1]*1 +offset[1]
                    else:
                        y = y - size[1] + self.hit_size[1]
                        if (i == 4):
                            x = x -size[0]+offset[0]+90
                        else:
                            x = x - size[0]+offset[0]
                    
                else:
                    x = x - (size[0]) + offset[0]
                    y = y - (size[1]/2) + offset[1]

            elif (i in [8, 9, 10]):
                if (image):
                    # +90 rotation needed
                    b = wx.BitmapFromImage(image.Rotate90(clockwise=True))
                    size = b.GetSize()
                    offset = (-10, 0)
                

                if (dtype == 'Motor A'):
                    if (i == 10  and orient < 0):
                        b = wx.BitmapFromImage(image.Rotate90().Rotate90())
                        size = b.GetSize()
                        x,y = self.centres[11]
                        x = x - self.hit_size[0]*1 + offset[1]
                        y = y - 90 + offset[0]
                    else:

                        y = y + size[1] - self.hit_size[1]*3
                        if (i == 10):
                            x = x +offset[0]-90
                        else:
                            x = x +offset[0]
                        
                elif (dtype == 'Motor B'):
                    if (i == 10  and orient < 0):
                        b = wx.BitmapFromImage(image.Rotate90().Rotate90())
                        size = b.GetSize()
                        x,y = self.centres[11]
                        x = x - self.hit_size[0]*0.5 + offset[1]
                        y = y - 90 + offset[0]
                    else:
                        y = y - size[1] + self.hit_size[1]*1.5
                        if (i == 10):
                            x = x +offset[0]-90
                        else:
                            x = x +offset[0]
                    
                else:
                    x = x + offset[0]
                    y = y - (size[1]/2) + offset[1]
                
            else:
                if (image):
                    # 180 rotation needed
                    b = wx.BitmapFromImage(image.Rotate90().Rotate90())
                    size = b.GetSize()
                    offset = (0, -10)
                

                if (dtype == 'Motor A'):
                    if (i == 1  and orient < 0):
                        b = wx.BitmapFromImage(image.Rotate90(clockwise=False))
                        size = b.GetSize()
                        x,y = self.centres[2]
                        x = x - size[0] + self.hit_size[0]
                        y = y - 90 + offset[1]
                    else:

                        x = x - self.hit_size[0]*2
                        if (i == 1):
                            y = y +offset[1]-90
                        else:
                            y = y + offset[1]
                        
                elif (dtype == 'Motor B'):
                    if (i == 1  and orient < 0):
                        b = wx.BitmapFromImage(image.Rotate90(clockwise=False))
                        size = b.GetSize()
                        x,y = self.centres[2]
                        x = x - size[0] + self.hit_size[0]
                        y = y - 90 + + self.hit_size[1]*0.5 + offset[1] 
                    else:
                        x = x - size[0] + self.hit_size[0]*1
                        if (i == 1):
                            y = y +offset[1]-90
                        else:
                            y = y + offset[1]
                    
                else:
                    x = x - (size[0]/2) + offset[0]
                    y = y + offset[1]

            if (image):
                dc.DrawBitmap(b, x, y, True)
                self.locations_full.append((i, cfg[i][0], wx.Rect(x, y, size[0], size[1])))
            else:
                self.locations_empty.append((i, wx.Rect(x, y, size[0], size[1])))
                                 
        if (not overlay):
            overlay = device_data.get_overlay_bmap()
        
        dc.DrawBitmap(overlay, self.mb_origin[0], self.mb_origin[1], True)

        self.SetVirtualSize(self.window_size)



    def update_move_centre_pt(self, screen_centre_pt, name, drag_image):
        centre_pt = self.ScreenToClient(screen_centre_pt)
##        # BED zooming support
##        if (self.zoom != 1.0):
##            centre_pt.Set(centre_pt.x/self.zoom, centre_pt.y/self.zoom)
        return self.local_move_centre_pt(centre_pt, name, drag_image)
    
    def local_move_centre_pt(self, centre_pt, name, drag_image):
        # check in zones to speed things up
        location = -1
        update = False
        detail_index = -1
        centre_pt = self.CalcUnscrolledPosition(centre_pt)
        which_id = 0
        
        # BED zooming support
        if (self.zoom != 1.0):
            centre_pt.Set(centre_pt.x/self.zoom, centre_pt.y/self.zoom)

        for loc, rect in self.locations_empty:
            if (rect.InsideXY(centre_pt.x, centre_pt.y)):
                location = loc
                break

        if (location != self.zone_hit):
            good = win_data.config_check(location, name)
            dc = None
            origin = self.mb_origin[:]
            
            if (good):
                # put the overlay on
                overlay = device_data.get_overlay_bmap(location)
            else:
                # put no overlay on
                overlay = device_data.get_overlay_bmap()

            if (self.zoom != 1.0):
                image = overlay.ConvertToImage()
                w = image.GetWidth() * self.zoom
                h = image.GetHeight() * self.zoom
                image.Rescale(w, h)
                overlay = image.ConvertToBitmap()
                origin[0] *= self.zoom
                origin[1] *= self.zoom
                

            dc = wx.ClientDC(self)
            self.DoPrepareDC(dc)
            drag_image.Hide()
            update = True
            dc.DrawBitmap(overlay, origin[0], origin[1], True)
                
            self.zone_hit = location

        return location, update, None



    # --------------- Drag Image handling --------------------------------

    def hit_test(self, pt):
        """Is the point on a device?"""
        for loc, name, rect in self.locations_full:
            if (rect.InsideXY(pt.x, pt.y)):
                dtype,name = win_data.config_get(loc)
                if (dtype):
                    return (loc, dtype)
                else:
                    return (-1, None)

        return (-1, None)

    
    def on_left_down(self, event):
        # Make sure that we have the focus
        #self.SetFocus()

        pt = self.CalcUnscrolledPosition(event.GetPosition())
        # BED zooming support
        if (self.zoom != 1.0):
            pt.Set(pt.x/self.zoom, pt.y/self.zoom)

        self.drag_loc, self.drag_name = self.hit_test(pt)

        if (self.drag_loc >= 0):
            self.drag_start_pos = pt
            # also set the selection and update the help window
            win_data.selection_take('cwork', self.drag_name, self.drag_loc)
            
        # Don't allow movements in basic mode
        if (not win_data.get_adv_mode()):
            self.drag_loc = -1
            self.drag_name = None
            self.drag_start_pos = None
            


    def on_left_up(self, event):
        loc = -1
        if (self.drag_image):
            pt = event.GetPosition()
            loc,update,dummy = self.local_move_centre_pt(pt, self.drag_name, self.drag_image)
            
            self.drag_bmp = None
            self.drag_image.Hide()
            self.drag_image.EndDrag()
            self.drag_image = None

            # check if we are removing it, is the program using it?
            if (win_data.config_check(loc, self.drag_name)):
                win_data.config_move_end(loc)
                win_data.click_sound()
            else:
                if (win_data.get_ok_to_delete("Module")):
                    if (not win_data.config_move_to_trash()):
                        # can't drop it - put it back
                        error_message="Can not delete the device as it is used in the program.\n" +\
                                       "Delete it from the program before deleting it here."
                        wx.MessageBox(error_message, caption="Can't delete device.", style=wx.OK | wx.ICON_ERROR)
                                   
                        win_data.config_move_abort()
                else:
                    win_data.config_move_abort()
                
        # force the work area to redraw
        self.SetCursor(wx.NullCursor)
        self.Refresh()
        win_data.force_redraw('config')
            
    
    def on_mouse_motion(self, event):
        if (self.drag_loc < 0 or not event.Dragging() or not event.LeftIsDown()):
            return

        pt = event.GetPosition()
        
        if (not self.drag_image):
            # BED zooming support
            check_pt = wx.Point(pt.x/self.zoom, pt.y/self.zoom)

            tolerance = 4
            
            dx = abs(check_pt.x - self.drag_start_pos.x)
            dy = abs(check_pt.y - self.drag_start_pos.y)
            if (dx <= tolerance and dy <= tolerance):
                return

            # remove the old one but remember it if we have to put it back
            self.drag_start = (self.drag_loc, self.drag_name)
            win_data.config_move_start(self.drag_loc)
            # force the work area to redraw
            self.Refresh()
            self.Update()
            win_data.force_redraw('config')

            # get the selected variant since we had to click to get here
            bmp = device_data.get_device_bmap(self.drag_name, True)
            if (self.zoom != 1.0):
                image = bmp.ConvertToImage()
                w = image.GetWidth() * self.zoom
                h = image.GetHeight() * self.zoom
                image.Rescale(w, h)
                bmp = image.ConvertToBitmap()
            
            self.drag_image = wx.DragImage(bmp, wx.StockCursor(wx.CURSOR_HAND))
            #dev_x,dev_y = device_data.get_device_size()
            dev_x,dev_y = bmp.GetSize()
            hotspot = (dev_x/2, dev_y/2)
            #print "on_mouse_motion: hotspot", hotspot

            self.drag_image.BeginDrag(hotspot, self, False, self.GetClientRect())
            loc,update,dummy = self.local_move_centre_pt(pt, self.drag_name, self.drag_image)
            self.drag_image.Move(pt)
            self.drag_image.Show()
        else:
            loc,update,dummy = self.local_move_centre_pt(pt, self.drag_name, self.drag_image)
            self.drag_image.Move(pt)
            if (update):
                self.drag_image.Show()
                
##            else:
##                # if we are out of the window then scroll in this direction
##                size = self.GetClientSize()
##                start = self.GetViewStart()
##                total = self.GetVirtualSize()
##                scroll_pixels = self.GetScrollPixelsPerUnit()
                
##                if (pt.x < start[0] and (start[0] > 0)):
##                    print "Scroll left"
##                elif (pt.x > (start[0] + size[0]) and (pt.x < total[0])):
##                    print "Scroll right"
##                elif (pt.y < start[1] and (start[1] > 0)):
##                    self.Scroll(-1, (start[1]-pt.y)/scroll_pixels[1])
##                    self.Refresh()
##                elif (pt.y > (start[1] + size[1]) and (pt.y < total[1])):
##                    self.Scroll(-1, (start[1]+pt.y)/scroll_pixels[1])
##                    self.Refresh()
