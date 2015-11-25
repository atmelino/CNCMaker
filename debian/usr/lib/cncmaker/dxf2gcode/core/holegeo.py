# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2014-2015
#    Robert Lichtenberger
#    Jean-Paul Schouwstra
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from __future__ import absolute_import
from __future__ import division

from copy import deepcopy
from math import pi

from core.point import Point


class HoleGeo(object):
    """
    HoleGeo represents drilling holes.
    """
    def __init__(self, Ps):
        """
        Standard Method to initialise the HoleGeo
        """
        self.Ps = Ps
        self.length = -1

        self.topLeft = None
        self.bottomRight = None

        self.abs_geo = None

    def __deepcopy__(self, memo):
        return HoleGeo(deepcopy(self.Ps, memo))

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nHoleGeo at (%s) " % self.Ps

    def reverse(self):
        """
        Reverses the direction.
        """
        pass

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)

        self.abs_geo = HoleGeo(Ps)

    def get_start_end_points(self, start_point, angles=None):
        if angles is None:
            return self.Ps
        elif angles:
            return self.Ps, 0
        else:
            return self.Ps, Point(0, -1) if start_point else Point(0, -1)

    def make_path(self, caller, drawHorLine):
        radius = caller.parentLayer.tool_diameter / 2
        segments = 30
        Ps = self.Ps.get_arc_point(0, radius)
        self.topLeft = deepcopy(Ps)
        self.bottomRight = deepcopy(Ps)
        for i in range(1, segments + 1):
            ang = i * 2 * pi / segments
            Pe = self.Ps.get_arc_point(ang, radius)
            drawHorLine(caller, Ps, Pe)
            self.topLeft.detTopLeft(Pe)
            self.bottomRight.detBottomRight(Pe)
            Ps = Pe

    def isHit(self, caller, xy, tol):
        tol2 = tol**2
        radius = caller.parentLayer.getToolRadius()
        segments = 30
        Ps = self.Ps.get_arc_point(0, radius)
        for i in range(1, segments + 1):
            ang = i * 2 * pi / segments
            Pe = self.Ps.get_arc_point(ang, radius)
            if xy.distance2_to_line(Ps, Pe) <= tol2:
                return True
            Ps = Pe
        return False

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a Hole.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        return PostPro.make_print_str("(Drilled hole)%nl")
