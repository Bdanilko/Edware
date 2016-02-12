#!/usr/bin/env python

# * **************************************************************** **
#
# File: program_work.py
# Desc: Use the work window for program tasks
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


import sys
import wx

import work_win
import win_data
import bric_data

class Program_work(work_win.Work_win):
    def __init__(self, parent, frame):
        work_win.Work_win.__init__(self, parent)
        self.frame = frame
        self.selected_id = -1
        self.drop_locations = []
        self.pickup_locations = []
        self.program_flows = []

        self.zone_hit = -1
        self.zone_arrow = None
        self.big_x = -1

        self.zoom = 1.0

        self.adj = None
        self.connections = {}

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.drag_id = -1
        self.drag_image = None
        self.drag_start = (-1, None)
        self.drag_start_pos = None
        self.drag_which = 0

        # ((right-not-sel, right-sel), (left-not-sel, left-sel))
        self.arrows = ((bric_data.get_arrow_bmap(True, False),
                        bric_data.get_arrow_bmap(True, True)),
                       (bric_data.get_arrow_bmap(False, False),
                        bric_data.get_arrow_bmap(False, False)))

        self.arrow_w, self.arrow_h = self.arrows[0][0].GetSize()

        self.normal_h = 90
        self.normal_w = 90

##        self.scroll_timer = wx.Timer(self)
##        self.scroll_timer.Start(300, oneShot=False)

##        self.scroll_x = 0
##        self.scroll_y = 0

        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
##        self.Bind(wx.EVT_TIMER, self.on_scroll_timeout)


    def on_move(self, event):
        self.on_size(event)

    def on_size(self, event):
        # send the new size to the program pallete
        size = self.GetClientSize()
        upper_left = self.GetClientAreaOrigin()
        #print size, upper_left, self.ClientToScreen(upper_left), self.GetClientRect()
        upper_left = self.ClientToScreen(upper_left)
        rect = wx.Rect(upper_left[0], upper_left[1], size[0], size[1])
        #print "Program Work:", rect

        #self.SetScrollbars(20, 20, size[0]/20, size[1]/20)

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
        #print "Starting paint"
        self.y_offset = 0
        dc = wx.PaintDC(self)
        self.DoPrepareDC(dc)

        # Things can move about now
        self.zone_hit = -1

        dc.SetBackground(wx.Brush("white", wx.SOLID))
        dc.SetUserScale(self.zoom, self.zoom)
        dc.Clear()

        ourGray = wx.Colour(red=108, green=109, blue=112)
        ourPen = wx.Pen(ourGray, 12)
        ourPen.SetCap(wx.CAP_BUTT)
        dc.SetPen(ourPen)
        dc.SetBrush(wx.Brush(ourGray, wx.SOLID))

        centre_line = 0
        centre_line_buffer = 200
        left = 20
        loop_returns = {}

        self.drop_locations = []
        self.pickup_locations = []

        streams = win_data.program().get_stream_count()
        stream = 0
        x = 20
        biggest_x = 0

        limits = []
        while (stream < streams):
            # is the stream being moved (ready for deletion)
            if (win_data.program().get_stream_id(stream) == -1):
                stream += 1
                continue

            compute_connections = {}
            x = 20
            tree_data, adj, min_min_up = win_data.program().get_tree_data(stream)
            #print "tree_data", tree_data
            #print "Adj", adj, "min_min_up", min_min_up

            self.adj = adj
            self.compute_placement(x, 0, tree_data, 0, compute_connections)

            #print "Compute_connections", compute_connections
            # find the smallest and biggest y and biggest x
            initialised = False
            x_max = 0
            x_min = 0
            y_max = 0
            y_min = 0

            for bric_id in compute_connections:
                for point in compute_connections[bric_id]:
                    x, y = point
                    if (not initialised):
                        x_max = x_min = x
                        y_max = y_min = y
                        initialised = True
                    else:
                        if (x > x_max):
                            x_max = x
                        if (x < x_min):
                            x_min = x
                        if (y > y_max):
                            y_max = y
                        if (y < y_min):
                            y_min = y

            #print "x_max", x_max, "y_max", y_max, "x_min", x_min, "y_min", y_min
            limits.append((x_min, x_max, y_min, y_max))

            stream += 1

        #print "Limits", limits
        centre_line = 0
        visible_stream = 0
        stream = 0
        x = 20

        while (stream < streams):

            # is the stream being moved (ready for deletion)
            if (win_data.program().get_stream_id(stream) == -1):
                stream += 1
                continue

            win_data.program().zero_connections(self.connections)

            tree_data, adj, min_min_up = win_data.program().get_tree_data(stream)
