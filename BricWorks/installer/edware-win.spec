# -*- mode: python -*-
a = Analysis(['edware.py'],
             pathex=['C:\\Documents and Settings\\Brian\\My Documents\\EdWare\\EdWare'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)

bric_tree = Tree("gui/brics", "gui/brics")
device_tree = Tree("gui/devices", "gui/devices")
doc_tree = Tree("docs", "docs")
other_files = [("Click.wav", "Click.wav", "DATA"),
               ("README.txt", "README.txt", "DATA"),
               ("tass.py", "tass.py", "DATA")
               ]

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='edware.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='edware.ico')
coll = COLLECT(exe,
               a.binaries,
               bric_tree, device_tree, doc_tree, other_files,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='edware')
