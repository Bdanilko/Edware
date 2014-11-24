# * **************************************************************** **
#
# File: about.py
# Desc: Display a simple 'about' box
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
# Svn: $Id: about.py 50 2006-12-02 01:10:37Z briand $
# * **************************************************************** */


import wx
import wx.html

class AboutBox(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "About Edison EdWare", size=(600,500))
        self.html_text = '''
        <html>
        <body>
        <center>
        <h1>Edison EdWare</h1>
        <h2>Version 0.8.3</h2>
        Programming your Edison Robot<br>
        http://www.microbric.com/
        </center>
        <p>
        <font size="-2">
        Copyright 2006,2014 Microbric Pty Ltd<br>
        This program is distributed under the terms of the Gnu General Public License, version 2
        (for the full text, see gpl.txt in the docs directory)
        </font>
        <p>
        
        <font size="1">
        Author: Brian Danilko, <b>Likeable Software</b> (http://www.likeablesoftware.com)
        </font>
        </p>
        
        <p>
        <font size="1">
        Made possible by awesome robot firmware by: Bill Hammond, <b>Circuitworks</b> (http://www.circuitworks.com.au)
        </font>
        </p>
        
        <p>
        <font size="-2">
        This program, and previous versions, were developed using the following open-source components:
        <ul>
        <li><b>Python</b> (http://www.python.org)
        <li><b>wxPython</b> (http://www.wxpython.org)
        <li><b>pyWin32</b> (http://pywin32.sourceforge.net)
        <li><b>Inno Setup</b> (http://www.jrsoftware.org)
        <li><b>pyInstaller</b> (http://www.pyinstaller.org)
        <li>----------- previous version components ----------------
        <li><b>pySerial</b> (http://pyserial.sourceforge.net)
        <li><b>comscan.py</b> from bitpim (http://www.bitpim.org)
        </font>
        </ul>
        
        </body>
        </html>
        '''

        html = wx.html.HtmlWindow(self)
        html.SetPage(self.html_text)
        button = wx.Button(self, wx.ID_OK, "Okay")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(button, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()
        

import webbrowser

class SimpleHelpBox(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Edison EdWare Help", size=(600,300))
        self.help_text = '''
        <html>
        <body>
        <center>
        <h1>Edison EdWare Help</h1>

        </body>
        </html>
        '''

        # <h4>
        # Help is available at the Microbric web site at:<br>
        # http://www.i-bot.com.au/ai2/sitefiles/File/BricWorkshelp.pdf
        # </h4>

        # <p>
        # <font size="2">
        # You can either download it and display it in your favourite pdf viewer or
        # you can open it with your browser.
        # </font>
        # </p>

        html = wx.html.HtmlWindow(self)
        html.SetPage(self.help_text)
        cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        #open_button = wx.Button(self, wx.ID_OK, "Open in browser")
        
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(cancel, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        #hsizer.Add((10, -1))
        #hsizer.Add(open_button, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(hsizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()
        
        #self.Bind(wx.EVT_BUTTON, self.on_open_clicked, open_button)


    def on_open_clicked(self, event):
        webbrowser.open(url="http://www.i-bot.com.au/ai2/sitefiles/File/BricWorkshelp.pdf", new=True, autoraise=True)
        self.EndModal(wx.ID_OK)

