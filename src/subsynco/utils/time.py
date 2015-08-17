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

import re

class Time(object):
    @staticmethod
    def format(millis, comma=False):
        millis = long(millis)
        pre = ''
        if millis < 0:
            pre = '-'
            millis = - millis
        hours = millis / 3600000
        millis -= hours * 3600000
        minutes = millis / 60000
        millis -= minutes * 60000
        seconds = millis / 1000
        millis = millis - seconds * 1000
        if comma:
            time_format = '{0}{1:0>2}:{2:0>2}:{3:0>2},{4:0>3}'
        else:
            time_format = '{0}{1:0>2}:{2:0>2}:{3:0>2}.{4:0>3}'
        return time_format.format(pre, hours, minutes, seconds, millis)
    
    @staticmethod
    def millis_from_str(text):
        regex = re.compile(r'^([+-]?)(\d{2}):([0-5]\d):([0-5]\d)\.(\d{3})$')
        match = regex.match(text)
        if (match is None):
            raise TypeError(_('"{}" is not a time. Failed to determine number '
                            'of milliseconds.').format(text))
        millis = Time.millis_from_strs(match.group(2), match.group(3),
                                       match.group(4), match.group(5))
        millis = (- millis) if match.group(1) == '-' else millis
        return millis

    @staticmethod
    def millis_from_strs(h, m, s, ms):
        return long(ms) + long(s)*1000 + long(m)*60000 + long(h)*3600000

