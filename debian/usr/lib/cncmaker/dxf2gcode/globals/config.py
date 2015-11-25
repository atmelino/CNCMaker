# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2009-2015
#    Christian Kohlöffel
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

import os
import pprint
import logging

from globals.configobj.configobj import ConfigObj, flatten_errors
from globals.configobj.validate import Validator
import globals.globals as g
from globals.d2gexceptions import *

from globals.six import text_type
import globals.constants as c
if c.PYQT5notPYQT4:
    from PyQt5 import QtCore
else:
    from PyQt4 import QtCore

logger = logging.getLogger("Core.Config")

CONFIG_VERSION = "9.7"
"""
version tag - increment this each time you edit CONFIG_SPEC

compared to version number in config file so
old versions are recognized and skipped"
"""

CONFIG_SPEC = str('''
#  Section and variable names must be valid Python identifiers
#      do not use whitespace in names

# do not edit the following section name:
    [Version]
    # do not edit the following value:
    config_version = string(default = "''' +
    str(CONFIG_VERSION) + '")\n' +
    '''
    [Paths]
    # by default look for DXF files in
    import_dir = string(default = "D:/Eclipse_Workspace/DXF2GCODE/trunk/dxf")

    # export generated gcode by default to
    output_dir = string(default = "D:")

    [Filters]
    pstoedit_cmd = string(default = "C:\Program Files (x86)\pstoedit\pstoedit.exe")
    pstoedit_opt = list(default = list('-f', 'dxf', '-mm', '-dt'))

    [Axis_letters]
    ax1_letter = string(default = "X")
    ax2_letter = string(default = "Y")
    ax3_letter = string(default = "Z")

    [Plane_Coordinates]
    axis1_start_end = float(default = 0)
    axis2_start_end = float(default = 0)

    [Depth_Coordinates]
    axis3_retract = float(default = 15.0)
    axis3_safe_margin = float(default = 3.0)
    axis3_start_mill_depth = float(default = 0.0)
    axis3_slice_depth = float(default = -1.5)
    axis3_mill_depth = float(default = -3.0)

    [Feed_Rates]
    f_g1_plane = float(default = 400)
    f_g1_depth = float(default = 150)

    [General]
    mode3d = boolean(default = False)
    write_to_stdout = boolean(default = False)
    show_disabled_paths = boolean(default = True)
    live_update_export_route = boolean(default = False)
    split_line_segments = boolean(default = False)
    automatic_cutter_compensation = boolean(default = False)
    # machine types supported: milling; lathe; drag_knife
    machine_type = option('milling', 'lathe', 'drag_knife', default = 'milling')
    # The unit used for all values in this file
    tool_units = option('mm', 'in', default = 'mm')

    [Cutter_Compensation]
    # if done_by_machine is set to False DXF2GCODE will create a virtual path for G41 and G42 command. And output
    # is set to G40; i.e. it will create the path that normally your machine will create with cutter compensation
    done_by_machine = boolean(default = True)
    # The percentage below denotes the minimal / maximal path of the cutter offset path that should be met such
    # that the current starting point can be considered as a good starting point. Otherwise it moves the starting
    # point to the next closest point and tries it again.
    min_length_considered = float(default = 0.60)
    max_length_considered = float(default = 1.40)
    # If the direction is not maintained of current shape it moves the starting point and tries it again
    direction_maintained = boolean(default = True)

    [Drag_Knife_Options]
    # drag_angle: if larger than this angle (in degrees), tool retracts to dragDepth
    # the dragDepth is given by axis3_slice_depth
    drag_angle = float(default = 20)

    [Route_Optimisation]
    default_TSP = boolean(default = False)

    # Path optimizer behaviour:
    #  CONSTRAIN_ORDER_ONLY: fixed Shapes and optimized Shapes can be mixed. Only order of fixed shapes is kept
    #  CONSTRAIN_PLACE_AFTER: optimized Shapes are always placed after any fixed Shape
    TSP_shape_order = option('CONSTRAIN_ORDER_ONLY', 'CONSTRAIN_PLACE_AFTER', default = 'CONSTRAIN_ORDER_ONLY')
    mutation_rate = float(default = 0.95)
    max_population = integer(default = 20)
    max_iterations = integer(default = 300)
    begin_art = option('ordered', 'random', 'heuristic', default = 'heuristic')

    [Import_Parameters]
    point_tolerance = float(default = 0.001)
    spline_check = integer(default = 3)
    fitting_tolerance = float(default = 0.001)
    # insert elements (which are part of a block) to layer where the block is inserted
    insert_at_block_layer = boolean(default = False)

    [Layer_Options]
    id_float_separator = string(default = ":")

    # mill options
    mill_depth_identifiers = list(default = list('MillDepth', 'Md', 'TiefeGesamt', 'Tg'))
    slice_depth_identifiers = list(default = list('SliceDepth', 'Sd', 'TiefeZustellung', 'Tz'))
    start_mill_depth_identifiers = list(default = list('StartMillDepth', 'SMd', 'StartTiefe', 'St'))
    retract_identifiers = list(default = list('RetractHeight', 'Rh', 'Freifahrthoehe', 'FFh'))
    safe_margin_identifiers = list(default = list('SafeMargin', 'Sm', 'Sicherheitshoehe', 'Sh'))
    f_g1_plane_identifiers = list(default = list('FeedXY', 'Fxy', 'VorschubXY', 'Vxy', 'F'))
    f_g1_depth_identifiers = list(default = list('FeedZ', 'Fz', 'VorschubZ', 'Vz'))

    # tool options
    tool_nr_identifiers = list(default = list('ToolNr', 'Tn', 'T', 'WerkzeugNummer', 'Wn'))
    tool_diameter_identifiers = list(default = list('ToolDiameter', 'Td', 'WerkzeugDurchmesser', 'Wd'))
    spindle_speed_identifiers = list(default = list('SpindleSpeed', 'Drehzahl', 'RPM', 'UPM', 'S'))
    start_radius_identifiers = list(default = list('StartRadius', 'Sr'))

    [Tool_Parameters]
    [[1]]
    diameter = float(default = 2.0)
    speed = float(default = 6000)
    start_radius = float(default = 0.2)

    [[2]]
    diameter = float(default = 2.0)
    speed = float(default = 6000.0)
    start_radius = float(default = 1.0)

    [[10]]
    diameter = float(default = 10.0)
    speed = float(default = 6000.0)
    start_radius = float(default = 2.0)

    [[__many__]]
    diameter = float(default = 3.0)
    speed = float(default = 6000)
    start_radius = float(default = 3.0)

    [Custom_Actions]
    [[custom_gcode]]
    gcode = string(default = '"""(change subsection name and insert your custom GCode here. Use triple quotes to place the code on several lines)"""')

    [[__many__]]
    gcode = string(default = "(change subsection name and insert your custom GCode here. Use triple quote to place the code on several lines)")

    [Logging]
    # Logging to textfile is enabled automatically for now
    logfile = string(default = "logfile.txt")

    # log levels are, in increasing importance:
    #      DEBUG; INFO; WARNING; ERROR; CRITICAL
    # log events with importance >= loglevel are logged to the
    # corresponding output

    # this really goes to stderr
    console_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'CRITICAL')

    file_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'DEBUG')

    # logging level for the message window
    window_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'INFO')

''').splitlines()
""" format, type and default value specification of the global config file"""


