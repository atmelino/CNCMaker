# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2011-2014
#    Christian Kohlöffel
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

"""
Special purpose canvas including all required plotting function etc.
"""

from globals.six import text_type
import globals.constants as c
if c.PYQT5notPYQT4:
    from PyQt5.QtWidgets import QTextBrowser
    from PyQt5 import QtCore
else:
    from PyQt4.QtGui import QTextBrowser
    from PyQt4 import QtCore

class MessageBox(QTextBrowser):
    """
    The MessageBox Class performs the write functions in the Message Window.
    The previous defined MessageBox class is used as output (Within ui).
    @sideeffect: None
    """

    def __init__(self, origobj):
        """
        Initialization of the MessageBox class.
        @param origobj: This is the reference to to parent class initialized
        previously.
        """
        super(MessageBox, self).__init__()
        self.setOpenExternalLinks(True)

        self.append(self.tr("You are using DXF2GCODE"))
        self.append(self.tr("Version %s (%s)") % (c.VERSION, c.DATE))
        self.append(self.tr("For more information and updates visit:"))
        self.append("<a href='http://sourceforge.net/projects/dxf2gcode/'>http://sourceforge.net/projects/dxf2gcode/</a>")

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return text_type(QtCore.QCoreApplication.translate('MessageBox',
                                                           string_to_translate))

    def write(self, string):
        """
        The function is called by the window logger to write
        the log message to the Messagebox
        @param charstr: The log message which will be written.
        """
        stripped_string = string.strip()
        if stripped_string:
            self.append(stripped_string)
            self.verticalScrollBar().setValue(1e9)
