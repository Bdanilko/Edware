#!/usr/bin/env python

# * **************************************************************** **
#
# File: gui.py
# Desc: Master file to put all of the gui elements together.
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
# Svn: $Id: bricworks.py 52 2006-12-03 00:44:40Z briand $
# * **************************************************************** */

import wx
import os
import os.path
import glob
import sys
import cPickle

import gui.config_win
import gui.var_win
import gui.detail_win
import gui.help_win
import gui.program_pallete
import gui.config_pallete
import gui.program_work
import gui.config_work
import gui.downloader
import gui.about

import gui.win_data

SESSION_FILE_NAME = "edware_session.dat"
USER_DIR = "."

class Session_data(object):
    def __init__(self):
        self.sdata_version = 11
        self.win_size = (800,600)
        self.win_pos = None
        self.sashes = [140, 120, -120]
        self.advanced_mode = False
        self.edison_mode = True
        self.usb_device = ""
        self.toolbar = True
        self.main_window = 'program'
        self.strict_versions = True

    def __cmp__(self, rhs):
        return cmp(self.__dict__, rhs.__dict__)

    def convert_from_3(self, v3_data):
        self.sdata_version = 4
        self.strict_versions = True

        self.win_size = v3_data.win_size
        self.win_pos = v3_data.win_pos
        self.sashes = v3_data.sashes
        self.advanced_mode = v3_data.advanced_mode
        self.usb_device = v3_data.usb_device
        self.toolbar = v3_data.toolbar
        self.main_window = v3_data.main_window

sdata = Session_data()
sdata_changed = True


class Bricworks_frame(wx.Frame):
    def __init__(self, parent, title="Edison EdWare"):
        wx.Frame.__init__(self, parent, title=title, size=(800, 500))

##        splash_bmap = wx.Bitmap("gui/devices/motherboard.png", wx.BITMAP_TYPE_ANY)
##        wx.SplashScreen(splash_bmap, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT, 2000, self, -1)
##        wx.Yield()

        self.save_path = os.getcwd()
        self.save_file = ""

        self.splitter_done = False
        self.splitter_attempts = 0

        self.menu_data = (("&File",
                           ("New", "Start a new program", self.menu_new_edison),
                           ("&Open", "Open an existing program", self.menu_open),
                           ("", "", ""),
                           ("&Save", "Save the current program", self.menu_save),
                           ("Save &As", "Save the current program under a new name", self.menu_saveas),
                           ("", "", ""),
                           ("&Exit", "Exit EdWare", self.menu_exit)),

                          # ("&View",
                          #  ("*&Configuration view", "Edit the module configuration", self.menu_config),
                          #  ("*&Program view", "Edit the program", self.menu_program),
##                           ("", "", ""),
##                           ("Zoom - &Normal", "Display the blocks at normal size", self.menu_zoom_normal),
##                           ("Zoom - &Bigger", "Display the blocks at a larger size", self.menu_zoom_bigger),
##                           ("Zoom - &Smaller", "Display the blocks at a smaller size", self.menu_zoom_smaller)),
#                           ),
#                          ("&Settings",

##                           ("*&Basic mode", "Basic level programming mode", self.menu_basic_mode),
##                           ("*&Advanced mode", "Advanced level programming mode", self.menu_adv_mode),
#                           ("+&Advanced mode", "Advanced level programming mode", self.menu_adv_mode),
#                           ("", "", ""),
##                           ("&USB Device", "Set the usb device for downloading", self.menu_usb_device),
##                           ("", "", ""),
#                           ("+&Display toolbar", "Display the toolbar under the menu", self.menu_enable_toolbar),

##                           ("", "", ""),
##                           ("+&Strict version check", "Make sure saved programs are readable by Bricworks",
##                            self.menu_strict_versions),
#                           ),


                          ("&Program Edison",
                           ("Program &Edison", "Program Edison",
                            self.menu_edison_program),
                           ("", "", ""),
                           ("&Check program size", "Report on the bytes and variables used in the program",
                            self.menu_check_program),

                           ("", "", ""),
                           ("&Download new firmware", "Download new firmware to Edison",
                            self.menu_edison_firmware),
                           ),
                          ("&Help",
                           ("&Help", "Display help for Edison EdWare", self.menu_help),
                           ("&About", "Display information about Edison EdWare", self.menu_about)))


        self.init_status_bar()
        self.init_menu()
        self.init_tool_bar()

        # Set the icon up
