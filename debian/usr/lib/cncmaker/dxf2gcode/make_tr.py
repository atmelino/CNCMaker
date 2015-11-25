#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Generates the tr file based on the defined PyQt Project File
"""

import os, sys
import subprocess

PYTHONPATH = os.path.split(sys.executable)[0]
PLYPATH = os.path.join(PYTHONPATH, "Lib\\site-packages\\PyQt4\\pylupdate4.exe")
LREPATH = os.path.join(PYTHONPATH, "Lib\\site-packages\\PyQt4\\lrelease.exe")

FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

FILES = ("..\\core\\arcgeo.py",
         "..\\core\\project.py",
         "..\\core\\shape.py",
         "..\\dxfimport\\geoent_arc.py",
         "..\\dxfimport\\geoent_circle.py",
         "..\\dxfimport\\geoent_line.py",
         "..\\dxfimport\\importer.py",
         "..\\globals\\config.py",
         "..\\gui\\canvas.py",
         "..\\gui\\canvas2d.py",
         "..\\gui\\canvas3d.py",
         "..\\gui\\messagebox.py",
         "..\\gui\\popupdialog.py",
         "..\\gui\\treehandling.py",
         "..\\postpro\\postprocessor.py",
         "..\\postpro\\postprocessorconfig.py",
         "..\\postpro\\tspoptimisation.py",
         "..\\dxf2gcode.py",
         "..\\dxf2gcode.ui"
         )


TSFILES = ("dxf2gcode_de_DE.ts",
           "dxf2gcode_fr.ts",
           "dxf2gcode_ru.ts")

FILESSTR = ""
for FILE in FILES:
    FILESSTR += ("%s\\i18n\\%s " % (FILEPATH, FILE))

TSFILESTR = ""
for TSFILE in TSFILES:
    TSFILESTR += ("%s\\i18n\\%s " % (FILEPATH, TSFILE))

OPTIONS = "-ts"

cmd1 = ("%s %s %s %s\n" % (PLYPATH, FILESSTR, OPTIONS, TSFILESTR))
print(cmd1)
print(subprocess.call(cmd1, shell=True))

cmd2 = ("%s %s\n" % (LREPATH, TSFILESTR))
print(cmd2)
print(subprocess.call(cmd2, shell=True))

print("\nREADY")