class MyConfig(object):
    """
    This class hosts all functions related to the Config File.
    """
    def __init__(self):
        """
        initialize the varspace of an existing plugin instance
        init_varspace() is a superclass method of plugin
        """

        self.folder = os.path.join(g.folder, c.DEFAULT_CONFIG_DIR)
        self.filename = os.path.join(self.folder, 'config' + c.CONFIG_EXTENSION)

        self.default_config = False # whether a new name was generated
        self.var_dict = dict()
        self.spec = ConfigObj(CONFIG_SPEC, interpolation=False, list_values=False, _inspec=True)

        # try:

        self.load_config()
        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.vars = DictDotLookup(self.var_dict)

        self.mode3d = self.vars.General['mode3d']

        self.machine_type = self.vars.General['machine_type']
        self.fitting_tolerance = self.vars.Import_Parameters['fitting_tolerance']
        self.point_tolerance = self.vars.Import_Parameters['point_tolerance']

        self.metric = 1  # true unit is determined while importing
        self.tool_units_metric = 0 if self.vars.General['tool_units'] == 'in' else 1

        # except Exception, msg:
        #     logger.warning(self.tr("Config loading failed: %s") % msg)
        #     return False

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return text_type(QtCore.QCoreApplication.translate('MyConfig',
                                                           string_to_translate))

    def make_settings_folder(self):
        """Create settings folder if necessary"""
        try:
            os.mkdir(self.folder)
        except OSError:
            pass

    def load_config(self):
        """Load Config File"""
        if os.path.isfile(self.filename):
            try:
                # file exists, read & validate it
                self.var_dict = ConfigObj(self.filename, configspec=CONFIG_SPEC)
                _vdt = Validator()
                result = self.var_dict.validate(_vdt, preserve_errors=True)
                validate_errors = flatten_errors(self.var_dict, result)

                if validate_errors:
                    logger.error(self.tr("errors reading %s:") % self.filename)

                for entry in validate_errors:
                    section_list, key, error = entry
                    if key is not None:
                        section_list.append(key)
                    else:
                        section_list.append('[missing section]')
                    section_string = ', '.join(section_list)
                    if not error:
                        error = self.tr('Missing value or section.')
                    logger.error(section_string + ' = ' + error)

                if validate_errors:
                    raise BadConfigFileError("syntax errors in config file")

                # check config file version against internal version
                if CONFIG_VERSION:
                    fileversion = self.var_dict['Version']['config_version']  # this could raise KeyError

                    if fileversion != CONFIG_VERSION:
                        raise VersionMismatchError(fileversion, CONFIG_VERSION)

            except VersionMismatchError:
                raise VersionMismatchError(fileversion, CONFIG_VERSION)  # TODO pop-up error?

            except Exception as inst:
                logger.error(inst)
                (base, ext) = os.path.splitext(self.filename)
                badfilename = base + c.BAD_CONFIG_EXTENSION
                logger.debug(self.tr("trying to rename bad cfg %s to %s") % (self.filename, badfilename))
                try:
                    os.rename(self.filename, badfilename)
                except OSError as e:
                    logger.error(self.tr("rename(%s,%s) failed: %s") % (self.filename, badfilename, e.strerror))
                    raise
                else:
                    logger.debug(self.tr("renamed bad varspace %s to '%s'") % (self.filename, badfilename))
                    self.create_default_config()
                    self.default_config = True
                    logger.debug(self.tr("created default varspace '%s'") % self.filename)
            else:
                self.default_config = False
                # logger.debug(self.dir())
                # logger.debug(self.tr("created default varspace '%s'") % self.filename)
                # logger.debug(self.tr("read existing varspace '%s'") % self.filename)
        else:
            self.create_default_config()
            self.default_config = True
            logger.debug(self.tr("created default varspace '%s'") % self.filename)

        self.var_dict.main.interpolation = False  # avoid ConfigObj getting too clever

    def create_default_config(self):
        # check for existing setting folder or create one
        self.make_settings_folder()

        # derive config file with defaults from spec
        self.var_dict = ConfigObj(configspec=CONFIG_SPEC)
        _vdt = Validator()
        self.var_dict.validate(_vdt, copy=True)
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def _save_varspace(self):
        """Saves Variables space"""
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def print_vars(self):
        """Prints Variables"""
        print("Variables:")
        for k, v in self.var_dict['Variables'].items():
            print(k, "=", v)


