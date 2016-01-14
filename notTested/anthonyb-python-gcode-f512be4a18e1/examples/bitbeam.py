#!/usr/bin/python

"""
Generate the gcode to cut out bitbeam

-1, -2 or -3 will generate code to mill out a whole sheet
-t1, -t2 or -t3 will generate short test runs with one length 5 bitbeam
    (useful when working the kinks out of the job)
"""

# TODO: perhaps start from z=0 as the spoilboard, then mill down from
# z=14-15, to make it work on multiple heights of material 
# without reworking?
# UPDATE: I have a load of same depth pieces now, so not so urgent.

# dirty!
import sys
sys.path.insert(0, '..')

import cnc
cnc.init()

runout = 0.5 # mm
cnc.tool_width = 3.175 + runout
cnc.step_over = cnc.tool_width / 2
cnc.step_down = cnc.tool_width / 2

material_height = 11.000 # mm

# 1cm bitbeams - 'centibeams'?
# for real bitbeams, this should be 8.000, and holes should be 4.8mm
beam_width = 10.000


# bitbeams of 17cm long * 2, then 10 & 6 * 2, then 17 * 2, 
# then 6 & 10 * 3, etc. with 7.5mm between each beam

"""[
((10.0, 10.0), 17), 
((27.5, 10.0), 17), 
((45.0, 10.0), 10), ((45.0, 120.0), 6), 
((62.5, 10.0), 6), ((62.5, 80.0), 10), 
((80.0, 10.0), 17), 
((97.5, 10.0), 17), 
((115.0, 10.0), 10), ((115.0, 120.0), 6), 
((132.5, 10.0), 6), ((132.5, 80.0), 10), 
((150.0, 10.0), 10), ((150.0, 120.0), 6), 
((167.5, 10.0), 17)
]"""
beam_positions = []
beam_x = [10 + i*(beam_width+7.5) for i in range(10)]
beam_lengths = [
    (17, ), (17, ),  (10, 6), (6, 10), (17, ),
    (17, ), (10, 6), (6, 10), (10, 6), (17, ), ]

max_x = 75
for x, beams in zip(beam_x, beam_lengths):
    if x > max_x:
        break
    y = 10.0
    for beam in beams:
        beam_positions.append( ((x, y), beam) )
        y += beam_width * beam + 10.0

if len(sys.argv) == 1:
    print beam_positions


### 1st pass/file - cut out beams with holes
def vert_bitbeam(pos, length):
    opp_corner = (pos[0] + beam_width, pos[1] + beam_width * length)

    cnc.comment("milling down to bitbeam height/width")
    cnc.fillrectangle(
        pos, 
        opp_corner, 
        material_height - beam_width,
        offset="outside")

    # holes are just 3.175 for now, but might need to be wider
    cnc.comment("drilling holes")
    for i in range(length):
        hole_pos = (pos[0] + beam_width / 2, 
                    pos[1] + beam_width / 2 + i * beam_width)
        cnc.drill(hole_pos, material_height)

    cnc.comment("milling outside profile")
    cnc.rectangle(
        pos, 
        opp_corner, 
        material_height,
        start_depth=material_height - beam_width,
        offset="outside")

if '-1' in sys.argv:
    for pos, length in beam_positions:
        vert_bitbeam(pos, length)

if '-t1' in sys.argv:
    vert_bitbeam((5, 5), 5)


### 2nd (optional) pass/file - cut out guide for 3rd pass

if '-2' in sys.argv:
    # guide / registration holes along bottom and side to line up guide
    # drill into spoilboard, line up with 3.175 endmills or M3 bolts
    cnc.drill((5, 5), depth=material_height + 3.000)
    cnc.drill((80, 5), depth=material_height + 3.000)

    # 'dogbone' slots to hold beams tightly in place for step 3
    for pos, slot_length in beam_positions:
        cnc.comment("Milling dogbone slot at (%.02f, %.02f)" % pos)
        opp_corner = (pos[0] + beam_width, pos[1] + beam_width * length)
        cnc.dogbone_rect(pos, 
                     opp_corner, 
                     material_height,
                     sides=('top', 'bottom'))

if '-t2' in sys.argv:
    length = 5
    pos = (5, 5)
    cnc.comment("Milling dogbone slot at (%.02f, %.02f)" % pos)
    opp_corner = (pos[0] + beam_width, pos[1] + beam_width * length)
    cnc.dogbone_rect(pos, 
                 opp_corner,
                 material_height,
                 sides=('top', 'bottom'))


### 3rd pass/file - cut horizontal holes into the result of the 1st pass,
# which is placed sideways into the registered cutouts from the 3rd pass

# just drill holes
def vert_bitbeam_holes(pos, length):
    # holes are just 3.175 for now, but might need to be wider
    cnc.comment("drilling holes")
    for i in range(length):
        hole_pos = (pos[0] + beam_width / 2, 
                    pos[1] + beam_width / 2 + i * beam_width)
        cnc.drill(hole_pos, material_height)

if '-3' in sys.argv:
    for pos, length in beam_positions:
        vert_bitbeam_holes(pos, length)

if '-t3' in sys.argv:
    length = 5
    pos = (5, 5)
    vert_bitbeam_holes(pos, length)


