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

from math import sqrt, sin, cos, atan2

from core.point3d import Point3D


class Point(object):
    __slots__ = ["x", "y"]

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __str__(self):
        return 'X -> %6.3f  Y -> %6.3f' % (self.x, self.y)

    def __eq__(self, other):
        return (-1e-12 < self.x - other.x < 1e-12) and (-1e-12 < self.y - other.y < 1e-12)

    def __ne__(self, other):
        return not self == other

    def __neg__(self):
        return -1.0 * self

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __radd__(self, other):
        return Point(self.x + other, self.y + other)

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other):
        if isinstance(other, list):
            # Scale the points
            return Point(self.x * other[0], self.y * other[1])
        else:
            # Calculate Scalar (dot) Product
            return self.x * other.x + self.y * other.y

    def __rmul__(self, other):
        return Point(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Point(self.x / other, self.y / other)

    def eq(self, other, tol):
        return abs(self.x - other.x) < tol and abs(self.y - other.y) < tol

    def unit_vector(self):
        return self / self.length()

    def length_squared(self):
        return self.x**2 + self.y**2

    def length(self):
        return sqrt(self.length_squared())

    def distance(self, other):
        return (self - other).length()

    def distance2_to_line(self, Ps, Pe):
        dLine = Pe - Ps

        u = ((self.x - Ps.x) * dLine.x + (self.y - Ps.y) * dLine.y) / dLine.length_squared()
        if u > 1.0:
            u = 1.0
        elif u < 0.0:
            u = 0.0

        closest = Ps + u * dLine
        diff = closest - self
        return diff.length_squared()

    def norm_angle(self, other):
        """
        Returns angle between two given points
        """
        return atan2(other.y - self.y, other.x - self.x)

    def within_tol(self, other, tol):
        """
        Are the two points within tolerance
        """
        # TODO is this sufficient, or do we want to compare the distance
        return abs(self.x - other.x) <= tol and abs(self.y - other.y) < tol

    def get_arc_point(self, ang=0.0, r=1.0):
        """
        Returns the Point on the arc defined by r and the given angle
        @param ang: The angle of the Point
        @param r: The radius from the given Point
        @return: A Point at given radius and angle from Point self
        """
        return Point(self.x + cos(ang) * r, self.y + sin(ang) * r)

    def rot_sca_abs(self, sca=None, p0=None, pb=None, rot=None, parent=None):
        """
        Generates the absolute geometry based on the geometry self and the
        parent. If reverse = 1 is given the geometry may be reversed.
        @param sca: The Scale
        @param p0: The Offset
        @param pb: The Base Point
        @param rot: The angle by which the contour is rotated around p0
        @param parent: The parent of the geometry (EntityContentClass)
        @return: A new Point which is absolute position
        """
        if sca is None and parent is not None:
            p0 = parent.p0
            pb = parent.pb
            sca = parent.sca
            rot = parent.rot

            pc = self - pb
            rotx = (pc.x * cos(rot) + pc.y * -sin(rot)) * sca[0]
            roty = (pc.x * sin(rot) + pc.y * cos(rot)) * sca[1]
            p1 = Point(rotx, roty) + p0

            # Recursive loop if the point self is  introduced
            if parent.parent is not None:
                p1 = p1.rot_sca_abs(parent=parent.parent)

        elif parent is None and sca is None:
            p0 = Point()
            pb = Point()
            sca = [1.0, 1.0, 1.0]
            rot = 0.0

            pc = self - pb
            rotx = (pc.x * cos(rot) + pc.y * -sin(rot)) * sca[0]
            roty = (pc.x * sin(rot) + pc.y * cos(rot)) * sca[1]
            p1 = Point(rotx, roty) + p0

        else:
            pc = self - pb
            rotx = (pc.x * cos(rot) + pc.y * -sin(rot)) * sca[0]
            roty = (pc.x * sin(rot) + pc.y * cos(rot)) * sca[1]
            p1 = Point(rotx, roty) + p0

#        print(("Self:    %s\n" % self)+\
#              ("P0:      %s\n" % p0)+\
#              ("Pb:      %s\n" % pb)+\
#              ("Pc:      %s\n" % pc)+\
#              ("rot:     %0.1f\n" % degrees(rot))+\
#              ("sca:     %s\n" % sca)+\
#              ("P1:      %s\n\n" % p1))

        return p1

    def detTopLeft(self, point):
        self.x = min(self.x, point.x)
        self.y = max(self.y, point.y)

    def detBottomRight(self, point):
        self.x = max(self.x, point.x)
        self.y = min(self.y, point.y)

    def to3D(self, z=0.0):
        return Point3D(self.x, self.y, z)
