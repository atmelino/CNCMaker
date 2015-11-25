# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
#    Jean-Paul Schouwstra
#    Robert Lichtenberger
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

import re

import globals.globals as g


class LayerContent(object):
    def __init__(self, nr, name, shapes):
        self.nr = nr
        self.name = name
        self.shapes = Shapes(shapes)
        self.exp_order = []  # used for shape order optimization, ... Only contains shapes

        # Use default tool 1 (always exists in config)
        self.tool_nr = 1
        self.tool_diameter = g.config.vars.Tool_Parameters['1']['diameter']
        self.speed = g.config.vars.Tool_Parameters['1']['speed']
        self.start_radius = g.config.vars.Tool_Parameters['1']['start_radius']

        # preset defaults
        self.axis3_retract = g.config.vars.Depth_Coordinates['axis3_retract']
        self.axis3_safe_margin = g.config.vars.Depth_Coordinates['axis3_safe_margin']

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nLayerContent" +\
               "\nnr:     %i" % self.nr +\
               "\nname:   %s" % self.name +\
               "\nshapes: %s" % self.shapes

    def should_ignore(self):
        return self.name.startswith('IGNORE' + g.config.vars.Layer_Options['id_float_separator'])

    def isBreakLayer(self):
        return self.name.startswith('BREAKS' + g.config.vars.Layer_Options['id_float_separator'])

    def isMillLayer(self):
        return self.name.startswith('MILL' + g.config.vars.Layer_Options['id_float_separator'])

    def isDrillLayer(self):
        return self.name.startswith('DRILL' + g.config.vars.Layer_Options['id_float_separator'])

    def isParameterizableLayer(self):
        return self.isMillLayer() or self.isDrillLayer() or self.isBreakLayer()

    def automaticCutterCompensationEnabled(self):
        return not self.should_ignore() and not self.isDrillLayer()

    def getToolRadius(self):
        return self.tool_diameter / 2

    def overrideDefaults(self):
        # search for layer commands to override defaults
        if self.isParameterizableLayer():
            layer_commands = self.name.replace(",", ".")
            lopts_re = re.compile("([a-zA-Z]+ *"+g.config.vars.Layer_Options['id_float_separator']+" *[\-\.0-9]+)")
            # print lopts_re.findall(layer_commands)
            for lc in lopts_re.findall(layer_commands):
                name, value = lc.split(g.config.vars.Layer_Options['id_float_separator'])
                name = name.strip()
                # print '\"%s\" \"%s\"' %(name, value)
                if name in g.config.vars.Layer_Options['tool_nr_identifiers']:
                    self.tool_nr = float(value)
                elif name in g.config.vars.Layer_Options['tool_diameter_identifiers']:
                    self.tool_diameter = float(value)
                elif name in g.config.vars.Layer_Options['spindle_speed_identifiers']:
                    self.speed = float(value)
                elif name in g.config.vars.Layer_Options['start_radius_identifiers']:
                    self.start_radius = float(value)
                elif name in g.config.vars.Layer_Options['retract_identifiers']:
                    self.axis3_retract = float(value)
                elif name in g.config.vars.Layer_Options['safe_margin_identifiers']:
                    self.axis3_safe_margin = float(value)
                elif name in g.config.vars.Layer_Options['start_mill_depth_identifiers']:
                    for shape in self.shapes:
                        shape.axis3_start_mill_depth = float(value)
                elif name in g.config.vars.Layer_Options['slice_depth_identifiers']:
                    for shape in self.shapes:
                        shape.axis3_slice_depth = float(value)
                elif name in g.config.vars.Layer_Options['mill_depth_identifiers']:
                    for shape in self.shapes:
                        shape.axis3_mill_depth = float(value)
                elif name in g.config.vars.Layer_Options['f_g1_plane_identifiers']:
                    for shape in self.shapes:
                        shape.f_g1_plane = float(value)
                elif name in g.config.vars.Layer_Options['f_g1_depth_identifiers']:
                    for shape in self.shapes:
                        shape.f_g1_depth = float(value)
        if self.should_ignore():
            # Disable shape by default, if it lives on an ignored layer
            for shape in self.shapes:
                shape.setDisable(True)


class Layers(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    # def __iter__(self):
    def non_break_layer_iter(self):
        for layer in list.__iter__(self):
            if not layer.isBreakLayer():
                yield layer
        else:
            raise StopIteration()

    def break_layer_iter(self):
        for layer in list.__iter__(self):
            if layer.isBreakLayer():
                yield layer
        else:
            raise StopIteration()


class Shapes(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    # def __iter__(self):
    def selected_iter(self):
        for shape in list.__iter__(self):
            if shape.selected:
                yield shape
        else:
            raise StopIteration()

    def not_selected_iter(self):
        for shape in list.__iter__(self):
            if not shape.selected:
                yield shape
        else:
            raise StopIteration()

    def not_disabled_iter(self):
        for shape in list.__iter__(self):
            if not shape.disabled:
                yield shape
        else:
            raise StopIteration()
