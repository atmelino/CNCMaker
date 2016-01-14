#!/usr/bin/python

"""
Mill out a hold down. General plan is something like this:
 _______
|_______|
|_______|
|_______|
|       |
|   _   |
|  | |  |
|  | |  |
|  | |  |
|  |_|  |
|       |
|       |
|_______|
 _______
|       |
|_______|

with the top being a bit of a ramp/step thing, the bottom being square
and another block to put under it so that the hold down is level and
clamps firmly.
"""

# dirty!
import sys
sys.path.insert(0, '..')

import cnc
cnc.init()

# I think my "runout" was actually due to not bolting the rotary tool
# in hard enough...
runout = 0.0 # mm
cnc.tool_width = 3.175 + runout
cnc.step_over = cnc.tool_width / 2
cnc.step_down = cnc.tool_width / 2

# make tabs fairly chunky
cnc.tab_width = 5.000
cnc.tab_height = cnc.tool_width

material_height = 10.000 # mm
recess_depth = material_height - 7.5

cnc.comment("milling bottom block")
cnc.rectangle((5,5), (30, 15), depth=material_height, offset="outside", tab=True)

cnc.comment("milling central recess")
cnc.fillrectangle((10, 30), (25, 95), depth=recess_depth, offset="inside")

cnc.comment("milling central slot")
cnc.rectangle((14.75, 35), (20.25, 90), start_depth=recess_depth, depth=material_height, offset="inside")

cnc.comment("front slope")
# mill slightly outside the edges, so that we don't get rounded corners
cnc.fillrectangle((2.5, 105), (32.5, 110), depth=2.5, offset="inside")
cnc.fillrectangle((2.5, 110), (32.5, 115), depth=5.0, offset="inside")
cnc.fillrectangle((2.5, 115), (32.5, 120), depth=7.5, offset="inside")

cnc.comment("cut out around hold down")
cnc.rectangle((5, 25), (30, 120), depth=material_height, offset="outside", tab=True)

cnc.comment("back to zero")
cnc.rapidmove((0, 0))

