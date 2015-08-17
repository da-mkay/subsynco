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

import bisect
import codecs
import re
import sys
from subsynco.utils.textfile import TextFile
from subsynco.utils.time import Time


class SubtitleFile(object):
    @staticmethod
    def load_srt(path, encoding):
        return SrtFile(path).load(encoding)

    @staticmethod
    def save_srt(path, subtitle_list):
        SrtFile(path).save(subtitle_list)


class SrtFile(object):
    def __init__(self, path):
        self._path = path
        # pre-compile regular expressions
        self._re_id = re.compile(r'\d+$')
        self._re_time = re.compile(r'(\d{2}):([0-5]\d):([0-5]\d),(\d{3}) --> '
            r'(\d{2}):([0-5]\d):([0-5]\d),(\d{3})'
            r'( X1:(\d+) X2:(\d+) Y1:(\d+) Y2:(\d+))?$')

    def load(self, enc):
        subtitle_list = SubtitleList()
        with codecs.open(self._path, 'r', encoding=enc) as f:
            text = f.read().encode('utf-8')
            i = 0
            lines = re.split(r'\r?\n', text)
            while i<len(lines):
                i, subtitle = self._get_next_sub(lines, i)
                subtitle_list.add_subtitle(subtitle)
            return subtitle_list
            
    def _get_next_sub(self, lines, i):
        l = lines[i].strip()
        if (self._re_id.match(l) is None):
            raise ValueError(_('Invalid id line ("{0}")').format(
                                                             l.decode('utf-8')))
        id_ = int(l)

        if (i+1 >= len(lines)):
            raise ValueError(_('Missing timestamp line'))
        l = lines[i+1].strip()
        time_match = self._re_time.match(l)
        if (time_match is None):
            raise ValueError(_('Invalid timestamp line ("{0}")').format(
                                                             l.decode('utf-8')))
        # TODO handle optional coordinates (X1, X2, Y1, Y2)
        if (time_match.group(9) is not None):
            raise NotImplementedError(
                              _('Coordinates found (currently not supported)!'))
        start = Time.millis_from_strs(time_match.group(1), time_match.group(2),
                                   time_match.group(3), time_match.group(4))
        end = Time.millis_from_strs(time_match.group(5), time_match.group(6),
                                   time_match.group(7), time_match.group(8))

        text = ''
        j = i+2
        while True:
            if (j >= len(lines)):
                raise ValueError(_('Missing text line'))
            text += lines[j] + '\r\n'
            j += 1
            if (lines[j].strip() == ''):
                break
        
        # skip trailing empty lines
        while j<len(lines):
            if (lines[j]!=''):
                break
            j += 1

        return (j, Subtitle(start, end, text.strip(), id_))
    
    def save(self, subtitle_list):
        # TODO maybe support other encodings for destination file
        # TODO handle optional coordinates (X1, X2, Y1, Y2)
        with codecs.open(self._path, 'w', encoding='utf8') as f:
            sub_counter = 0
            for subtitle in subtitle_list:
                sub_counter += 1
                sub = '{0}\r\n{1} --> {2}\r\n{3}\r\n\r\n'.format(
                    sub_counter,
                    Time.format(subtitle.start, True),
                    Time.format(subtitle.end, True),
                    subtitle.text
                )
                f.write(sub.decode('utf-8'))


