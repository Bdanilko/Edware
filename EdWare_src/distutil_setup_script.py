import os
import site
import sys
from cx_Freeze import setup, Executable

## Get the site-package folder, not everybody will install
## Python into C:\PythonXX
site_dir = site.getsitepackages()[1]
include_dll_path = os.path.join(site_dir, "wx-3.0-msw", "wx")

## Collect the list of missing dll when cx_freeze builds the app
missing_dll = ["freetype6.dll",
               "gdiplus.dll",
               "libcairo-2.dll",
               "libcairo-gobject-2.dll",
               "libcairo-script-interpreter-2.dll",
               "libexpat-1.dll",
               "libfontconfig-1.dll",
               "libpng14-14.dll",
               "wxbase30u_net_vc90.dll",
               "wxbase30u_vc90.dll",
               "wxbase30u_xml_vc90.dll",
               "wxmsw30u_adv_vc90.dll",
               "wxmsw30u_aui_vc90.dll",
               "wxmsw30u_core_vc90.dll",
               "wxmsw30u_gl_vc90.dll",
               "wxmsw30u_html_vc90.dll",
               "wxmsw30u_media_vc90.dll",
               "wxmsw30u_propgrid_vc90.dll",
               "wxmsw30u_qa_vc90.dll",
               "wxmsw30u_ribbon_vc90.dll",
               "wxmsw30u_richtext_vc90.dll",
               "wxmsw30u_stc_vc90.dll",
               "wxmsw30u_webview_vc90.dll",
               "wxmsw30u_xrc_vc90.dll",
               "zlib1.dll"]

required_files = ["Click.wav",
                  "edware.icns",
                  "edware.ico",
                  "mbw.ico",
                  ]
   
## We also need to add the glade folder, cx_freeze will walk
## into it and copy all the necessary files
resource_dirs = ["gui\\brics",
                 "gui\\devices",
                 "docs"]

## Create the list of includes as cx_freeze likes
include_files = []
for dll in missing_dll:
    include_files.append((os.path.join(include_dll_path, dll), dll))

## Let's add resource dirs
for resource_dir in resource_dirs:
    include_files.append((resource_dir, resource_dir))

## Append required files
for required_file in required_files:
    include_files.append(required_file)

base = None

## Lets not open the console while running the app
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("edware.py",
                          base=base,
                          icon="edware.ico"),
               Executable("tass.py",
                          base=None),
               Executable("audio_creator.py",
                          base=None),
               Executable("audio_test.py",
                          base=None),
               Executable("newversion.py",
                          base=None)]

buildOptions = {"compressed": False,
                "includes": ["wx"],
                "packages": ["wx"],
                "excludes": ["Tkinter", "ttk", "bz2"],
                "include_files": include_files}

setup(name="Edware",
      version="1.0",
      description="Edware.",
      options={"build_exe": buildOptions},
      executables=executables)
