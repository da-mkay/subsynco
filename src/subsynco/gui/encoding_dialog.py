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


class EncodingDialog(object):

    def __init__(self, parent, text):
        self._text = text
        self.encoding = None
        
        self._builder = Gtk.Builder()
        glade_file = Resources.find(path.join('data', 'gui', 'glade',
                                              'encoding_dialog.glade'))
        self._builder.add_from_file(glade_file)
        self._dialog = self._builder.get_object('encoding_dialog')
        self._dialog.set_transient_for(parent)
        self._builder.connect_signals(self)
        self._text_content = self._builder.get_object('text_content')
        self._store_encoding = self._builder.get_object('store_encoding')
        
        encodings = sorted(TextFile.get_available_encodings_with_title(),
                           key=itemgetter(0))
        
        # Test which encoding can be used to decode the text-file and
        # add those encodings to the combo box.
        for encoding in encodings:
            try:
                self._text.decode(encoding[1])
                # decode successfull --> add to list
                self._store_encoding.append(encoding)
            except UnicodeDecodeError:
                continue
    
    def run(self):
        return self._dialog.run()

    def destroy_dialog(self):
        return self._dialog.destroy()

    def _on_combo_encoding_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            self.encoding = model[tree_iter][:2][1]
            decoded = self._text.decode(self.encoding).encode('utf-8')
            self._text_content.get_buffer().set_text(decoded)

    @staticmethod
    def detect_textfile_encoding(parent, file_):
        """Try to automatically detect the character encoding of the
        specified file. If that fails show a dialog to force the user
        to select the correct character encoding.
        """
        encoding = TextFile.detect_encoding(file_)
        if encoding is None:
            enc_dlg = EncodingDialog(parent, open(file_).read())
            res = enc_dlg.run()
            enc_dlg.destroy_dialog()
            if res == Gtk.ResponseType.OK and enc_dlg.encoding is not None:
                encoding = enc_dlg.encoding
            else:
                return None
        return encoding
