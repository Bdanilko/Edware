# -*- mode: python -*-
a = Analysis(['edware.py'],
             pathex=['C:\\Users\\User\\Documents\\edware_1.0.7'],
             hiddenimports=[],
             hookspath=None,
             excludes=["tcl", "tk", "tkinter", "_tkinter", "Tkinter", "FixTk"],
             runtime_hooks=None)
pyz = PYZ(a.pure)

bric_tree = Tree("gui/brics", "gui/brics")
device_tree = Tree("gui/devices", "gui/devices")
doc_tree = Tree("docs", "docs")
prog_tree = Tree("My Programs", "My Programs")
# waver_tree = Tree("waver", "waver")
other_files = [("Click.wav", "Click.wav", "DATA"),
               ("tass.py", "tass.py", "DATA")
               ]

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='edware.exe',
          debug=False,
          strip=None,
          upx=False,
          console=False, icon='edware.ico')
coll = COLLECT(exe,
               a.binaries,
               bric_tree, device_tree, doc_tree, prog_tree, other_files,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=False,
               name='edware')