##        ib = wx.IconBundle()
##        ib.AddIconFromFile("bricworks.ico", wx.BITMAP_TYPE_ANY)
##        self.SetIcons(ib)


        # Not needed as pyInstaller sets up the icon
        # icon = wx.Icon("bricworks.ico", wx.BITMAP_TYPE_ICO)
        # if (sys.platform == 'darwin'):
        #     self.dockicon = wx.TaskBarIcon()
        #     self.dockicon.SetIcon(icon)
        # else:
        #     self.SetIcon(icon)



        # get data
        gui.device_data.load_devices()
        gui.bric_data.load_brics()
        gui.win_data.clear_pdata()

        self.splitters = []
        self.splitters.append(wx.SplitterWindow(self, -1, style= wx.SP_3D))                # between pallete and work
        self.splitters.append(wx.SplitterWindow(self.splitters[0], -1, style=wx.SP_3D))
        #self.splitters.append(wx.SplitterWindow(self.splitters[1], -1, style=wx.SP_3D))

        pp = gui.program_pallete.Program_pallete(self.splitters[0])       # pallete of brics
        #cp = gui.config_pallete.Config_pallete(self.splitters[0])         # pallete of components

        pwork = gui.program_work.Program_work(self.splitters[1], self)
        #cwork = gui.config_work.Config_work(self.splitters[2], self)

        #p21 = Top_right_panel(self.splitters[1])
        p22 = Bottom_right_panel(self.splitters[1])

        self.splitters[1].SplitHorizontally(pwork, p22, 120)
        self.splitters[0].SplitVertically(pp, self.splitters[1], 200)

        # Don't allow losing a window
        for s in self.splitters:
            s.SetMinimumPaneSize(20)
        self.splitters[1].SetSashGravity(1.0)

        # add in the LAST windows
        gui.win_data.register_window("splitter1", self.splitters[0])
        gui.win_data.register_window("splitter2", self.splitters[1])
        #gui.win_data.register_window("splitter3", self.splitters[2])
        gui.win_data.register_window("status", self.status_bar)
        gui.win_data.register_window("ppallete", pp)
        #gui.win_data.register_window("cpallete", cp)
        gui.win_data.register_window("pwork", pwork)
        #gui.win_data.register_window("cwork", cwork)
        gui.win_data.register_window("frame", self)

        # set up for program
        gui.win_data.verify_registry()

        gui.win_data.set_zoom(1.0)

        # get the last session and apply those values
        self.session_load()

        # Initialise status fields
        gui.win_data.status_file("")
        gui.win_data.status_space(0, 20)
        gui.win_data.status_info("Edison EdWare")


        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_IDLE, self.on_idle)

    def set_basic_mode(self):
        # basic mode
        #id = self.menu_bar.FindMenuItem("&File", "&New - Advanced")
        #self.menu_bar.FindItemById(id).Enable(False)
##        id = self.menu_bar.FindMenuItem("&Settings", "&USB Device")
##        self.menu_bar.FindItemById(id).Enable(False)
##        id = self.menu_bar.FindMenuItem("&Program Robot", "Program via &USB")
##        self.menu_bar.FindItemById(id).Enable(False)
##        id = self.menu_bar.FindMenuItem("&Program Robot", "&Download new firmware")
##        self.menu_bar.FindItemById(id).Enable(False)

        #id = self.menu_bar.FindMenuItem("&Settings", "&Advanced mode")
        #self.menu_bar.FindItemById(id).Check(False)

        gui.win_data.set_adv_mode(False)


    def set_initial_basic_modules(self):
        gui.win_data.config_clear()
        gui.win_data.config_add(0,"Line Tracker")
        gui.win_data.config_add(1, "Bump")
        gui.win_data.config_add(2, "LED")
        gui.win_data.config_add(3, "Motor A")
        gui.win_data.config_add(5, "IR Receiver")
        gui.win_data.config_add(6, "Sounder")
        gui.win_data.config_add(7, "IR Transmitter")
        gui.win_data.config_add(8, "Motor B")
        gui.win_data.config_add(10, "LED")
        gui.win_data.config_add(11, "Bump")

        gui.win_data.config_change_name(1, "RIGHT_BUMPER")
        gui.win_data.config_change_name(11, "LEFT_BUMPER")
        gui.win_data.config_change_name(2, "RIGHT_LED")
        gui.win_data.config_change_name(10, "LEFT_LED")

    def set_edison_modules(self):
        gui.win_data.set_edison_configuration()

    def set_adv_mode(self):
        # advanced mode
        id = self.menu_bar.FindMenuItem("&File", "&New - Advanced")
        self.menu_bar.FindItemById(id).Enable(True)
