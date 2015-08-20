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

import codecs
from subsynco.utils.textfile import TextFile


class CutsFile(object):
    @staticmethod
    def load_cutlist(path, encoding):
        return Cutlist(path).load(encoding)


class Cutlist(object):
    def __init__(self, path):
        self._path = path

    def load(self, enc):
        """Returns a list of cuts. Each cut is a tuple of three values
        in seconds: start, duration and cut position (sum of durations).
        Each cut specifies which part of the video is kept (not cut out).
        """
        cuts = []
        start = 0.0
        duration = 0.0
        cut_position = 0.0
        in_cut_section = False
        with codecs.open(self._path, 'r', encoding=enc) as f:
            for line in f:
                line = line.encode('utf-8').lower()
                if line.startswith('['):
                    if in_cut_section:
                        cuts.append((start, duration, cut_position))
                    start = 0.0
                    duration = 0.0
                    in_cut_section = False
                if line.startswith('[cut'):
                    in_cut_section = True
                elif in_cut_section and line.startswith('start='):
                    start = float(line[6:])*1000
                elif in_cut_section and line.startswith('duration='):
                    duration = float(line[9:])*1000
                    cut_position += duration
        if in_cut_section:
            cuts.append((start, duration, cut_position))
        return cuts

