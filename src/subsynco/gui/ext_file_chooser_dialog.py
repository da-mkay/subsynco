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
from operator import itemgetter
from os import path

from subsynco.utils.textfile import TextFile
from subsynco.utils.resources import Resources


class ExtFileChooserDialog(object):

    def __init__(self, parent, title, enable_encoding_selection=False):
        self._enable_encoding_selection = enable_encoding_selection
        self.encoding = None
        
        self._builder = Gtk.Builder()
        glade_file = Resources.find(path.join('data', 'gui', 'glade',
                                              'ext_file_chooser_dialog.glade'))
        self._builder.add_from_file(glade_file)
        self._dialog = self._builder.get_object('filechooserdialog')
        self._dialog.set_transient_for(parent)
        self._dialog.set_title(title)
        self._builder.connect_signals(self)
        self._box_encoding = self._builder.get_object('box_encoding')
        self._combo_encoding = self._builder.get_object('combo_encoding')
        self._store_encoding = self._builder.get_object('store_encoding')
        
        if not enable_encoding_selection:
            self._box_encoding.hide()
        
        self._combo_encoding.set_row_separator_func(self._is_separator, None)
        
        encodings = sorted(TextFile.get_available_encodings_with_title(),
                                                            key=itemgetter(0))
        
        self._store_encoding.append([_('Detect automatically'), None])
        self._store_encoding.append(['-', None])
        for encoding in encodings:
            self._store_encoding.append(encoding)
            
        self._combo_encoding.set_active(0)
    
    def run(self):
        return self._dialog.run()

    def destroy_dialog(self):
        return self._dialog.destroy()

    def _on_combo_encoding_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            self.encoding = model[tree_iter][1]
    
    def _is_separator(self, model, tree_iter, data):
        item_text = model[tree_iter][0]
        return item_text == '-'
    
    def set_current_folder(self, folder):
        self._dialog.set_current_folder(folder)
    
    def add_filter(self, filter_):
        self._dialog.add_filter(filter_)
    
    def get_filename(self):
        return self._dialog.get_filename()
    
    def get_uri(self):
        return self._dialog.get_uri()
    
    