##        id = self.menu_bar.FindMenuItem("&Settings", "&USB Device")
##        self.menu_bar.FindItemById(id).Enable(True)
##        id = self.menu_bar.FindMenuItem("&Program Robot", "Program via &USB")
##        self.menu_bar.FindItemById(id).Enable(True)
##        id = self.menu_bar.FindMenuItem("&Program Robot", "&Download new firmware")
##        self.menu_bar.FindItemById(id).Enable(True)

        id = self.menu_bar.FindMenuItem("&Settings", "&Advanced mode")
        self.menu_bar.FindItemById(id).Check(True)

        gui.win_data.set_adv_mode(True)

        # refresh the programming pallete
        gui.win_data.force_redraw("ppallete")

    #def set_module_view(self):
        # Turn off the zooms
##        id = self.menu_bar.FindMenuItem("&View", "Zoom - &Normal")
##        self.menu_bar.FindItemById(id).Enable(False)
##        id = self.menu_bar.FindMenuItem("&View", "Zoom - &Bigger")
##        self.menu_bar.FindItemById(id).Enable(False)
##        id = self.menu_bar.FindMenuItem("&View", "Zoom - &Smaller")
##        self.menu_bar.FindItemById(id).Enable(False)
        #self.zoom_combo_box.Enable(False)

        #id = self.menu_bar.FindMenuItem("&View", "&Configuration view")
        #self.menu_bar.FindItemById(id).Check(True)
        #self.mode_combo_box.SetValue("Configuration")

#    def set_program_view(self):
        # Turn on the zooms
##        id = self.menu_bar.FindMenuItem("&View", "Zoom - &Normal")
##        self.menu_bar.FindItemById(id).Enable(True)
##        id = self.menu_bar.FindMenuItem("&View", "Zoom - &Bigger")
##        self.menu_bar.FindItemById(id).Enable(True)
##        id = self.menu_bar.FindMenuItem("&View", "Zoom - &Smaller")
##        self.menu_bar.FindItemById(id).Enable(True)
        #self.zoom_combo_box.Enable(True)

        # id = self.menu_bar.FindMenuItem("&View", "&Program view")
        # self.menu_bar.FindItemById(id).Check(True)
        # self.mode_combo_box.SetValue("Program")


    def session_load(self):
        global sdata
        global sdata_changed
        session_path = os.path.join(USER_DIR, SESSION_FILE_NAME)
        print "session_path:", session_path
        if (not os.path.isfile(session_path)):
            # if USER_DIR doesn't have a file, then try locally
            session_path = SESSION_FILE_NAME
        
        if (os.path.isfile(session_path)):
            try:
                # assume that we can read, if not then ignore reading the session data
                file_obj = file(session_path, 'r')
                test = cPickle.load(file_obj)
                file_obj.close()

                if (test.sdata_version == sdata.sdata_version):
                    sdata = test
                elif (test.sdata_version == 3):
                    sdata.convert_from_3(test)
                
            except Exception, e:
                pass

        #self.save_path = sdata.save_path
        #self.save_file = sdata.save_file

        # force strict checks
        sdata.strict_versions = True
        self.SetSize(sdata.win_size)
        if (sdata.win_pos):
            self.SetPosition(sdata.win_pos)

        for i in range(len(self.splitters)):
            self.splitters[i].SetSashPosition(sdata.sashes[i])

        # BED-EDISON remove the Advancedmode menu item
        if (sdata.edison_mode):
            self.set_basic_mode()
            #id = self.menu_bar.FindMenuItem("&Settings", "&Advanced mode")
            #self.menu_bar.FindItemById(id).Check(False)
            self.set_edison_modules()
        else:
            if (sdata.advanced_mode):
                self.set_adv_mode()
                #id = self.menu_bar.FindMenuItem("&Settings", "&Advanced mode")
                #self.menu_bar.FindItemById(id).Check(True)
            else:
                self.set_basic_mode()
                #id = self.menu_bar.FindMenuItem("&Settings", "&Advanced mode")
                #self.menu_bar.FindItemById(id).Check(False)
                self.set_initial_basic_modules()

        #id = self.menu_bar.FindMenuItem("&Settings", "&Display toolbar")
        #if (sdata.toolbar):
        #    self.menu_bar.FindItemById(id).Check(True)
        #else:
        #    self.menu_bar.FindItemById(id).Check(False)