##            print "tree_data", tree_data
##            print "Adj", adj, "min_min_up", min_min_up
##            if (min_min_up < 0):
##                centre_line += (min_min_up * -1 * 100)
##                print "Centre_line dropped:", min_min_up * -100

            self.adj = adj

            y_offset = limits[visible_stream][2] - 100
            centre_line += -1 * y_offset;

            y_range = limits[visible_stream][3] - limits[visible_stream][2]
            bottom_adjust = y_range - (-1 * y_offset) + 100

            #print "Centre_line", centre_line
            (x_max, cl_max) = self.paint_flow(dc, x, centre_line, tree_data, 0, stream)
            #print "from paint_flow():", x_max, cl_max

            x_offset = limits[visible_stream][1] + 20
            if (x_offset > biggest_x):
                biggest_x = x_offset
                self.big_x = biggest_x
                #print "Biggest x", biggest_x

            centre_line += bottom_adjust
            #print "bottom centre_line", bottom_adjust, centre_line

            stream += 1
            visible_stream += 1


        # now need the point for adding new streams
        x = left
        cl = centre_line + 100
        x, bmap_size = self.draw_bmap(dc, "new_event", x, cl, 0)
        self.drop_locations.append((0, None, (left, cl-bmap_size[1]/2), 0,
                                    wx.Rect(left, cl-bmap_size[1]/2, bmap_size[0], bmap_size[1])))

        #print "Post-Bounding box", dc.MinY(), dc.MaxY()
        self.SetVirtualSize(((biggest_x+20) * self.zoom,(cl + centre_line_buffer)*self.zoom))

        #print "drop_locations", self.drop_locations
        #print "pickup_locations", self.pickup_locations
        #print "connections", self.connections


    def compute_placement(self, x, cl_base, flow, branch, connections):
        # flow starts with cl adjustment then nodes
        cl_adjust = 90
        cl_skip = 90+10
        cl_max = cl_base
        x_max = x
        new_cl = [cl_base, cl_base]

        cl = cl_base
        i = 1
        end = len(flow)-1
        while (i < end):

            if (flow[i] == -2):
                (big_x_1, new_cl_1) = self.compute_placement(x, new_cl[0], flow[i+1], 0, connections)
                (big_x_2, new_cl_2) = self.compute_placement(x, new_cl[1], flow[i+2], 1, connections)
                i += 3

                # Next one will be the End so can connect up unequal branches then
                x = max(big_x_1, big_x_2)

            else:
                bric_id = flow[i]

                if (bric_id not in connections):
                    connections[bric_id] = [None, None, None]

                name = win_data.program().get_bric_name(bric_id)
                prev_0 = win_data.program().get_prev_id(bric_id, 0)
                if (prev_0 > 0):
                    prev_name_0 = win_data.program().get_bric_name(prev_0)

                if (name not in ("If","Loop", "EndIf", "EndLoop")):
                    # draw the bric, then the arrow
                    connections[bric_id][0] = (x,cl)
                    connections[bric_id][1] = (x,cl)

                    x = self.compute_bmap(name, x, bric_id)
                    # allow for an arrow
                    x += self.arrow_w
                    connections[bric_id][2] = (x,cl)

                elif (name in ("EndIf", "EndLoop")):
                    # draw the bric, then the arrow
                    connections[bric_id][0] = (x, cl-cl_adjust)
                    connections[bric_id][1] = (x, cl+cl_adjust)

                    x = self.compute_bmap(name, x, bric_id)

                    # allow for an arrow
                    x += self.arrow_w
                    connections[bric_id][2] = (x,cl)

                elif (name == "Loop"):

                    connections[bric_id][0] = (x, cl)

                    x = self.compute_bmap(name, x, bric_id)

                    # allow for an arrow
                    x += self.arrow_w

                    connections[bric_id][1] = (x, cl-cl_adjust)
                    connections[bric_id][2] = (x, cl+cl_adjust)


                    # Create two streams and be intelligent about the hit points
                    top, bot = self.adj[bric_id]

                    new_cl = (cl - cl_adjust + top*cl_skip, cl + cl_adjust + bot*cl_skip)


                else:
                    connections[bric_id][0] = (x, cl)
                    # draw the bric, then the arrow
                    x = self.compute_bmap(name, x, bric_id)

                    # allow for the arrows
                    x += self.arrow_w

                    connections[bric_id][1] = (x, cl-cl_adjust)
                    connections[bric_id][2] = (x, cl+cl_adjust)


                    # Create two streams and be intelligent about the hit points
                    top, bot = self.adj[bric_id]

                    new_cl = (cl - cl_adjust + top*cl_skip, cl + cl_adjust + bot*cl_skip)


                i += 1


        return (x,cl_max)


    def compute_bmap(self, name, x, bric_id):
        if (name == "new_event"):
            bmap = bric_data.get_new_bmap(False)
        elif (name == 'If'):
            if_var = win_data.program().get_bric_if_variant(bric_id)
            if (win_data.selection_check('pwork', None, bric_id)):
                bmap = bric_data.get_if_bmap(if_var, True)
            else:
                bmap = bric_data.get_if_bmap(if_var, False)

        else:
            if (win_data.selection_check('pwork', None, bric_id)):
                bmap = bric_data.get_bric_bmap(name, bric_data.BRIC_SELECTED)
            else:
                bmap = bric_data.get_bric_bmap(name, bric_data.BRIC_NORMAL)

        x += bmap.GetWidth()
        return x



    def paint_flow(self, dc, x, cl_base, flow, branch, stream):
        #print "paint_flow() x:", x, "cl_base:", cl_base, "flow:", flow

        # flow starts with cl adjustment then nodes
        cl_adjust = 90
        cl_skip = 90+10
        cl_max = cl_base
        x_max = x
        new_cl = [cl_base, cl_base]
        loop_returns = {}
        self.in_paint = True

        #cl = cl_base + flow[0] * cl_adjust
        cl = cl_base
        i = 1
        end = len(flow)-1
        while (i < end):

            if (flow[i] == -2):
                (big_x_1, new_cl_1) = self.paint_flow(dc, x, new_cl[0], flow[i+1], 0, stream)
                (big_x_2, new_cl_2) = self.paint_flow(dc, x, new_cl[1], flow[i+2], 1, stream)
                i += 3

                # Next one will be the End so can connect up unequal branches then

                x = max(big_x_1, big_x_2)
                if (new_cl_1 > cl_max):
                    cl_max = new_cl_1

                if (new_cl_2 > cl_max):
                    cl_max = new_cl_2

            else:
                bric_id = flow[i]

                name = win_data.program().get_bric_name(bric_id)
                prev_0 = win_data.program().get_prev_id(bric_id, 0)
                if (prev_0 > 0):
                    prev_name_0 = win_data.program().get_bric_name(prev_0)

                if (name not in ("If","Loop", "EndIf", "EndLoop")):
                    # draw the bric, then the arrow
                    self.connections[bric_id][0] = (x,cl)
                    self.connections[bric_id][1] = (x,cl)
                    x = self.draw_bmap_and_add_location(dc, name, x, cl, bric_id, branch)
                    # draw an arrow
                    self.draw_arrow_and_add_location(dc, 0, x, cl, bric_id, branch)
                    x += self.arrow_w
                    self.connections[bric_id][2] = (x,cl)

