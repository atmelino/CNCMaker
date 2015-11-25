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

from __future__ import absolute_import
from __future__ import division

from math import sqrt, sin, cos, pi, degrees
from copy import deepcopy
import logging

from core.point import Point
import globals.globals as g

from globals.six import text_type
import globals.constants as c
if c.PYQT5notPYQT4:
    from PyQt5 import QtCore
else:
    from PyQt4 import QtCore

logger = logging.getLogger("Core.ArcGeo")


class ArcGeo(object):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """
    def __init__(self, Ps=None, Pe=None, O=None, r=1,
                 s_ang=None, e_ang=None, direction=1, drag=False):
        """
        Standard Method to initialize the ArcGeo. Not all of the parameters are
        required to fully define a arc. e.g. Ps and Pe may be given or s_ang and
        e_ang
        @param Ps: The Start Point of the arc
        @param Pe: the End Point of the arc
        @param O: The center of the arc
        @param r: The radius of the arc
        @param s_ang: The Start Angle of the arc
        @param e_ang: the End Angle of the arc
        @param direction: The arc direction where 1 is in positive direction
        """
        self.type = "ArcGeo"
        self.Ps = Ps
        self.Pe = Pe
        self.O = O
        self.r = abs(r)
        self.s_ang = s_ang
        self.e_ang = e_ang
        self.drag = drag

        # Get the Circle center point with known Start and End Points
        if self.O is None:

            if self.Ps is not None and\
               self.Pe is not None and\
               direction is not None:

                arc = self.Pe.norm_angle(self.Ps) - pi / 2
                m = self.Pe.distance(self.Ps) / 2

                if abs(self.r - m) < g.config.fitting_tolerance:
                    lo = 0.0
                else:
                    lo = sqrt(pow(self.r, 2) - pow(m, 2))

                d = -1 if direction < 0 else 1

                self.O = self.Ps + (self.Pe - self.Ps) / 2
                self.O.y += lo * sin(arc) * d
                self.O.x += lo * cos(arc) * d

            # Compute center point
            elif self.s_ang is not None:
                self.O.x = self.Ps.x - self.r * cos(self.s_ang)
                self.O.y = self.Ps.y - self.r * sin(self.s_ang)
            else:
                logger.error(self.tr("Missing value for Arc Geometry"))

        # Calculate start and end angles
        if self.s_ang is None:
            self.s_ang = self.O.norm_angle(self.Ps)
        if self.e_ang is None:
            self.e_ang = self.O.norm_angle(self.Pe)

        self.ext = self.dif_ang(self.Ps, self.Pe, direction)

        self.length = self.r * abs(self.ext)

        self.topLeft = None
        self.bottomRight = None

        self.abs_geo = None

    def __deepcopy__(self, memo):
        return ArcGeo(deepcopy(self.Ps, memo),
                      deepcopy(self.Pe, memo),
                      deepcopy(self.O, memo),
                      deepcopy(self.r, memo),
                      deepcopy(self.s_ang, memo),
                      deepcopy(self.e_ang, memo),
                      deepcopy(self.ext, memo))

    def __str__(self):
        return "\nArcGeo" +\
               "\nPs:  %s; s_ang: %0.5f" % (self.Ps, self.s_ang) +\
               "\nPe:  %s; e_ang: %0.5f" % (self.Pe, self.e_ang) +\
               "\nO:   %s; r: %0.3f" % (self.O, self.r) +\
               "\next: %0.5f; length: %0.5f" % (self.ext, self.length)

    def toShortString(self):
        return "(%f, %f) -> (%f, %f)" % (self.Ps.x, self.Ps.y, self.Pe.x, self.Pe.y)

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return text_type(QtCore.QCoreApplication.translate('ArcGeo',
                                                           string_to_translate))

    def dif_ang(self, Ps, Pe, direction):
        """
        Calculated the angle between Pe and Ps with respect to the origin
        @param Ps: the start Point of the arc
        @param Pe: the end Point of the arc
        @param direction: the direction of the arc
        @return: Returns the angle between -2* pi and 2 *pi for the arc,
        0 excluded - we got a complete circle
        """
        dif_ang = (self.O.norm_angle(Pe) - self.O.norm_angle(Ps)) % (-2 * pi)

        if direction > 0:
            dif_ang += 2 * pi
        elif dif_ang == 0:
            dif_ang = -2 * pi

        return dif_ang

    def reverse(self):
        self.Ps, self.Pe = self.Pe, self.Ps
        self.s_ang, self.e_ang = self.e_ang, self.s_ang
        self.ext = -self.ext
        if self.abs_geo:
            self.abs_geo.reverse()

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)
        O = self.O.rot_sca_abs(parent=parent)
        r = self.scaled_r(self.r, parent)

        direction = 1 if self.ext > 0.0 else -1

        if parent is not None and parent.sca[0] * parent.sca[1] < 0.0:
            direction *= -1

        self.abs_geo = ArcGeo(Ps=Ps, Pe=Pe, O=O, r=r, direction=direction)

    def scaled_r(self, r, parent):
        """
        Scales the radius based on the scale given in its parents. This is done
        recursively.
        @param r: The radius which shall be scaled
        @param parent: The parent Entity (Instance: EntityContentClass)
        @return: The scaled radius
        """
        # Rekursive Schleife falls mehrfach verschachtelt.
        # Recursive loop if nested.
        if parent is not None:
            r *= parent.sca[0]
            r = self.scaled_r(r, parent.parent)

        return r

    def update_start_end_points(self, start_point, value):
        prv_dir = self.ext
        if start_point:
            self.Ps = value
            self.s_ang = self.O.norm_angle(self.Ps)
        else:
            self.Pe = value
            self.e_ang = self.O.norm_angle(self.Pe)

        self.ext = self.dif_ang(self.Ps, self.Pe, self.ext)

        if 2 * abs(((prv_dir - self.ext) + pi) % (2 * pi) - pi) >= pi:
            # seems very unlikely that this is what you want - the direction changed (too drastically)
            self.Ps, self.Pe = self.Pe, self.Ps
            self.s_ang, self.e_ang = self.e_ang, self.s_ang
            self.ext = self.dif_ang(self.Ps, self.Pe, prv_dir)

        self.length = self.r * abs(self.ext)

    def get_start_end_points(self, start_point, angles=None):
        if start_point:
            if angles is None:
                return self.Ps
            elif angles:
                return self.Ps, self.s_ang + pi/2 * self.ext / abs(self.ext)
            else:
                direction = (self.O - self.Ps).unit_vector()
                direction = -direction if self.ext >= 0 else direction
                return self.Ps, Point(-direction.y, direction.x)
        else:
            if angles is None:
                return self.Pe
            elif angles:
                return self.Pe, self.e_ang - pi/2 * self.ext / abs(self.ext)
            else:
                direction = (self.O - self.Pe).unit_vector()
                direction = -direction if self.ext >= 0 else direction
                return self.Pe, Point(-direction.y, direction.x)

    def get_point_from_start(self, i, segments):
        ang = self.s_ang + i * self.ext / segments
        return self.O.get_arc_point(ang, self.r)

    def make_path(self, caller, drawHorLine):
        segments = int(abs(degrees(self.ext)) // 3 + 1)
        Ps = self.O.get_arc_point(self.s_ang, self.r)
        self.topLeft = deepcopy(Ps)
        self.bottomRight = deepcopy(Ps)
        for i in range(1, segments + 1):
            Pe = self.get_point_from_start(i, segments)
            drawHorLine(caller, Ps, Pe)
            self.topLeft.detTopLeft(Pe)
            self.bottomRight.detBottomRight(Pe)
            Ps = Pe

    def isHit(self, caller, xy, tol):
        tol2 = tol**2
        segments = int(abs(degrees(self.ext)) // 3 + 1)
        Ps = self.O.get_arc_point(self.s_ang, self.r)
        for i in range(1, segments + 1):
            Pe = self.get_point_from_start(i, segments)
            if xy.distance2_to_line(Ps, Pe) <= tol2:
                return True
            Ps = Pe
        return False

    def Write_GCode(self, PostPro=None):
        """
        Writes the GCODE for an Arc.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        Ps, s_ang = self.get_start_end_points(True, True)
        Pe, e_ang = self.get_start_end_points(False, True)

        O = self.O
        r = self.r
        IJ = O - Ps

        # If the radius of the element is bigger than the max, radius export the element as an line.
        if r > PostPro.vars.General["max_arc_radius"]:
            string = PostPro.lin_pol_xy(Ps, Pe)
        else:
            if self.ext > 0:
                string = PostPro.lin_pol_arc("ccw", Ps, Pe, s_ang, e_ang, r, O, IJ)
            elif self.ext < 0 and PostPro.vars.General["export_ccw_arcs_only"]:
                string = PostPro.lin_pol_arc("ccw", Pe, Ps, e_ang, s_ang, r, O, O - Pe)
            else:
                string = PostPro.lin_pol_arc("cw", Ps, Pe, s_ang, e_ang, r, O, IJ)
        return string