class DictDotLookup(object):
    """
    Creates objects that behave much like a dictionaries, but allow nested
    key access using object '.' (dot) lookups.
    """
    def __init__(self, d):
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]

    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def __setitem__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value

    def __iter__(self):
        return iter(self.__dict__.keys())

    def __repr__(self):
        return pprint.pformat(self.__dict__)

# if __name__ == '__main__':
#     cfg_data = eval("""{
#         'foo' : {
#             'bar' : {
#                 'tdata' : (
#                     {'baz' : 1 },
#                     {'baz' : 2 },
#                     {'baz' : 3 },
#                 ),
#             },
#         },
#         'quux' : False,
#     }""")
#
#     cfg = DictDotLookup(cfg_data)
#
#     # iterate
#     for k, v in cfg.__iter__(): #foo.bar.iteritems():
#         print k, " = ", v
#
#     print "cfg=", cfg
#
#     #   Standard nested dictionary lookup.
#     print 'normal lookup :', cfg['foo']['bar']['tdata'][0]['baz']
#
#     #   Dot-style nested lookup.
#     print 'dot lookup    :', cfg.foo.bar.tdata[0].baz
#
#     print "qux=", cfg.quux
#     cfg.quux = '123'
#     print "qux=", cfg.quux
#
#     del cfg.foo.bar
#     cfg.foo.bar = 4711
#     print 'dot lookup    :', cfg.foo.bar #.tdata[0].baz