class SubtitleList(object):
   
    def __init__(self):
        self._subtitles = []

    def add_subtitle(self, subtitle):
        i = bisect.bisect(self._subtitles, subtitle)
        self._subtitles.insert(i, subtitle)
        return i

    def remove_subtitle(self, i):
        self._subtitles.pop(i)

    def get_subtitle(self, millis):
        # Subtitles are sorted at first by their start-time and then by
        # their end-time. Therefore bisect_left returns ...
        #  ... the index of a subtitle with a start-time of `millis`.
        #  ... the index of a subtitle that is to the right of a
        #      subtitle with a start-time lower than `millis`.
        #  ... an index that equals the number of subtitles.
        #  ... 0.
        # So the subtitle at the index returned by bisect_left may not
        # be the wanted subtitle. We still need to check the end-time
        # to be sure that `millis` is between start- and end-time.
        # And even then we need to check the preceding subtitles to
        # get the first matching subtitle (necessary because we may have
        # overlapping subtitles.
        i = bisect.bisect_left(self._subtitles, Subtitle(millis, millis))
        e = None
        e_i = -1
        if (i >= len(self._subtitles)):
            i = len(self._subtitles) - 1
        # Look left until a non-matching subtitle is found.
        while (i>=0):
            tmp = self._subtitles[i]
            if (millis >= tmp.end):
                break
            if (tmp.start <= millis):
                e = tmp
                e_i = i
            i -= 1
        return e_i, e

    def get_next_closest_subtitle(self, millis):
        """Get the subtitle that fits to millis or a subtitle that
        follows millis.

        May return the same subtitle which is returned by get_subtitle.
        However if no subtitle was found that fits to millis the next
        subtitle that follows after millis is returned. If there is no
        such subtitle then the last subtitle in the list is returned.
        """
        i = bisect.bisect_left(self._subtitles, Subtitle(millis, millis))
        if (i >= len(self._subtitles)):
            i = len(self._subtitles) - 1
        e = None if i<0 else self._subtitles[i]
        e_i = -1 if e is None else i
        while (i>=0):
            tmp = self._subtitles[i]
            if (millis >= tmp.end):
                break
            e = tmp
            e_i = i
            i -= 1
        return e_i, e

    def move_subtitle(self, i, millis):
        subtitle = self._subtitles[i]
        # adjust possible negative results
        new_start = 0 if -millis >= subtitle.start else subtitle.start + millis
        new_end = 0 if -millis >= subtitle.end else subtitle.end + millis
        if (subtitle.start == new_start and subtitle.end == new_end):
            # unchanged timings
            return i
        # determine new position of modified subtitle
        dummy_subtitle = Subtitle(new_start, new_end)
        new_i = bisect.bisect(self._subtitles, dummy_subtitle)
        if (new_i < i):
            # Subtitle moves left.
            # Example: from 2 to 1     Order of ins/pop is important!
            # pre:     a b X c         This would fail:
            # pop(2):  a b c           ins(1):  a X b X c
            # ins(1):  a X b c         pop(2):  a X X c
            self._subtitles.pop(i)
            self._subtitles.insert(new_i, subtitle)
        elif (new_i > i+1):
            # Subtitle moves right.
            # Because we remove the item at i (<= new_i) we need to add
            # the new item at new_i-1 instead of new_i.
            new_i -= 1
            self._subtitles.pop(i)
            self._subtitles.insert(new_i, subtitle)
        else:
            # Subtitle does not move.
            new_i = i
        subtitle.start = new_start
        subtitle.end = new_end
        return new_i
    
    def change_fps(self, fps_from, fps_to):
        if fps_from == fps_to:
            return 0
        # We do not need to use self.move_subtitle! Since we modify the
        # timestamps of each single subtitle the order of the subtitles
        # after the call to change_fps will be the same as before the
        # call.
        fpms_from = fps_from / 1000
        fpms_to = fps_to / 1000
        for sub in self:
            start_new = self._convert_millis(sub.start, fpms_from, fpms_to)
            end_new = self._convert_millis(sub.end, fpms_from, fpms_to)
            sub.start = start_new
            sub.end = end_new
        return self.__len__()

    def _convert_millis(self, millis, fpms_from, fpms_to):
        frame_old = millis * fpms_from
        millis_new = frame_old / fpms_to
        return millis_new

    def __iter__(self):
        return iter(self._subtitles)

    def __getitem__(self, key):
        return self._subtitles[key]

    def __len__(self):
        return len(self._subtitles)


class Subtitle(object):

    def __init__(self, start, end, text='', orig_id=None):
        self.orig_id = orig_id
        if orig_id:
            self.orig_start = start
            self.orig_end = end
            self.orig_text = text
        else:
            self.orig_start = None
            self.orig_end = None
            self.orig_text = None
        self.start = start
        self.end = end
        self.text = text

    # __lt__, __eq__ handle overlapping subtitles:
    #
    # e1: |----|            |----|          |--------|      |---|
    # e2:      |---|            |------|        |--|        |------|
    #
    #     ================ time ================>>>

    def __lt__(self, other):
        if self.start == other.start:
            return self.end < other.end
        return self.start < other.start

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end

    def __repr__(self):
        return '<{}, {}, {}>'.format(self.start, self.end, self.text)


if __name__ == '__main__':
    sub = SubtitleList()
    sub.add_subtitle(Subtitle(1000, 2000, 'Test1'))
    sub.add_subtitle(Subtitle(3000, 4000, 'Test2'))

    print(len(sub))
    print(sub[0])
    print(sub.get_subtitle(2500))
    print(sub.get_next_closest_subtitle(0))

    print('Reading subtitle...')
    SrtFile('example.srt').load('latin1')
