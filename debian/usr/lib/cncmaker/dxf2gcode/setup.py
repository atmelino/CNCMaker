#!/usr/bin/python
# run: python setup.py build

import sys, os
import shutil
from cx_Freeze import setup, Executable


version = "4.10.2015"

base = 'Console'
if sys.platform == 'win32':
    base = 'Win32GUI'  # Tells the build script to hide the console.

# script based on
# https://github.com/Fireforge/PySide-OpenGL-cx_Freeze-Example
# http://stackoverflow.com/questions/15486292/cx-freeze-doesnt-find-all-dependencies
def include_OpenGL():
    PYTHONPATH = os.path.split(sys.executable)[0]
    path_base = os.path.join(PYTHONPATH, "Lib\\site-packages\\OpenGL")
    skip_count = len(path_base)
    zip_includes = [(path_base, "OpenGL")]
    for root, sub_folders, files in os.walk(path_base):
        for file_in_root in files:
            zip_includes.append(
                ("{}".format(os.path.join(root, file_in_root)),
                 "{}".format(os.path.join("OpenGL", root[skip_count + 1:], file_in_root))
                 )
            )
    return zip_includes

# Remove the existing folders
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)

options = {
    'build_exe': {
        # 'packages': '' ,
        # 'includes': '',
        # 'excludes': '',
        'zip_includes': include_OpenGL(),
        'silent': True
    }
}

executables = [
    Executable(script='dxf2gcode.py',
               base=base,
               icon="images\\DXF2GCODE-001.ico",
               appendScriptToExe=True,
               appendScriptToLibrary=False,
               targetName="dxf2gcode.exe"
               )
]

setup(name='DXF2GCODE',
      version=version,
      description='Converting 2D drawings to CNC machine compatible G-Code.',
      options=options,
      executables=executables
      )
