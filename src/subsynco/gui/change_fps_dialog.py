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

from subsynco.gui.spin_entry import SpinEntry
from subsynco.utils.resources import Resources


class ChangeFpsDialog(object):

    def __init__(self, parent):
        self._builder = Gtk.Builder()
        glade_file = Resources.find(path.join('data', 'gui', 'glade',
                                              'change_fps_dialog.glade'))
        self._builder.add_from_file(glade_file)
        self._dialog = self._builder.get_object('change_fps_dialog')
        self._dialog.set_transient_for(parent)
        grid_main = self._builder.get_object('grid_main')
        
        self._adj_fps_from = self._builder.get_object('adj_fps_from')
        self._adj_fps_to = self._builder.get_object('adj_fps_to')

        self.fps_from = 23.976216
        self.fps_to = 25.000

        self._adj_fps_from.set_value(self.fps_from)
        self._adj_fps_to.set_value(self.fps_to)

        self._spin_fps_from = SpinEntry()
        self._spin_fps_from.set_adjustment(self._adj_fps_from)
        grid_main.attach(self._spin_fps_from, 1, 0, 1, 1)
        self._spin_fps_from.show()

        self._spin_fps_to = SpinEntry()
        self._spin_fps_to.set_adjustment(self._adj_fps_to)
        self._spin_fps_to.set_hexpand(True)
        grid_main.attach(self._spin_fps_to, 1, 1, 1, 1)
        self._spin_fps_to.show()

    def run(self):
        res = self._dialog.run()
        if res == Gtk.ResponseType.OK:
            self.fps_to = self._adj_fps_to.get_value()
            self.fps_from = self._adj_fps_from.get_value()
        return res

    def destroy_dialog(self):
        return self._dialog.destroy()
    