##        id = self.menu_bar.FindMenuItem("&Settings", "&Strict version check")
##        if (sdata.strict_versions):
##            self.menu_bar.FindItemById(id).Check(True)
##        else:
##            self.menu_bar.FindItemById(id).Check(False)

        # if (sdata.main_window == 'program'):
        #     self.set_program_view()
        #     gui.win_data.switch_to_program()
        # else:
        #     self.set_module_view()
        #     gui.win_data.switch_to_config()

        self.change_dirty(False)
        sdata_changed = False


    def session_save(self):
        global sdata_changed
        cdata = Session_data()
        cdata.win_size = self.GetSize()
        cdata.win_pos = self.GetPosition()

        for i in range(len(self.splitters)):
            cdata.sashes[i] = self.splitters[i].GetSashPosition()

        #cdata.save_path = self.save_path
        #cdata.save_file = self.save_file
        cdata.main_window = gui.win_data.get_main_window_type()
        cdata.advanced_mode = gui.win_data.get_adv_mode()
        cdata.usb_device = sdata.usb_device
        cdata.strict_versions = sdata.strict_versions

        #id = self.menu_bar.FindMenuItem("&Settings", "&Display toolbar")
        #if (self.menu_bar.FindItemById(id).IsChecked()):
        #    cdata.toolbar = True
        #else:
        cdata.toolbar = True

        if (sdata_changed or (cdata != sdata)):
            #print "Session data changed"

            # Try two locations to write the file. Try to do it in a platform
            # agnostic way.
            goodFileObj = False
            
            # First in the session directory
            session_path = os.path.join(USER_DIR, SESSION_FILE_NAME)
            try:
                file_obj = file(session_path, 'w')
                goodFileObj = True
            except Exception:
                pass

            # else in the current directory
            if (not goodFileObj):
                try:
                    file_obj = file(SESSION_FILE_NAME, 'w')
                    goodFileObj = True
                except Exception:
                    pass

            if (goodFileObj):
                cPickle.dump(cdata, file_obj, 0)
                file_obj.close()

        sdata_changed = False

    def on_move(self, event):
        self.on_size(event)

    def on_size(self, event):
        # send the new size to the program pallete
        size = self.GetClientSize()
        upper_left = self.GetClientAreaOrigin()
        #print size, upper_left, self.ClientToScreen(upper_left), self.GetClientRect()
        upper_left = self.ClientToScreen(upper_left)
        rect = wx.Rect(upper_left[0], upper_left[1], size[0], size[1])
        #print rect
        gui.win_data.inform_pallete_of_frame_rect(rect)

        event.Skip()

    def on_idle(self, event):
        # check to see if all splitters are correct yet
        if (not self.splitter_done and self.splitter_attempts < 20):
            self.splitter_attempts += 1
            self.splitter_done = True
            for i in range(len(self.splitters)):
                if (sdata.sashes[i] != self.splitters[i].GetSashPosition()):
                    #print "on_idle(): Positioning splitter", i
                    self.splitters[i].SetSashPosition(sdata.sashes[i])
                    event.RequestMore()

                    # negative values get read as positive ones, so on a negative
                    # we have to hope for the best
                    if (sdata.sashes[i] > 0):
                        self.splitter_done = False


    def inform_work_rect(self, rect):
        gui.win_data.inform_pallete_of_work_rect(rect)

    def init_status_bar(self):
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetFieldsCount(3)
        self.status_bar.SetStatusWidths([-2,-1,-1])

    def init_menu(self):
        self.menu_bar = wx.MenuBar()
        for md in self.menu_data:
            menu_label = md[0]
            menu_items = md[1:]
            self.menu_bar.Append(self.init_menu_items(menu_items), menu_label)
        self.SetMenuBar(self.menu_bar)

        self.change_dirty(False)


    def change_dirty(self, dirty):
        "Modify the menu items that change with dirty/not dirty"
        save_id = self.menu_bar.FindMenuItem("&File", "&Save")
        self.menu_bar.FindItemById(save_id).Enable(dirty)
        if (not dirty):
            gui.win_data.update_dirty(False)


    def init_menu_items(self, items):
        menu = wx.Menu()
        for label,status,handler in items:
            if (not label):
                menu.AppendSeparator()
            else:
                if (label.startswith('*')):
                    menu_item = menu.AppendRadioItem(-1, label[1:], status)
                elif (label.startswith('+')):
                    menu_item = menu.AppendCheckItem(-1, label[1:], status)
                else:
                    if (label == "&About"):
                        id = wx.ID_ABOUT
                    elif (label == "&Exit"):
                        id = wx.ID_EXIT
                    else:
                        id = -1
                    menu_item = menu.Append(id, label, status)

                self.Bind(wx.EVT_MENU, handler, menu_item)

        return menu


    def init_tool_bar(self):
        self.tool_bar = self.CreateToolBar()
        id = wx.NewId()
        #self.mode_combo_box = wx.ComboBox(self.tool_bar, id, "Program", choices = ["Configuration", "Program"],
        #                                  size=(180, -1))

        #self.tool_bar.AddControl(wx.StaticText(self.tool_bar, -1, " View "))
        #self.tool_bar.AddControl(self.mode_combo_box)
        #self.Bind(wx.EVT_COMBOBOX, self.on_change_mode, id=id)
        #self.tool_bar.AddSeparator()

        self.zoom_id = wx.NewId()
        self.zoom_combo_box = wx.ComboBox(self.tool_bar, self.zoom_id, "100%",
                                          choices = ["50%", "60%", "70%", "80%", "90%",
                                                     "100%", "120%", "150%"], size=(100, -1))
        self.tool_bar.AddControl(wx.StaticText(self.tool_bar, -1, " Zoom "))
        self.tool_bar.AddControl(self.zoom_combo_box)
        self.Bind(wx.EVT_COMBOBOX, self.on_change_zoom, id=self.zoom_id)

        self.tool_bar.AddSeparator()
        self.add_var_id = wx.NewId()
        self.add_var_button = wx.Button(self.tool_bar, self.add_var_id, "Add Variable", size=(120,-1))
        self.tool_bar.AddControl(self.add_var_button)
        self.Bind(wx.EVT_BUTTON, self.on_add_variable, id=self.add_var_id)

        self.tool_bar.AddSeparator()
        self.add_prog_id = wx.NewId()
        self.add_prog_button = wx.Button(self.tool_bar, self.add_prog_id, "Program Edison", size=(140,-1))
        self.tool_bar.AddControl(self.add_prog_button)
        self.Bind(wx.EVT_BUTTON, self.on_program_button, id=self.add_prog_id)



        self.tool_bar.Realize()
        # start it on
        self.tool_bar.Show()

        #id = self.menu_bar.FindMenuItem("&Settings", "Display toolbar")
        #self.menu_bar.FindItemById(id).Check(True)

    def on_change_mode(self, event):
        new_mode = event.GetString().lower()
        if (new_mode == "program"):
            id = self.menu_bar.FindMenuItem("&View", "&Program view")
            self.menu_bar.FindItemById(id).Check(True)
            self.menu_program(event)
        elif (new_mode == "configuration"):
            id = self.menu_bar.FindMenuItem("&View", "&Configuration view")
            self.menu_bar.FindItemById(id).Check(True)
            self.menu_config(event)

    def on_change_zoom(self, event):
        new_zoom = event.GetString()
        zoom = float(new_zoom[:-1])/100
        gui.win_data.set_zoom(zoom)

    def on_add_variable(self, event):
        gui.win_data.add_variable()

    def on_program_button(self, event):
        gui.win_data.selection_drop_all()
        dialog = gui.downloader.audio_downloader("", "Download over audio")
        result = dialog.ShowModal()
        dialog.Destroy()

    def menu_edison_program(self, event):
        gui.win_data.selection_drop_all()
        dialog = gui.downloader.audio_downloader("", "Download over audio")
        result = dialog.ShowModal()
        dialog.Destroy()

    def menu_edison_firmware(self, event):
        gui.win_data.selection_drop_all()
        dialog = gui.downloader.audio_firmware_downloader("", "Download new FIRMWARE over audio")
        result = dialog.ShowModal()
        dialog.Destroy()

    def menu_new_edison(self, event):
        gui.win_data.selection_drop_all()
        if (self.handle_unsaved_changes("Unsaved program.")):
            gui.win_data.clear_pdata()
            self.set_basic_mode()
            self.set_edison_modules()
            self.change_dirty(False)
            self.save_file = ""
            gui.win_data.status_file(self.save_file)
            gui.win_data.make_var_and_config_update()
            self.Refresh()

    def menu_open(self, event):
        gui.win_data.selection_drop_all()
        if (not self.handle_unsaved_changes("Unsaved program.")):
            return
        gui.win_data.clear_pdata()
        load_path = wx.FileSelector("Open program", default_path=self.save_path,
                                    wildcard="EdWare files (*.edw)|*.edw|All files (*.*)|*.*",
                                    flags=wx.OPEN)

        if (load_path):
            self.load_existing_path(load_path)


    def load_existing_path(self, load_path):
        gui.win_data.selection_drop_all()
        #print "Load_path", load_path
        if (not os.path.isfile(load_path)):

            wx.MessageBox("Can't open the file: %s" % (load_path,),
                          "Error while opening program.", wx.OK | wx.ICON_ERROR)
        else:
            gui.win_data.clear_pdata()
            (path, ext) = os.path.splitext(load_path)
            try:
                fh = file(load_path, 'rb')
                # if older 'mbw' file then use python un-pickling, else use JSON
                if (ext.lower() == ".mbw"):
                    gui.win_data.load(fh, sdata.strict_versions)
                else:
                    # expect all other files will be JSON
                    gui.win_data.loadEdisonAsJson(fh, sdata.strict_versions)
                fh.close()

                # remember the path and file -- change to .edw if not already
                if (ext.lower() != ".edw"):
                    load_path = path + ".edw"
                self.save_path, self.save_file = os.path.split(load_path)
                gui.win_data.status_file(self.save_file)

                if (gui.win_data.get_adv_mode()):
                    self.set_adv_mode()
                else:
                    self.set_basic_mode()
                self.change_dirty(False)

            except Exception, e:
                #print "Exception:", e
                raise e
                wx.MessageBox("Error opening the program. Maybe the disk vanished?",
                              "Error while opening program.", wx.OK | wx.ICON_ERROR)

            gui.win_data.make_var_and_config_update()
            self.Refresh()

    def menu_save(self, event):
        gui.win_data.selection_drop_all()
        if (gui.win_data.is_data_dirty()):
            if (self.save_file):
                gui.win_data.status_file(self.save_file)
                self.program_save(self.save_path, self.save_file)
            else:
                self.menu_saveas(event)

    def menu_saveas(self, event):
        gui.win_data.selection_drop_all()
        save_path = self.offer_save(self.save_path, self.save_file)
        #print "Save_path", save_path
        if (save_path):
            # save the new file name
            self.save_path, self.save_file = os.path.split(save_path)
            gui.win_data.status_file(self.save_file)
            self.program_save(self.save_path, self.save_file)

    def menu_exit(self, event):
        gui.win_data.selection_drop_all()
        if (self.handle_unsaved_changes("Exiting with a modified program.")):
            self.change_dirty(False)
            self.Close()

    def on_close(self, event):
        gui.win_data.selection_drop_all()
        if (self.handle_unsaved_changes("Exiting with a modified program.")):
            self.session_save()
            self.Destroy()

    def handle_unsaved_changes(self, title):
        if (gui.win_data.is_data_dirty()):

            result = wx.MessageBox("Your program has changes that have not been saved.\n\n" +\
                                   "Would you like to save the changes first?",
                                   title,
                                   wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT | wx.ICON_QUESTION)
            if (result == wx.YES):
                if (self.save_file):
                    self.program_save(self.save_path, self.save_file)
                else:
                    saved_path = self.offer_save(self.save_path, self.save_file)
                    if (saved_path):
                        # save the new file name
                        self.save_path, self.save_file = os.path.split(saved_path)
                        gui.win_data.status_file(self.save_file)
                        self.program_save(self.save_path, self.save_file)
                    else:
                        # abort the exit
                        return False

            elif (result == wx.CANCEL):
                return False

        return True


    def offer_save(self, path, filename):
        save_path = wx.FileSelector("Save program", default_path=path, default_filename=filename,
                                    flags=wx.SAVE|wx.OVERWRITE_PROMPT)
        if (save_path and not os.path.isfile(save_path) and os.path.splitext(save_path)[1] == ""):
            save_path += ".edw"
        return save_path

    def program_save(self, path, filename):
        try:
            # Edison has gone to a JSON format!
            if (sdata.edison_mode):
                fh = file(os.path.join(path, filename), 'wb')
                gui.win_data.saveEdisonAsJson(fh)
                fh.close()
            else:
                fh = file(os.path.join(path, filename), 'wb')
                gui.win_data.save(fh)
                fh.close()

        except Exception,e:
            extraInfo = "Exception:%s, python ver:%s" % (e, sys.version)
            wx.MessageBox("Error saving the program. Maybe the disk is full?\n(%s)" % (extraInfo),
                          "Error while saving.", wx.OK | wx.ICON_ERROR)

    def menu_usb_device(self, event):
        global sdata_changed
        device_name = sdata.usb_device
        device_name = wx.GetTextFromUser("Please enter the USB device for programming the robot",
                                         "USB Device", default_value = device_name,
                                        parent=self)
        if (len(device_name) > 0 and (not device_name == sdata.usb_device)):
            sdata.usb_device = device_name
            sdata_changed = True

    def menu_check_program(self, event):
        gui.win_data.selection_drop_all()
        gui.downloader.check_size()

    def menu_screen_program(self, event):
        gui.win_data.selection_drop_all()
        dialog = gui.downloader.screen_downloader("", "Download via Screen")
        result = dialog.ShowModal()
        #print result
        dialog.Destroy()

    def menu_cable_program(self, event):
        global sdata_changed
        gui.win_data.selection_drop_all()
        dialog = gui.downloader.usb_downloader(sdata.usb_device, "", "Download via USB")
        result = dialog.ShowModal()
        used_device = dialog.get_port()
        dialog.Destroy()

        if (len(used_device) > 0 and (not used_device == sdata.usb_device)):
            sdata.usb_device = used_device
            sdata_changed = True

    def menu_firmware(self, event):
        global sdata_changed
        gui.win_data.selection_drop_all()
        dialog = gui.downloader.firmware_downloader(sdata.usb_device, "", "Download new FIRMWARE via USB")
        result = dialog.ShowModal()
        used_device = dialog.get_port()
        dialog.Destroy()

        if (len(used_device) > 0 and (not used_device == sdata.usb_device)):
            sdata.usb_device = used_device
            sdata_changed = True

    def menu_hex_download(self, event):
        global sdata_changed
        gui.win_data.selection_drop_all()
        dialog = gui.downloader.hex_downloader(sdata.usb_device, "", "Download Intel hex file via USB")
        result = dialog.ShowModal()
        used_device = dialog.get_port()
        dialog.Destroy()

        if (len(used_device) > 0 and (not used_device == sdata.usb_device)):
            sdata.usb_device = used_device
            sdata_changed = True

    # def menu_config(self, event):
    #     gui.win_data.selection_drop_all()
    #     gui.win_data.switch_to_config()
    #     self.mode_combo_box.SetSelection(0)
    #     self.set_module_view()

    # def menu_program(self, event):
    #     gui.win_data.selection_drop_all()
    #     gui.win_data.switch_to_program()
    #     self.mode_combo_box.SetSelection(1)
    #     self.set_program_view()

    def menu_zoom_normal(self, event):
        gui.win_data.adjust_zoom(0)

    def menu_zoom_bigger(self, event):
        gui.win_data.adjust_zoom(1)

    def menu_zoom_smaller(self, event):
        gui.win_data.adjust_zoom(-1)

    def menu_basic_mode(self, event):
        self.set_basic_mode()

    # def menu_adv_mode(self, event):
    #     # Are we already advanced
    #     if (gui.win_data.get_adv_mode()):
    #         wx.MessageBox("To go back to basic (factory) mode, you must use 'New - Basic'.",
    #                       "Back to Basics.", wx.OK | wx.ICON_WARNING)

    #         id = self.menu_bar.FindMenuItem("&Settings", "&Advanced mode")
    #         self.menu_bar.FindItemById(id).Check(True)

    #     else:
    #         self.set_adv_mode()



    def menu_help(self, event):
        dlg = gui.about.SimpleHelpBox(self)
        dlg.ShowModal()
        dlg.Destroy()

    def menu_about(self, event):
        # BED debug
        #gui.win_data.program().dump()

        dlg = gui.about.AboutBox(self)
        dlg.ShowModal()
        dlg.Destroy()

    def menu_enable_toolbar(self, event):
        id = self.menu_bar.FindMenuItem("&Settings", "&Display toolbar")
        if (self.menu_bar.FindItemById(id).IsChecked()):
            self.tool_bar.Show()
        else:
            self.tool_bar.Hide()

        self.Fit()
        self.Refresh()

    def menu_strict_versions(self, event):
        global sdata_changed
        id = self.menu_bar.FindMenuItem("&Settings", "&Strict version check")
        if (self.menu_bar.FindItemById(id).IsChecked()):
            sdata.strict_versions = True
        else:
            sdata.strict_versions = False
        sdata_changed = True



