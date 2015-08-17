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

from __future__ import print_function
import sys

class Logger(object):
    @staticmethod
    def info(msg):
        print(_('Info - {}').format(msg).encode('utf-8'))

    @staticmethod
    def warn(msg):
        print(_('Warning - {}').format(msg).encode('utf-8'), file=sys.stderr)

    @staticmethod
    def error(msg):
        print(_('Error - {}').format(msg).encode('utf-8'), file=sys.stderr)