##                    #BED try connecting everything
##                    print "not-if-loop-end"
##                    if (prev_0 > 0):
##                        if (prev_name_0 in ("Loop", "If")):
##                            self.connect(dc, self.connections[prev_0][branch+2], self.connections[bric_id][0])
##                        else:
##                            self.connect(dc, self.connections[prev_0][2], self.connections[bric_id][0])

                elif (name in ("EndIf", "EndLoop")):
                    # draw the bric, then the arrow
                    self.connections[bric_id][0] = (x, cl-cl_adjust)
                    self.connections[bric_id][1] = (x, cl+cl_adjust)

                    x = self.draw_bmap_and_add_location(dc, name, x, cl, bric_id, branch)
                    # draw an arrow
                    self.draw_arrow_and_add_location(dc, 0, x, cl, bric_id, branch)
                    x += self.arrow_w
                    self.connections[bric_id][2] = (x, cl)

                    # Check for connecting the lines for unequal lengths and loops
                    start_bric_id = bric_id - 1
                    prev_name = win_data.program().get_bric_name(start_bric_id)
                    if (prev_name == "Loop"):
                        # draw a line if more then 1 apart
                        #print "end-loop"
                        if (prev_0 != bric_id - 1):
                            self.connect(dc, self.connections[bric_id][0],
                                         self.connections[prev_0][2])

                        self.connect(dc, self.connections[bric_id][1],
                                     self.connections[bric_id-1][2])

                    else: # If
                        prev_0 = win_data.program().get_prev_id(bric_id, 0)
                        prev_1 = win_data.program().get_prev_id(bric_id, 1)
                        #print "Bric id:", bric_id, prev_0, prev_1
                        #print "end-if"
                        if (prev_0 == bric_id-1):
                            self.connect(dc, self.connections[bric_id][0],
                                         self.connections[prev_0][1])
                        else:
                            self.connect(dc, self.connections[bric_id][0],
                                         self.connections[prev_0][2])

                        if (prev_1 == bric_id-1):
                            self.connect(dc, self.connections[bric_id][1],
                                         self.connections[prev_1][2])
                        else:
                            self.connect(dc, self.connections[bric_id][1],
                                         self.connections[prev_1][2])

                elif (name == "Loop"):

                    self.connections[bric_id][0] = (x, cl)
                    # draw the bric, then the arrow
                    x = self.draw_bmap_and_add_location(dc, name, x, cl, bric_id, branch)

                    arrow_y = self.draw_arrow(dc, 1, x, cl+cl_adjust)
                    self.draw_arrow_and_add_location(dc, 0, x, cl-cl_adjust, bric_id, branch)
                    x += self.arrow_w
                    self.connections[bric_id][1] = (x, cl-cl_adjust)
                    self.connections[bric_id][2] = (x, cl+cl_adjust)

