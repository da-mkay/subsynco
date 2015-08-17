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

from gi.repository import GdkPixbuf
from gi.repository import Gtk
from os import path

from subsynco.utils.resources import Resources


class AboutDialog(object):

    def __init__(self, parent):
        self._builder = Gtk.Builder()
        gui_folder = Resources.find(path.join('data', 'gui'))
        self._builder.add_from_file(path.join(gui_folder, 'glade',
                                              'about_dialog.glade'))
        self._dialog = self._builder.get_object('about_dialog')
        logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file(path.join(gui_folder,
                                                     'logo', 'logo-about.png'))
        self._dialog.set_logo(logo_pixbuf)
        self._dialog.set_transient_for(parent)
    
    def run(self):
        return self._dialog.run()

    def destroy_dialog(self):
        return self._dialog.destroy()
