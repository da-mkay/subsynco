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

from gi.repository import Gtk
from os import path

from subsynco.gui.spin_entry import TimeEntry
from subsynco.media.subtitle import Subtitle
from subsynco.media.text_formatter import TextFormatter
from subsynco.utils.resources import Resources


class SubtitleDialog(object):

    def __init__(self, parent, subtitle, edit=False, allow_edit_time=True):
        self.subtitle = subtitle
        
        self._builder = Gtk.Builder()
        glade_file = Resources.find(path.join('data', 'gui', 'glade',
                                              'subtitle_dialog.glade'))
        self._builder.add_from_file(glade_file)
        self._builder.connect_signals(self)
        self._dialog = self._builder.get_object('subtitle_dialog')
        self._dialog.set_transient_for(parent)
        grid_main = self._builder.get_object('grid_main')
        
        self._txt_text = self._builder.get_object('txt_text')
        self._txt_text.get_buffer().set_text(self.subtitle.text)

        if edit:
            self._dialog.set_title(_('Edit subtitle'))
        else:
            self._dialog.set_title(_('Add subtitle'))

        self._adj_start = self._builder.get_object('adj_start')
        self._adj_end = self._builder.get_object('adj_end')
        self._adj_duration = self._builder.get_object('adj_duration')

        self._adj_start.set_value(self.subtitle.start)
        self._adj_end.set_value(self.subtitle.end)
        self._adj_duration.set_value(self.subtitle.end - self.subtitle.start)

        if allow_edit_time:
            self._time_start = TimeEntry()
            self._time_start.set_adjustment(self._adj_start)
            grid_main.attach(self._time_start, 1, 0, 1, 1)
            self._time_start.show()

            self._time_end = TimeEntry()
            self._time_end.set_adjustment(self._adj_end)
            grid_main.attach(self._time_end, 1, 1, 1, 1)
            self._time_end.show()

            self._time_duration = TimeEntry()
            self._time_duration.set_adjustment(self._adj_duration)
            grid_main.attach(self._time_duration, 1, 2, 1, 1)
            self._time_duration.show()
        else:
            self._builder.get_object('lbl_duration').set_visible(False)
            self._builder.get_object('lbl_start').set_visible(False)
            self._builder.get_object('lbl_end').set_visible(False)

        self._text_formatter = TextFormatter()

    def run(self):
        res = self._dialog.run()
        if res == Gtk.ResponseType.OK:
            self.subtitle.start = self._adj_start.get_value()
            self.subtitle.end = self._adj_end.get_value()
            buf = self._txt_text.get_buffer()
            start_iter = buf.get_start_iter()
            end_iter = buf.get_end_iter()
            self.subtitle.text = self._text_formatter.fix_format(
                                       buf.get_text(start_iter, end_iter, True))
        return res

    def destroy_dialog(self):
        return self._dialog.destroy()
    
    def _on_adj_duration_value_changed(self, adj):
        end = self._adj_start.get_value() + self._adj_duration.get_value()
        self._adj_end.set_value(end)
    
    def _on_adj_end_value_changed(self, adj):
        start = self._adj_start.get_value()
        end = self._adj_end.get_value()
        if end < start:
            self._adj_end.set_value(start)
        else:
            self._adj_duration.set_value(end - start)
    
    def _on_adj_start_value_changed(self, adj):
        start = self._adj_start.get_value()
        end = self._adj_end.get_value()
        if end < start:
            self._adj_end.set_value(start)
        else:
            self._adj_duration.set_value(end - start)