##                    #BED try connecting everything
##                    prev_0 = win_data.program().get_prev_id(bric_id, 0)
##                    print "loop"
##                    self.connect(dc, self.connections[prev_0][2], self.connections[bric_id][0])

                    # Create two streams and be intelligent about the hit points
                    top, bot = self.adj[bric_id]

                    new_cl = (cl - cl_adjust + top*cl_skip, cl + cl_adjust + bot*cl_skip)

                    if ((top < 0) and win_data.program().get_next_id(bric_id, 0) != (bric_id+1)):
                        self.connect(dc, self.connections[bric_id][1], (x,new_cl[0]))

##                    if (bot > 0):
##                        self.connect(dc, self.connections[bric_id][2], (x,new_cl[1]))


                    if (new_cl[1] > cl_max):
                        cl_max = new_cl[1]


                else:
                    self.connections[bric_id][0] = (x, cl)
                    # draw the bric, then the arrow
                    x = self.draw_bmap_and_add_location(dc, name, x, cl, bric_id, branch)
                    # draw two arrows

                    self.draw_arrow_and_add_location(dc, 0, x, cl-cl_adjust, bric_id, 0)
                    self.draw_arrow_and_add_location(dc, 0, x, cl+cl_adjust, bric_id, 1)
                    x += self.arrow_w
                    self.connections[bric_id][1] = (x, cl-cl_adjust)
                    self.connections[bric_id][2] = (x, cl+cl_adjust)

