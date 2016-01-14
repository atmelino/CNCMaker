#!/usr/bin/env python

"""Program to calculate the depths of a parabola,
so we can mill one out and maybe vacuum form it."""

# dirty!
import sys
sys.path.insert(0, '..')

diameter = 130
depth = 18

# focus measured from bottom of parabola
focus = diameter ** 2 / (depth * 16)

mill_diam = 3
radii = range(0, diameter / 2, mill_diam)

print "; diameter, depth:", diameter, depth
print "; focal length:", focus
print "; radii:", radii


# Formula: y == x ** 2 / 4a
# x = radius, y = depth
# a = (x ** 2) / 4y
a_const = (float(diameter / 2) ** 2) / (4 * depth)
print "; a_const:", a_const


depths = []
print "; depths (0 is centre):"
for r in radii:
    each_depth = (r ** 2) / (4 * a_const) - depth
    depths.append((r, each_depth))
    print ";     %d\t%0.2f" % (r, each_depth)

print ";", depths



import cnc

cnc.tool_width = 3.175
cnc.step_over = cnc.tool_width / 2
cnc.step_down = 1.0
cnc.safe_height = 5.00

cnc.init()

# start with a drill to depth at 0,0
# bad plan - this made a fair bit of smoke
#cnc.drill((0, 0), abs(depths[0][1]))

for r, each_depth in depths[1:]:
    cnc.circle((0,0), r, abs(each_depth))


print "; finishing pass"
f_radii = list(cnc.frange(0, diameter / 2.0, mill_diam / 4.0))
print ";", f_radii
f_depths = []
for r in f_radii:
    each_depth = (r ** 2) / (4 * a_const) - depth
    f_depths.append((r, each_depth))
    print ";     %d\t%0.2f" % (r, each_depth)
print ";", f_depths

for r, each_depth in f_depths[1:]:
    print ";", r, each_depth
    cnc.circle((0,0), r, abs(each_depth), start_depth=abs(each_depth)-0.1)

