#!/usr/bin/env python
'''
SubSynco - a tool for synchronizing subtitle files
Copyright (C) 2015  da-mkay

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
from os import path

class Resources(object):
    @staticmethod
    def find(file_):
        if getattr(sys, 'frozen', False):
            # The application is frozen by cx_Freeze (built for Windows)
            appdir = path.dirname(path.realpath(sys.executable))
        else:
            # The application is not frozen.
            appdir = path.dirname(path.realpath(path.join(__file__, '..')))

        return path.join(appdir, file_)