##                    #BED try connecting everything
##                    prev_0 = win_data.program().get_prev_id(bric_id, 0)
##                    print "if"
##                    self.connect(dc, self.connections[prev_0][2], self.connections[bric_id][0])

                    # Create two streams and be intelligent about the hit points
                    top, bot = self.adj[bric_id]

                    new_cl = (cl - cl_adjust + top*cl_skip, cl + cl_adjust + bot*cl_skip)

                    if ((top < 0) and win_data.program().get_next_id(bric_id, 0) != (bric_id+1)):
                        self.connect(dc, self.connections[bric_id][1], (x,new_cl[0]))

                    if ((bot > 0) and win_data.program().get_next_id(bric_id, 1) != (bric_id+1)):
                        self.connect(dc, self.connections[bric_id][2], (x,new_cl[1]))

                    if (new_cl[1] > cl_max):
                        cl_max = new_cl[1]

                i += 1

        #print "paint_flow returns", (x,1)

        # now do the final bric - Last
        if (flow[0] == 0):
            #print "Flow:", flow[0], "i:", i, "Stream:", stream
            if (stream == 0):
                new_x, bmap_size = self.draw_bmap(dc, "Last", x, cl, 0)
            else:
                new_x, bmap_size = self.draw_bmap(dc, "EndEvent", x, cl, 0)


        self.in_paint = False

        return (x,cl_max)

        #print self.drop_locations
        #print self.pickup_locations

    def draw_arrow(self, dc, atype, x, cl):
        arrow_y = cl-self.arrow_h/2
        dc.DrawBitmap(self.arrows[atype][0], x, arrow_y, True)

        return arrow_y

    def draw_arrow_and_add_location(self, dc, atype, x, cl, bric_id, which_id):
        arrow_y = self.draw_arrow(dc, atype, x, cl)

        # add the location
        self.drop_locations.append((bric_id, atype, (x, arrow_y), which_id,
                               wx.Rect(x, cl-self.normal_h/2, self.normal_w+self.arrow_w, self.normal_h)))
        return arrow_y

    def draw_bmap(self, dc, name, x, cl, bric_id):
        # **BED** scale bitmap if needed
        #print "Drawing:", name, "x:",x, "cl:", cl, "bric_id:", bric_id

        if (name == "new_event"):
            bmap = bric_data.get_new_bmap(False)
        elif (name == 'If'):
            if_var = win_data.program().get_bric_if_variant(bric_id)
            if (win_data.selection_check('pwork', None, bric_id)):
                bmap = bric_data.get_if_bmap(if_var, True)
            else:
                bmap = bric_data.get_if_bmap(if_var, False)

        else:
            if (win_data.selection_check('pwork', None, bric_id)):
                bmap = bric_data.get_bric_bmap(name, bric_data.BRIC_SELECTED)
            else:
                bmap = bric_data.get_bric_bmap(name, bric_data.BRIC_NORMAL)

        y = cl - bmap.GetHeight()/2

        dc.DrawBitmap(bmap, x, y, True)
        x += bmap.GetWidth()
        return (x, bmap.GetSize())

    def draw_bmap_and_add_location(self, dc, bric_name, x, cl, bric_id, which_id):
        new_x, bmap_size = self.draw_bmap(dc, bric_name, x, cl, bric_id)

        # add the location but skip "Start Main" and "End" tokens
        if ((bric_id > 1) and (not bric_name.startswith("End")) and (bric_name != "Last")):
            self.pickup_locations.append((bric_id, bric_name, which_id,
                                          wx.Rect(x, cl-bmap_size[1]/2, bmap_size[0], bmap_size[1])))

