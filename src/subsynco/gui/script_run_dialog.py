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
from gi.repository import GLib
from os import path

from subsynco.gui.encoding_dialog import EncodingDialog
from subsynco.gui.glib_helpers import GLibHelpers
from subsynco.utils.resources import Resources
from subsynco.utils.thread_helpers import ThreadHelpers
from subsynco.media.submod import Submod
from subsynco.media.subtitle import SubtitleFile


class ScriptRunDialog(object):
    STEP_LOADING_SUBMOD = 0
    STEP_LOADING_SUBTITLE = 1
    STEP_RUNNING_SUBMOD = 2
    STEP_SAVING_SUBTITLE = 3
    STEP_DONE = 4

    def __init__(self, parent, script_file):
        self._script_file = script_file
        self._submod = None
        
        builder = Gtk.Builder()
        glade_file = Resources.find(path.join('data', 'gui', 'glade',
                                              'script_run_dialog.glade'))
        builder.add_from_file(glade_file)
        self._dialog = builder.get_object('script_run_dialog')
        self._dialog.set_transient_for(parent)
        builder.connect_signals(self)

        self._spin_loading_submod = builder.get_object('spin_loading_submod')
        self._img_loading_submod = builder.get_object('img_loading_submod')
        self._spin_loading_subtitle = builder.get_object(
                                                        'spin_loading_subtitle')
        self._img_loading_subtitle = builder.get_object('img_loading_subtitle')
        self._spin_running_submod = builder.get_object('spin_running_submod')
        self._img_running_submod = builder.get_object('img_running_submod')
        self._spin_saving_subtitle = builder.get_object('spin_saving_subtitle')
        self._img_saving_subtitle = builder.get_object('img_saving_subtitle')
        self._scroll_log = builder.get_object('scroll_log')
        self._txt_log = builder.get_object('txt_log')
        self._btn_close = builder.get_object('btn_close')
        
        self._step_icons = [
            self._spin_loading_submod, self._img_loading_submod,
            self._spin_loading_subtitle, self._img_loading_subtitle,
            self._spin_running_submod, self._img_running_submod,
            self._spin_saving_subtitle, self._img_saving_subtitle
        ]
    
    def run(self):
        return self._dialog.run()

    def destroy_dialog(self):
        return self._dialog.destroy()

    def _on_dialog_show(self, widget):
        encoding = EncodingDialog.detect_textfile_encoding(self._dialog,
                                                           self._script_file)
        if encoding is None:
            self._error(self.STEP_LOADING_SUBMOD,
                        _('Could not determine encoding of Submod-script!'))
            return
        self._submod = Submod()
        self._load_script(encoding)
    
    @ThreadHelpers.run_in_thread
    def _load_script(self, encoding):
        """Try to load the Submod-script in a new thread.
        
        Then continue with the next step (detect subtitle encoding).
        """
        try:
            self._submod.load(self._script_file, encoding)
        except Exception as e:
            self._error(self.STEP_LOADING_SUBMOD, unicode(e))
            return
        self._detect_subtitle_encoding()

    @GLibHelpers.idle_add
    def _detect_subtitle_encoding(self):
        """Try to detect the encoding of the subtitle file if it's not
        set in the submod-script.
        
        This is done in the Gtk-thread because a dialog may be shown to
        select the proper encoding if it can not be detected
        automatically.
        
        Then continue with the next step (load subtitle and run Submod-
        script).
        """
        self._show_step_icons(self.STEP_LOADING_SUBTITLE)
        # Generate path for subtitle based on script-directory and
        # subtitle filename from the script.
        subtitle_filename = self._submod.script['subtitle']['filename']
        dir_, script_filename = path.split(self._script_file)
        subtitle_file = path.join(dir_, subtitle_filename)
        if not path.isfile(subtitle_file):
            self._error(self.STEP_LOADING_SUBTITLE,
                 _('Could not find subtitle file "{}"!').format(subtitle_file))
            return
        encoding = None
        if 'encoding' in self._submod.script['subtitle']:
            encoding = self._submod.script['subtitle']['encoding']
        if encoding is None:
            encoding = EncodingDialog.detect_textfile_encoding(self._dialog,
                                                               subtitle_file)
        if encoding is None:
            self._error(self.STEP_LOADING_SUBTITLE,
                           _('Could not determine encoding of subtitle file!'))
            return
        self._load_subtitle_run_script(subtitle_file, encoding)
        
    def _load_subtitle(self, subtitle_file, encoding):
        subtitle_list = SubtitleFile.load_srt(subtitle_file, encoding)
        self._show_step_icons(self.STEP_RUNNING_SUBMOD)
        return subtitle_list
    
    @ThreadHelpers.run_in_thread
    def _load_subtitle_run_script(self, subtitle_file, encoding):
        """Try to run the Submod-script in a new thread.
        """
        try:
            subtitle_loader = lambda f: self._load_subtitle(f, encoding)
            subtitle_list = self._submod.run(subtitle_file, subtitle_loader)
        except Exception as e:
            # Maybe the subtitle-checksum was wrong. Then an Exception
            # is raised before the subtitle was loaded. In that case
            # _load_subtitle was not called and thus the
            # STEP_RUNNING_SUBMOD-icons are not shown yet.
            # NOTE: _load_subtitle may raise an Exception, too.
            self._show_step_icons(self.STEP_RUNNING_SUBMOD)
            self._error(self.STEP_RUNNING_SUBMOD, unicode(e))
            return
        # Script has run, now save the new subtitle list.
        self._show_step_icons(self.STEP_SAVING_SUBTITLE)
        dir_, __ = path.split(self._script_file)
        # Generate name for new subtitle file based on the name of the
        # old subtitle file. '_submod' will be added before the file
        # extension. If the file already exists a new filename is
        # generated (by adding '.1', '.2' .. before the extension)
        # until a non existing filename is found.
        subtitle_filename = self._submod.script['subtitle']['filename']
        name_parts = subtitle_filename.rsplit('.', 1)
        name_base = name_parts[0] + '_submod'
        ext = '.'+name_parts[1] if len(name_parts)==2 else ''
        new_subtitle_file = path.join(dir_, name_base + ext)
        c = 0
        while path.isfile(new_subtitle_file):
            c += 1
            new_subtitle_file = path.join(dir_, name_base + '.' + str(c) + ext)
        try:
            SubtitleFile.save_srt(new_subtitle_file, subtitle_list)
        except Exception as e:
            self._error(self.STEP_SAVING_SUBTITLE, unicode(e))
            return
        self._show_step_icons(self.STEP_DONE)
        GLib.idle_add(self._allow_close)

    @GLibHelpers.idle_add
    def _show_step_icons(self, step):
        """Hides the spinner and shows the success-icon of the previous
        step and shows the spinner for the given step.
        """
        offset = (step-1)*2
        self._step_icons[offset].hide()
        self._step_icons[offset+1].show()
        if offset+2<len(self._step_icons):
            self._step_icons[offset+2].show()

    @GLibHelpers.idle_add
    def _error(self, step, text):
        """Hide the spinner and show the error icon for the given step
        and show the log-view containing the error text.
        """
        spin, image = self._step_icons[step*2], self._step_icons[step*2+1]
        spin.hide()
        image.set_from_icon_name('gtk-dialog-error', Gtk.IconSize.BUTTON)
        image.show()
        self._set_log(text)
        self._allow_close()

    def _set_log(self, text):
        self._txt_log.get_buffer().set_text(text.encode('utf-8'))
        self._scroll_log.show()

    def _allow_close(self):
        self._btn_close.set_sensitive(True)



