#!/usr/bin/python

"""
Generates the python file based on the defined uifile
"""

import os
import sys
import subprocess
import tempfile

from globals.six import PY2
import globals.constants as c
if c.PYQT5notPYQT4:
    pyQtVer = '5'
else:
    pyQtVer = '4'

PYTHONPATH = os.path.split(sys.executable)[0]
UICPATH = os.path.join(PYTHONPATH, "Lib\\site-packages\\PyQt" + pyQtVer)
FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

UIFILE = "dxf2gcode.ui"
PYFILEver = "dxf2gcode_ui%s.py" % pyQtVer

RCFILE = "dxf2gcode_images.qrc"
RCFILEver = "dxf2gcode_images%s.qrc" % pyQtVer

RCPYFILEver = "dxf2gcode_images%s_rc.py" % pyQtVer

ui_data = ""
with open(UIFILE, "r") as myfile:
    ui_data = myfile.read().replace(RCFILE, RCFILEver)

fd, tmp_ui_filename = tempfile.mkstemp()
try:
    if PY2:
        os.write(fd, ui_data)
    else:  # Python3
        os.write(fd, bytes(ui_data, 'UTF-8'))
    os.close(fd)

    OPTIONS = "-o"

    cmd1 = "%s\\pyuic%s.bat %s %s %s" % (UICPATH, pyQtVer, tmp_ui_filename, OPTIONS, PYFILEver)
    cmd2 = "%s\\pyrcc%s.exe %s %s %s" % (UICPATH, pyQtVer, OPTIONS, RCPYFILEver, RCFILE)

    print(cmd1)
    print(subprocess.call(cmd1))

    print(cmd2)
    print(subprocess.call(cmd2))

finally:
    os.remove(tmp_ui_filename)

print("\n!!!!!!!Do not commit the updated ...rc.py files to the repository if the .qrc files did not change,\n"
      " i.e. if you did not make any changes with relation to the images\n"
      " - the updated .pys are not important especially with PyQt5; it makes too many unnecessary changes!!!!!!")
print("\nREADY")