##        # add the location but skip "Start Main" and "End" and event tokens with children
##        if ((bric_id > 1 and (bric_name != "End")) and
##            ((bric_name != "Event" or win_data.program().get_next_id(bric_id, 0) == -1))):
##            self.pickup_locations.append((bric_id, bric_name, which_id,
##                                          wx.Rect(x, cl-bmap_size[1]/2, bmap_size[0], bmap_size[1])))
        return new_x

    def connect(self, dc, point1, point2):
        if (point1 != point2):
            #print "connecting (%d, %d) -> (%d, %d)" % (point1[0], point1[1], point2[0], point2[1])
            dc.DrawLine(point1[0], point1[1], point2[0], point2[1])

    # --------------- Hit testing from pallete --------------------------------------

    def update_move_centre_pt(self, screen_centre_pt, name, drag_image):
        centre_pt = self.ScreenToClient(screen_centre_pt)
        return self.local_move_centre_pt(centre_pt, name, drag_image)

    def local_move_centre_pt(self, centre_pt, name, drag_image):
        location = -1
        arrow_type = 0
        update = False
        centre_pt = self.CalcUnscrolledPosition(centre_pt)

        # BED zooming support
        if (self.zoom != 1.0):
            centre_pt.Set(centre_pt.x/self.zoom, centre_pt.y/self.zoom)
        which_id = 0

        for bric_id, atype, arrow_loc, which_id, rect in self.drop_locations:
            #for prev_index, arrow, rect in self.drop_locations:
            if (rect.InsideXY(centre_pt.x, centre_pt.y)):
                if (bric_id == 0):
                    # new-event bric
                    if (name in ["Event", "Subroutine"]):
                        location = 0
                    else:
                        location = -1

                # Events can only go in 1 spot
                elif (name in ["Event", "Subroutine"]):
                    location = -1

                else:
                    location = bric_id

                arrow_type = atype
                # Can't hit two rectangles at the same time
                break

        if (location != self.zone_hit):
            dc = wx.ClientDC(self)
            self.DoPrepareDC(dc)
            drag_image.Hide()
            if (self.zone_hit != -1):
                # there was a selected arrow (or new event) - extinguish it
                if (self.zone_hit == 0):
                    self.draw_new_bmap(dc, self.zone_arrow, False)
                else:
                    # an arrow
                    self.draw_arrow_for_pallete(dc, arrow_type, self.zone_arrow, 0)
                update = True

            # now draw the new one
            if (location != -1):
                if (location == 0):
                    self.draw_new_bmap(dc, arrow_loc, True)
                else:
                    self.draw_arrow_for_pallete(dc, arrow_type, arrow_loc, 1)
                self.zone_arrow = arrow_loc
                update = True

            self.zone_hit = location

        return location, update, which_id

    def draw_arrow_for_pallete(self, dc, atype, location, selected):
        bmap = self.arrows[atype][selected]
        if (self.zoom != 1.0):
            image = bmap.ConvertToImage()
            w = image.GetWidth() * self.zoom
            h = image.GetHeight() * self.zoom
            image.Rescale(w, h)
            bmap = image.ConvertToBitmap()


        dc.DrawBitmap(bmap, location[0]*self.zoom, location[1]*self.zoom, True)


    def draw_new_bmap(self, dc, location, selected):
        bmap = bric_data.get_new_bmap(selected)
        if (self.zoom != 1.0):
            image = bmap.ConvertToImage()
            w = image.GetWidth() * self.zoom
            h = image.GetHeight() * self.zoom
            image.Rescale(w, h)
            bmap = image.ConvertToBitmap()

        dc.DrawBitmap(bmap, location[0]*self.zoom, location[1]*self.zoom, True)



    # --------------- Drag Image handling --------------------------------

    def hit_test(self, centre_pt):
        """Is the point on a bric?"""

        for bric_id, name, which_id, rect in self.pickup_locations:
            if (rect.InsideXY(centre_pt.x, centre_pt.y)):
                return (bric_id, name, which_id)

        return (-1, None, -1)


    def on_left_down(self, event):
        # Make sure that we have the focus
        #self.SetFocus()

        pt = self.CalcUnscrolledPosition(event.GetPosition())

        # BED zooming support
        if (self.zoom != 1.0):
            pt.Set(pt.x/self.zoom, pt.y/self.zoom)

        #print "Left-down:", pt

        self.drag_id, self.drag_name, self.drag_which = self.hit_test(pt)
        if (self.drag_id >= 0):
            self.drag_start_pos = pt
            # also set the selection and update the help window
            win_data.selection_take('pwork', self.drag_name, self.drag_id)


    def on_left_up(self, event):
        loc = -1
        self.scroll_x, self.scroll_y = 0,0

        if (self.drag_image):
            pt = event.GetPosition()
            loc,update,which_id = self.local_move_centre_pt(pt, self.drag_name, self.drag_image)

            self.drag_bmp = None
            self.drag_image.Hide()
            self.drag_image.EndDrag()
            self.drag_image = None

            if (loc == -1):
                win_data.selection_drop_all()
                if (not win_data.get_ok_to_delete("Program")):
                    win_data.program().abort_move()
                else:
                    win_data.program().end_move(loc, which_id)
                    self.big_x = -1
                    self.Refresh(True)
                    self.Update()
            else:
                win_data.program().end_move(loc, which_id)
                win_data.click_sound()

        # force the work area to redraw
        self.SetCursor(wx.NullCursor)
        self.Refresh()


    def on_mouse_motion(self, event):
        if (self.drag_id < 0 or not event.Dragging() or not event.LeftIsDown()):
            return

        ok_to_drag = win_data.program().check_drag(self.drag_id, self.drag_name)
        if (not ok_to_drag):
            return

        raw_pt = event.GetPosition()
        check_pt = self.CalcUnscrolledPosition(raw_pt)


        if (not self.drag_image):
            # BED zooming support
            check_pt = wx.Point(check_pt.x/self.zoom, check_pt.y/self.zoom)
            #print "Move, raw:", raw_pt, "check:", check_pt

            tolerance = 4

            dx = abs(check_pt.x - self.drag_start_pos.x)
            dy = abs(check_pt.y - self.drag_start_pos.y)
            if (dx <= tolerance and dy <= tolerance):
                return

            #print "Start drag with movement:", dx, dy
            # remove the old one but remember it if we have to put it back
            self.drag_start = (self.drag_id, self.drag_name)
            win_data.program().start_move(self.drag_id, self.drag_which)
            # force the work area to redraw
            self.Refresh()
            self.Update()

            # get the selected variant since we had to click to get here
            bmp = bric_data.get_bric_bmap(self.drag_name, bric_data.BRIC_SELECTED)

            if (self.zoom != 1.0):
                image = bmp.ConvertToImage()
                w = image.GetWidth() * self.zoom
                h = image.GetHeight() * self.zoom
                image.Rescale(w, h)
                bmp = image.ConvertToBitmap()

            self.drag_image = wx.DragImage(bmp, wx.StockCursor(wx.CURSOR_HAND))
            dev_x,dev_y = bmp.GetSize()
            hotspot = (dev_x/2, dev_y/2)


            self.drag_image.BeginDrag(hotspot, self, False, self.GetClientRect())
            loc, update,which_id = self.local_move_centre_pt(raw_pt, self.drag_name, self.drag_image)
            self.drag_image.Move(raw_pt)
            self.drag_image.Show()

        else:

            loc, update,which_id = self.local_move_centre_pt(raw_pt, self.drag_name, self.drag_image)
            self.drag_image.Move(raw_pt)

            if (update):
                self.drag_image.Show()