class Top_right_panel(wx.Panel):
    def __init__(self, parent, size=(600, 100)):
        wx.Panel.__init__(self, parent)

        p11 = gui.config_win.Config_win(self)
        p12 = gui.var_win.Var_win(self)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(p11, 1, wx.EXPAND)
        box.Add(p12, 1, wx.EXPAND)
        self.SetSizer(box)

        gui.win_data.register_window("config", p11)
        gui.win_data.register_window("var", p12)

    def toggle_config_win_text(self):
        self.p11.toggle_wins()



class Bottom_right_panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        detail = gui.detail_win.Detail_win(self)
        help = gui.help_win.Help_win(self)
        vars = gui.var_win.Var_win(self)

        self.lower_box = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_box.Add(detail, 4, wx.EXPAND)
        self.lower_box.Add(help, 3, wx.EXPAND)
        self.lower_box.Add(vars, 2, wx.EXPAND)
        self.SetSizer(self.lower_box)

        gui.win_data.register_window("detail", detail)
        gui.win_data.register_window("help", help)
        gui.win_data.register_window("var", vars)



#----------------------------------------------------------------------

def main(file_path=None):
    app = wx.PySimpleApp()
    frame = Bricworks_frame(None)
    frame.Show(True)
    frame.Update()


    if (file_path):
        frame.load_existing_path(file_path)

    app.MainLoop()

#----------------------------------------------------------------------

class BricworksApp(wx.App):
    def OnInit(self):
        self.frame = Bricworks_frame(None)
        self.SetTopWindow(self.frame)
        self.frame.Show(True)
        self.frame.Update()
        return True

    def load(self, file_path):
        #print "Loading", file_path
        self.frame.load_existing_path(file_path)
        self.frame.Update()

def main2(file_path=None):
    app = BricworksApp(False)
    if (file_path):
        app.load(file_path)
    app.MainLoop()


if __name__ == '__main__':
    file_path = None
    if (len(sys.argv) > 1):
        file_path = sys.argv[1]

    # find the session writing error
    path = '~'
    new_path = os.path.expanduser(path)
    if (new_path == path):
        # didn't work, will have to just try to use the current directory
        USER_DIR = '.'
    else:
        USER_DIR = new_path
        
    print "USER_DIR:", USER_DIR
    
    main2(file_path)
