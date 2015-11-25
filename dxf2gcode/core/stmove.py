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

from math import sin, cos, pi, sqrt
from copy import deepcopy
import logging

import globals.globals as g
from core.linegeo import LineGeo
from core.arcgeo import ArcGeo
from core.point import Point
from core.intersect import Intersect
from core.shape import Geos

logger = logging.getLogger('Gui.StMove')


class StMove(object):
    """
    This Function generates the StartMove for each shape. It
    also performs the Plotting and Export of this moves. It is linked
    to the shape of its parent
    """
    # only need default arguments here because of the change of usage with super in QGraphicsLineItem
    def __init__(self, shape=None):
        if shape is None:
            return

        self.shape = shape

        self.start, self.angle = self.shape.get_start_end_points(True, True)
        self.end = self.start

        self.geos = Geos([])

        self.make_start_moves()

    def append(self, geo):
        # we don't want to additional scale / rotate the stmove geo
        # so no geo.make_abs_geo(self.shape.parentEntity)
        geo.make_abs_geo()
        self.geos.append(geo)

    def make_start_moves(self):
        """
        This function called to create the start move. It will
        be generated based on the given values for start and angle.
        """
        self.geos = Geos([])

        if g.config.machine_type == 'drag_knife':
            self.make_swivelknife_move()
            return
        elif self.shape.cut_cor != 40 and not g.config.vars.Cutter_Compensation["done_by_machine"]:
            self.make_own_cutter_compensation()
            return

        # Get the start rad. and the length of the line segment at begin.
        start_rad = self.shape.parentLayer.start_radius

        # Get tool radius based on tool diameter.
        tool_rad = self.shape.parentLayer.getToolRadius()

        # Calculate the starting point with and without compensation.
        start = self.start
        angle = self.angle

        if self.shape.cut_cor == 40:
            self.append(RapidPos(start))

        # Cutting Compensation Left
        elif self.shape.cut_cor == 41:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle + pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Pa_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Pa_ein.get_arc_point(angle + pi/2, start_rad)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(RapidPos(start_ein))

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(start_ein, Pa_ein)
            self.append(start_line)

            # generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Pa_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=1)
            self.append(start_rad)

        # Cutting Compensation Right
        elif self.shape.cut_cor == 42:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle - pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Pa_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Pa_ein.get_arc_point(angle - pi/2, start_rad)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(RapidPos(start_ein))

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(start_ein, Pa_ein)
            self.append(start_line)

            # generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Pa_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=0)
            self.append(start_rad)

    def make_swivelknife_move(self):
        """
        Set these variables for your tool and material
        @param offset: knife tip distance from tool centerline. The radius of the
        tool is used for this.
        """
        offset = self.shape.parentLayer.getToolRadius()
        drag_angle = self.shape.drag_angle

        startnorm = offset*Point(1, 0)  # TODO make knife direction a config setting
        prvend, prvnorm = Point(), Point()
        first = True

        for geo in self.shape.geos.abs_iter():
            if isinstance(geo, LineGeo):
                geo_b = deepcopy(geo)
                if first:
                    first = False
                    prvend = geo_b.Ps + startnorm
                    prvnorm = startnorm
                norm = offset * (geo_b.Pe - geo_b.Ps).unit_vector()
                geo_b.Ps += norm
                geo_b.Pe += norm
                if not prvnorm == norm:
                    direction = prvnorm.to3D().cross_product(norm.to3D()).z
                    swivel = ArcGeo(Ps=prvend, Pe=geo_b.Ps, r=offset, direction=direction)
                    swivel.drag = drag_angle < abs(swivel.ext)
                    self.append(swivel)
                self.append(geo_b)

                prvend = geo_b.Pe
                prvnorm = norm
            elif isinstance(geo, ArcGeo):
                geo_b = deepcopy(geo)
                if first:
                    first = False
                    prvend = geo_b.Ps + startnorm
                    prvnorm = startnorm
                if geo_b.ext > 0.0:
                    norma = offset*Point(cos(geo_b.s_ang+pi/2), sin(geo_b.s_ang+pi/2))
                    norme = Point(cos(geo_b.e_ang+pi/2), sin(geo_b.e_ang+pi/2))
                else:
                    norma = offset*Point(cos(geo_b.s_ang-pi/2), sin(geo_b.s_ang-pi/2))
                    norme = Point(cos(geo_b.e_ang-pi/2), sin(geo_b.e_ang-pi/2))
                geo_b.Ps += norma
                if norme.x > 0:
                    geo_b.Pe = Point(geo_b.Pe.x+offset/(sqrt(1+(norme.y/norme.x)**2)),
                                     geo_b.Pe.y+(offset*norme.y/norme.x)/(sqrt(1+(norme.y/norme.x)**2)))
                elif norme.x == 0:
                    geo_b.Pe = Point(geo_b.Pe.x,
                                     geo_b.Pe.y)
                else:
                    geo_b.Pe = Point(geo_b.Pe.x-offset/(sqrt(1+(norme.y/norme.x)**2)),
                                     geo_b.Pe.y-(offset*norme.y/norme.x)/(sqrt(1+(norme.y/norme.x)**2)))
                if prvnorm != norma:
                    direction = prvnorm.to3D().cross_product(norma.to3D()).z
                    swivel = ArcGeo(Ps=prvend, Pe=geo_b.Ps, r=offset, direction=direction)
                    swivel.drag = drag_angle < abs(swivel.ext)
                    self.append(swivel)
                prvend = geo_b.Pe
                prvnorm = offset*norme
                if -pi < geo_b.ext < pi:
                    self.append(ArcGeo(Ps=geo_b.Ps, Pe=geo_b.Pe, r=sqrt(geo_b.r**2+offset**2), direction=geo_b.ext))
                else:
                    geo_b = ArcGeo(Ps=geo_b.Ps, Pe=geo_b.Pe, r=sqrt(geo_b.r**2+offset**2), direction=-geo_b.ext)
                    geo_b.ext = -geo_b.ext
                    self.append(geo_b)
            # TODO support different geos, or disable them in the GUI
            # else:
            #     self.append(copy(geo))
        if not prvnorm == startnorm:
            direction = prvnorm.to3D().cross_product(startnorm.to3D()).z
            self.append(ArcGeo(Ps=prvend, Pe=prvend-prvnorm+startnorm, r=offset, direction=direction))

        self.geos.insert(0, RapidPos(self.geos.abs_el(0).Ps))
        self.geos[0].make_abs_geo()

    def make_own_cutter_compensation(self):
        toolwidth = self.shape.parentLayer.getToolRadius()

        geos = Geos([])

        direction = -1 if self.shape.cut_cor == 41 else 1

        if self.shape.closed:
            end, end_dir = self.shape.get_start_end_points(False, False)
            end_proj = Point(direction * end_dir.y, -direction * end_dir.x)
            prv_Pe = end + toolwidth * end_proj
        else:
            prv_Pe = None
        for geo_nr, geo in enumerate(self.shape.geos.abs_iter()):
            start, start_dir = geo.get_start_end_points(True, False)
            end, end_dir = geo.get_start_end_points(False, False)
            start_proj = Point(direction * start_dir.y, -direction * start_dir.x)
            end_proj = Point(direction * end_dir.y, -direction * end_dir.x)
            Ps = start + toolwidth * start_proj
            Pe = end + toolwidth * end_proj
            if Ps == Pe:
                continue
            if prv_Pe:
                r = geo.Ps.distance(Ps)
                d = (prv_Pe - geo.Ps).to3D().cross_product((Ps - geo.Ps).to3D()).z
                if direction * d > 0 and prv_Pe != Ps:
                    geos.append(ArcGeo(Ps=prv_Pe, Pe=Ps, O=geo.Ps, r=r, direction=d))
                    geos[-1].geo_nr = geo_nr
                # else:
                #     geos.append(LineGeo(Ps=prv_Pe, Pe=Ps))
            if isinstance(geo, LineGeo):
                geos.append(LineGeo(Ps, Pe))
                geos[-1].geo_nr = geo_nr
            elif isinstance(geo, ArcGeo):
                O = geo.O
                r = O.distance(Ps)
                geos.append(ArcGeo(Ps=Ps, Pe=Pe, O=O, r=r, direction=geo.ext))
                geos[-1].geo_nr = geo_nr
            # TODO other geos are not supported; disable them in gui for this option
            # else:
            #     geos.append(geo)
            prv_Pe = Pe

        tot_length = 0
        for geo in geos.abs_iter():
            tot_length += geo.length

        reorder_shape = False
        for start_geo_nr in range(len(geos)):
            # if shape is not closed we may only remove shapes from the start
            last_geo_nr = start_geo_nr if self.shape.closed else 0
            geos_adj = deepcopy(geos[start_geo_nr:]) + deepcopy(geos[:last_geo_nr])
            new_geos = Geos([])
            i = 0
            while i in range(len(geos_adj)):
                geo = geos_adj[i]
                intersections = []
                for j in range(i+1, len(geos_adj)):
                    intersection = Intersect.get_intersection_point(geos_adj[j], geos_adj[i])
                    if intersection and intersection != geos_adj[i].Ps:
                        intersections.append([j, intersection])
                if len(intersections) > 0:
                    intersection = intersections[-1]
                    change_end_of_geo = True
                    if i == 0 and intersection[0] >= len(geos_adj)//2:
                        geo.update_start_end_points(True, intersection[1])
                        geos_adj[intersection[0]].update_start_end_points(False, intersection[1])
                        if len(intersections) > 1:
                            intersection = intersections[-2]
                        else:
                            change_end_of_geo = False
                            i += 1
                    if change_end_of_geo:
                        geo.update_start_end_points(False, intersection[1])
                        i = intersection[0]
                        geos_adj[i].update_start_end_points(True, intersection[1])
                else:
                    i += 1
                # TODO
                # if len(new_geos) > 0 and not new_geos[-1].Pe.eq(geo.Ps, g.config.fitting_tolerance):
                #     break  # geo is disconnected
                new_geos.append(geo)
                if new_geos[0].Ps == new_geos[-1].Pe:
                    break

            new_length = 0
            for geo in new_geos:
                new_length += geo.length

            if tot_length * g.config.vars.Cutter_Compensation['min_length_considered']\
                    <= new_length <= tot_length * g.config.vars.Cutter_Compensation['max_length_considered'] and\
               (not g.config.vars.Cutter_Compensation['direction_maintained'] or
                    not self.shape.closed or self.shape.isDirectionOfGeosCCW(new_geos) != self.shape.cw):
                self.append(RapidPos(new_geos[0].Ps))
                for geo in new_geos:
                    if geo.Ps != geo.Pe:
                        self.append(geo)
                reorder_shape = True
                break
        if reorder_shape and self.shape.closed:
            # we do not reorder the original shape if it's not closed
            self.shape.geos = Geos(self.shape.geos[geos[start_geo_nr].geo_nr:] + self.shape.geos[:geos[start_geo_nr].geo_nr])

        if len(self.geos) == 0:
            self.append(RapidPos(self.start))

    def make_path(self, drawHorLine, drawVerLine):
        for geo in self.geos.abs_iter():
            drawVerLine(self.shape, geo.get_start_end_points(True))
            geo.make_path(self.shape, drawHorLine)
        drawVerLine(self.shape, geo.get_start_end_points(False))


class RapidPos(Point):
    def __init__(self, point):
        Point.__init__(self, point.x, point.y)
        self.abs_geo = None

    def get_start_end_points(self, start_point, angles=None):
        if angles is None:
            return self
        elif angles:
            return self, 0
        else:
            return self, Point(0, -1) if start_point else Point(0, -1)

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        self.abs_geo = RapidPos(self.rot_sca_abs(parent=parent))

    def make_path(self, caller, drawHorLine):
        pass

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a rapid position.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        return PostPro.rap_pos_xy(self)
