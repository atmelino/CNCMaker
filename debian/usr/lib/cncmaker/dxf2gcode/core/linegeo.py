# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
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

from __future__ import division

from math import sqrt, pi
from copy import deepcopy


class LineGeo(object):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """
    def __init__(self, Ps, Pe):
        """
        Standard Method to initialize the LineGeo.
        @param Ps: The Start Point of the line
        @param Pe: the End Point of the line
        """
        self.Ps = Ps
        self.Pe = Pe
        self.length = self.Ps.distance(self.Pe)

        self.topLeft = None
        self.bottomRight = None

        self.abs_geo = None

    def __deepcopy__(self, memo):
        return LineGeo(deepcopy(self.Ps, memo),
                       deepcopy(self.Pe, memo))

    def __str__(self):
        return "\nLineGeo" +\
               "\nPs:     %s" % self.Ps +\
               "\nPe:     %s" % self.Pe +\
               "\nlength: %0.5f" % self.length

    def to_short_string(self):
        return "(%f, %f) -> (%f, %f)" % (self.Ps.x, self.Ps.y, self.Pe.x, self.Pe.y)

    def reverse(self):
        self.Ps, self.Pe = self.Pe, self.Ps
        if self.abs_geo:
            self.abs_geo.reverse()

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)

        self.abs_geo = LineGeo(Ps=Ps, Pe=Pe)

    def distance2point(self, point):
        """
        Returns the distance between a line and a given Point
        @param point: The Point which shall be checked
        @return: returns the distance to the Line
        """
        # TODO to check if it can be replaced with distance2_to_line (of Point class)
        if self.Ps == self.Pe:
            return 1e10
        else:
            AE = self.Ps.distance(self.Pe)
            AP = self.Ps.distance(point)
            EP = self.Pe.distance(point)
            AEPA = (AE + AP + EP) / 2
            return abs(2 * sqrt(abs(AEPA * (AEPA - AE) *
                                    (AEPA - AP) * (AEPA - EP))) / AE)

    def update_start_end_points(self, start_point, value):
        prv_ang = self.Ps.norm_angle(self.Pe)
        if start_point:
            self.Ps = value
        else:
            self.Pe = value
        new_ang = self.Ps.norm_angle(self.Pe)

        if 2 * abs(((prv_ang - new_ang) + pi) % (2 * pi) - pi) >= pi:
            # seems very unlikely that this is what you want - the direction changed (too drastically)
            self.Ps, self.Pe = self.Pe, self.Ps

        self.length = self.Ps.distance(self.Pe)

    def get_start_end_points(self, start_point, angles=None):
        if start_point:
            if angles is None:
                return self.Ps
            elif angles:
                return self.Ps, self.Ps.norm_angle(self.Pe)
            else:
                return self.Ps, (self.Pe - self.Ps).unit_vector()
        else:
            if angles is None:
                return self.Pe
            elif angles:
                return self.Pe, self.Pe.norm_angle(self.Ps)
            else:
                return self.Pe, (self.Pe - self.Ps).unit_vector()

    def make_path(self, caller, drawHorLine):
        drawHorLine(caller, self.Ps, self.Pe)
        self.topLeft = deepcopy(self.Ps)
        self.bottomRight = deepcopy(self.Ps)
        self.topLeft.detTopLeft(self.Pe)
        self.bottomRight.detBottomRight(self.Pe)

    def isHit(self, caller, xy, tol):
        return xy.distance2_to_line(self.Ps, self.Pe) <= tol**2

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a Line.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        Ps = self.get_start_end_points(True)
        Pe = self.get_start_end_points(False)
        return PostPro.lin_pol_xy(Ps, Pe)
