#!/usr/bin/python

"""
A circle.
"""

# dirty!
import sys
sys.path.insert(0, '..')

import cnc
cnc.init()

cnc.tool_width = 3.175
cnc.step_over = cnc.tool_width / 2
cnc.step_down = 1.0 # cnc.tool_width / 2
cnc.tab_width = 5.000
cnc.tab_height = cnc.tool_width

material_height = 10.000 # mm
recess_depth = material_height - 7.5

cnc.circle((25, 25), 20.0, depth=material_height, tab=True)

cnc.fillcircle((70, 25), 20.0, depth=material_height)

cnc.fillcircle((70, 25), 20.0, depth=material_height, depth_first=False)

