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

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject
from gi.repository import Gst
from gi.repository import Gtk
# Required for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GstVideo

GObject.threads_init()
Gst.init(None)

import copy
import glob
import re
import urlparse
import urllib
from os import path
from subsynco.gui.about_dialog import AboutDialog
from subsynco.gui.change_fps_dialog import ChangeFpsDialog
from subsynco.gui.encoding_dialog import EncodingDialog
from subsynco.gui.ext_file_chooser_dialog import ExtFileChooserDialog
from subsynco.gui.format_check_dialog import FormatCheckDialog
from subsynco.gui.glib_helpers import GLibHelpers
from subsynco.gui.script_run_dialog import ScriptRunDialog
from subsynco.gui.subtitle_dialog import SubtitleDialog
from subsynco.gst.player import MultimediaPlayer
from subsynco.gui.spin_entry import TimeEntry
from subsynco.gui.subtitle_list_tree_model import SubtitleListTreeModel
from subsynco.media.cuts import CutsFile
from subsynco.media.subtitle import Subtitle, SubtitleList
from subsynco.media.subtitle import SubtitleFile
from subsynco.media.submod import Submod
from subsynco.media.text_formatter import TextFormatter
from subsynco.utils.logger import Logger
from subsynco.utils.resources import Resources
from subsynco.utils.settings import Settings
from subsynco.utils.time import Time


class MainWindow(object):

    def __init__(self):
        # Set default icons for all windows.
        # TODO Use name of icons and gtk-update-icon-cache instead of
        #      specifying each file. But only if it works on all
        #      platforms.
        theme_folder = Resources.find(path.join('data', 'gui', 'icons', 'hicolor'))
        get_app_pixbuf = lambda (size, ext): GdkPixbuf.Pixbuf.new_from_file(
                       path.join(theme_folder, size, 'apps', 'subsynco.' + ext))
        app_icons = map(get_app_pixbuf, [('16x16', 'png'), ('22x22', 'png'),
                                         ('32x32', 'png'), ('scalable', 'svg')])
        Gtk.Window.set_default_icon_list(app_icons)
    
        self._builder = Gtk.Builder()
        self._builder.add_from_file(Resources.find(path.join('data', 'gui' ,'glade',
                                              'main_window.glade')))
        self._builder.connect_signals(self)

        self._window = self._builder.get_object('main_window')
        self._lbl_position = self._builder.get_object('lbl_position')
        self._adj_position = self._builder.get_object('adj_position')
        self._scale_position = self._builder.get_object('scale_position')
        self._adj_position.set_upper(0)

        self._video = self._builder.get_object('video')
        self._player = MultimediaPlayer(self._video)
        self._player.set_position_changed_callback(
                                               self._on_player_position_changed)
        self._player.set_duration_changed_callback(
                                               self._on_player_duration_changed)
        
        # The start/end time should be displayed as hh:mm:ss.iii
        cellrenderer_start = self._builder.get_object('cellrenderer_start')
        column_start = self._builder.get_object('column_start')
        column_start.set_cell_data_func(cellrenderer_start,
                                        self._format_start_time_column)

        cellrenderer_end = self._builder.get_object('cellrenderer_end')
        column_end = self._builder.get_object('column_end')
        column_end.set_cell_data_func(cellrenderer_end,
                                      self._format_end_time_column)

        self._tree_subtitles = self._builder.get_object('tree_subtitles')
        self._tree_subtitles.set_property('rules-hint', True)
        self._selection_subtitle = self._builder.get_object(
                                                           'selection_subtitle')

        self._subtitle_list_model = None
        
        self._adj_seek = self._builder.get_object('adj_seek')
        self._adj_seek.set_value(Settings().get(self, 'seek_by', 100))
        self._update_seek_by()
        self._adj_move = self._builder.get_object('adj_move')
        self._adj_move.set_value(Settings().get(self, 'move_by', 100))
        self._move_by = self._adj_move.get_value()
        self._time_seek = TimeEntry()
        self._time_seek.set_adjustment(self._adj_seek)
        self._time_move = TimeEntry()
        self._time_move.set_adjustment(self._adj_move)
        box_settings = self._builder.get_object('box_settings')
        box_settings.add(self._time_seek)
        box_settings.add(self._time_move)
        box_settings.reorder_child(self._time_seek, 1)
        
        self._move_subsequent = Settings().get(self, 'move_subsequent', True)
        self._builder.get_object('check_movesubsequent').set_active(
                                                          self._move_subsequent)

        self._autoscroll = Settings().get(self, 'autoscroll', True)
        self._builder.get_object('check_autoscroll').set_active(
                                                               self._autoscroll)
        self._submod = None
        self._cuts = None
        self._subtitle_file = None
        self._subtitle_filename = None
        self._subtitle_encoding = None
        self._subtitle_unsaved = False
        self._text_formatter = TextFormatter()

    def show(self):
        self._window.show_all()

    def _on_player_position_changed(self, nanos):
        # The player's position has changed. So we update the GUI. For
        # example we show the current position and may scroll to the 
        # active subtitle in the list.
        if self._subtitle_list_model is not None:
            subtitle_i, __ = (self._subtitle_list_model.data.
                                     get_next_closest_subtitle(nanos / 1000000))
        
        @GLibHelpers.idle_add
        def update_gui():
            self._lbl_position.set_text(self._format_player_time_nanos(nanos))
            self._adj_position.set_value(nanos)
            if (self._subtitle_list_model is not None and
                    (self._autoscroll and subtitle_i >= 0)):
                path, __ = self._subtitle_list_model.get_path_iter_by_row(
                                                                    subtitle_i)
                self._tree_subtitles.scroll_to_cell(path, use_align=True,
                                                    row_align=0.5)
        update_gui()

    @GLibHelpers.idle_add
    def _on_player_duration_changed(self, nanos):
        self._adj_position.set_upper(nanos)

    def _on_adj_position_value_changed(self, adj):
        self._player.seek(long(self._adj_position.get_value()))

    def _on_delete_window(self, *args):
        return not self._try_quit()

    def _try_quit(self):
        """Try to quit the program.
        
        If the current subtitle is unsaved a dialog will be shown to
        ask the user whether he really wants to quit.
        
        Returns False if program was not quit.
        """
        quit = True
        if self._subtitle_unsaved:
            dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.INFO,
                                 Gtk.ButtonsType.NONE,
                                 _('You made changes that were not saved yet!'))
            dialog.add_buttons(_('Close without saving'),
                               Gtk.ResponseType.CLOSE,
                               Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                               Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            res = dialog.run()
            dialog.destroy()
            if res == Gtk.ResponseType.OK:
                self._save_current_subtitle()
            elif res == Gtk.ResponseType.CANCEL:
                quit = False
        if quit:
            self._player.stop()
            Gtk.main_quit()
            return True
        return False

    def _on_btn_play_clicked(self, button):
        self._player.play()

    def _on_btn_pause_clicked(self, button):
        self._player.pause()

    def _on_btn_seek_forward_clicked(self, button):
        self._player.seek_relative(self._seek_by)

    def _on_btn_seek_backward_clicked(self, button):
        self._player.seek_relative(- self._seek_by)

    def _on_tree_key_press(self, widget, event):
        if (event.keyval == Gdk.KEY_Left or event.keyval == Gdk.KEY_Right):
            self._move_selected_sub(event.keyval == Gdk.KEY_Right)
            self._tree_subtitles.emit_stop_by_name('key-press-event')

    def _on_adj_seek_value_changed(self, adj):
        Settings().set(self, 'seek_by', adj.get_value())
        self._update_seek_by()
        
    def _on_adj_move_value_changed(self, adj):
        Settings().set(self, 'move_by', adj.get_value())
        self._move_by = long(adj.get_value())

    def _on_check_autoscroll_toggled(self, check):
        self._autoscroll = check.get_active()
        Settings().set(self, 'autoscroll', self._autoscroll)
    
    def _on_check_movesubsequent_toggled(self, check):
        self._move_subsequent = check.get_active()
        Settings().set(self, 'move_subsequent', self._move_subsequent)

    def _on_btn_move_left_clicked(self, btn):
        self._move_selected_sub(False)

    def _on_btn_move_right_clicked(self, btn):
        self._move_selected_sub(True)
    
    def _on_btn_move_to_position_clicked(self, btn):
        # Move the selected subtitle to the player's current position.
        __, iter_ = self._selection_subtitle.get_selected()
        if iter_ != None:
            millis = long(self._adj_position.get_value()) / 1000000
            path = self._subtitle_list_model.move_subtitle_to(iter_, millis,
                                                          self._move_subsequent)
            self._select_subtitle(path)        
    
    def _on_btn_open_subtitle_clicked(self, btn):
        filechooser = self._new_open_filechooser(
                                       _('Please choose a subtitle file'), True)
        folder = Settings().get(self, 'subtitle_folder')
        if folder is not None:
            filechooser.set_current_folder(folder)
        filter_subtitle = Gtk.FileFilter()
        filter_subtitle.set_name(_('SubRip subtitles')+' (*.srt)')
        filter_subtitle.add_pattern('*.srt')
        filechooser.add_filter(filter_subtitle)
        res = filechooser.run()
        file_ = filechooser.get_filename()
        filechooser.destroy_dialog()
        if res == Gtk.ResponseType.OK and path.isfile(file_):
            dir_, filename = path.split(file_)
            Settings().set(self, 'subtitle_folder', dir_)
            self.open_subtitle(file_, filechooser.encoding)

    def _on_btn_open_video_clicked(self, btn):
        filechooser = self._new_open_filechooser(_('Please choose video file'))
        folder = Settings().get(self, 'video_folder')
        if folder is not None:
            filechooser.set_current_folder(folder)
        filter_subtitle = Gtk.FileFilter()
        filter_subtitle.set_name(_('Video files') +
                                       u' (*.avi, *.xvid, *.mp4, *.mkv, *.mpg)')
        filter_subtitle.add_pattern('*.avi')
        filter_subtitle.add_pattern('*.xvid')
        filter_subtitle.add_pattern('*.mp4')
        filter_subtitle.add_pattern('*.mkv')
        filter_subtitle.add_pattern('*.mpg')
        filechooser.add_filter(filter_subtitle)
        res = filechooser.run()
        file_ = filechooser.get_filename()
        file_uri = filechooser.get_uri()
        filechooser.destroy_dialog()
        if res == Gtk.ResponseType.OK and path.isfile(file_):
            dir_, filename = path.split(file_)
            Settings().set(self, 'video_folder', dir_)
            self._open_video(file_uri)

    def _on_btn_open_cuts_clicked(self, btn):
        filechooser = self._new_open_filechooser(
                                        _('Please choose a cutlist file'), True)
        folder = Settings().get(self, 'cuts_folder')
        if folder is not None:
            filechooser.set_current_folder(folder)
        filter_subtitle = Gtk.FileFilter()
        filter_subtitle.set_name(_('Cutlist files')+' (*.cutlist)')
        filter_subtitle.add_pattern('*.cutlist')
        filechooser.add_filter(filter_subtitle)
        res = filechooser.run()
        file_ = filechooser.get_filename()
        filechooser.destroy_dialog()
        if res == Gtk.ResponseType.OK and path.isfile(file_):
            dir_, filename = path.split(file_)
            Settings().set(self, 'cuts_folder', dir_)
            self._open_cutlist(file_, filechooser.encoding)

    def _on_btn_save_clicked(self, btn):
        self._save_current_subtitle()

    def _on_tree_subtitles_row_activated(self, tree, path, column):
        """A subtitle was double clicked or a subtitle was selected
        and the Return key etc. was pressed.
        
        Seek video to the subtitle's start-position.
        """
        iter_ = self._subtitle_list_model.get_iter(path)
        subtitle = self._subtitle_list_model.get_item(iter_)
        self._player.seek(long(subtitle.start * 1000000))

    def _update_seek_by(self):
        self._seek_by = long(self._adj_seek.get_value()) * 1000000
        self._adj_position.set_step_increment(self._seek_by)
        self._adj_position.set_page_increment(self._seek_by * 2)

    def _save_current_subtitle(self):
        if self._subtitle_file is not None:
            SubtitleFile.save_srt(self._subtitle_file,
                                                 self._subtitle_list_model.data)
            self._set_unsaved(False)

    def _new_open_filechooser(self, title, enable_encoding_selection=False):
        return ExtFileChooserDialog(self._window, title,
                                    enable_encoding_selection)

    def _set_unsaved(self, unsaved):
        # Update the window title if the unsaved-status has changed or
        # the file is unsaved (for example if it was just opened).
        update = not unsaved or self._subtitle_unsaved != unsaved
        self._subtitle_unsaved = unsaved
        if update:
            self._update_window_title()
            
    def _update_window_title(self):
        title = ''
        if self._subtitle_filename is not None:
            if self._subtitle_unsaved:
                title += '*'
            dir_, filename = path.split(self._subtitle_file)
            title += filename + ' - '
        self._window.set_title(title + 'SubSynco')

    def open_subtitle(self, subtitle_file, encoding=None):
        if encoding is None:
            encoding = EncodingDialog.detect_textfile_encoding(self._window,
                                                               subtitle_file)
        if encoding is None:
            return
        
        Logger.info(_('Using encoding {} for subtitle').format(encoding))

        try:
            subtitle_list = SubtitleFile.load_srt(subtitle_file, encoding)
        except Exception as e:
            dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.ERROR,
                         Gtk.ButtonsType.OK,
                         _('Failed to load subtitle file:\n{}!').format(e))
            dialog.run()
            dialog.destroy()
            return
        
        self._submod = Submod(subtitle_file, copy.deepcopy(subtitle_list),
                              encoding)
        self._cuts = None
        
        self._subtitle_file = subtitle_file
        dir_, filename = path.split(self._subtitle_file)
        self._subtitle_filename = filename
        self._subtitle_encoding = encoding
        self._set_unsaved(False)
        
        # Check for invalid syntax, for example missing end tags
        self._check_and_fix_subtitle_format(subtitle_list)
        
        self._subtitle_list_model = SubtitleListTreeModel(subtitle_list,
                                                      self._on_subtitle_changed)
        self._tree_subtitles.set_model(self._subtitle_list_model)
        self._player.set_subtitle_list(subtitle_list)
        
        # Try to find video/cutlist file for the subtitle and
        # autoamtically open it
        find_pattern = path.join(dir_, self._remove_extension(filename)+'.*')
        files = glob.glob(find_pattern)
        
        self._player.set_file(None)
        self._scale_position.clear_marks()
        
        video_found = False
        cutlist_found = False
        for file_ in files:
            if (not video_found and
                    re.match(r'.*(avi|xvid|mp4|mkv|mpg)$', file_)):
                video_found = True
                file_uri = urlparse.urljoin('file:', urllib.pathname2url(file_))
                self._open_video(file_uri)
            if not cutlist_found and file_.endswith('.cutlist'):
                cutlist_found = True
                self._open_cutlist(file_)
        
    def _open_video(self, video_file_uri):
        self._player.set_file(video_file_uri)
        self._player.pause()

    def _open_cutlist(self, cutlist_file, encoding=None):
        self._scale_position.clear_marks()
        if encoding is None:
            encoding = EncodingDialog.detect_textfile_encoding(self._window,
                                                               cutlist_file)
        if encoding is None:
            return
        try:
            self._cuts = CutsFile.load_cutlist(cutlist_file, encoding)
            # We don't need to mark the last cut because it will be at
            # the end of the video.
            cuts = self._cuts[:-1]
        except Exception as e:
            dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.ERROR,
                          Gtk.ButtonsType.OK,
                          _('Failed to load cutlist file:\n{}!').format(
                                                                     e.args[0]))
            dialog.run()
            dialog.destroy()
            return
        for start, duration, cut in cuts:
            cut_nanos = cut*1000000
            self._scale_position.add_mark(cut_nanos, Gtk.PositionType.TOP,
                        '<span foreground="white" background="blue"> X </span>')

    def _check_and_fix_subtitle_format(self, subtitle_list):
        """Check if the format-syntax in each subtitle is correct.
        
        For example '<i>Missing end tag' is invalid and must be
        '<i>...</i>'. If any invalid syntax is detected the subtitle is
        automatically corrected. Then a dialog is shown so that the user
        can verify the auto-corrected subtitles.
        """
        # holds the subs that were fixed and need to be checked
        fixed_subtitle_list = SubtitleList()
        for subtitle in subtitle_list:
            new_text = self._text_formatter.fix_format(subtitle.text)
            if new_text != subtitle.text:
                subtitle.text = new_text
                # add the SAME subtitle object to the list of fixed subs
                fixed_subtitle_list.add_subtitle(subtitle)
        
        if len(fixed_subtitle_list) > 0:
            # Show dialog so that user can check fixed subtitles
            fmt_dlg = FormatCheckDialog(self._window, fixed_subtitle_list)
            res = fmt_dlg.run()
            fmt_dlg.destroy_dialog()
            self._set_unsaved(True)

    def _remove_extension(self, filename):
        """Returns the filename without extension.
        """
        dot_pos = filename.rfind('.')
        if dot_pos > -1:
            return filename[:dot_pos]
        return filename
    
    def _move_selected_sub(self, move_forward):
        millis = self._move_by if move_forward else - self._move_by
        __, iter_ = self._selection_subtitle.get_selected()
        if iter_ != None:
            path = self._subtitle_list_model.move_subtitle_by(iter_, millis,
                                                          self._move_subsequent)
            self._select_subtitle(path)        

    def _select_subtitle(self, path):
        self._selection_subtitle.select_path(path)
        self._tree_subtitles.set_cursor(path)

    def _format_player_time_nanos(self, nanos):
        millis = nanos / 1000000
        return Time.format(millis)

    def _format_time_column(self, column_num, cell, model, iter_):
        time = model.get_value(iter_, column_num)
        val = Time.format(time)
        cell.set_property('text', val)

    def _format_start_time_column(self, column, cell, model, iter_, user_data):
        self._format_time_column(0, cell, model, iter_)
        
    def _format_end_time_column(self, column, cell, model, iter_, user_data):
        self._format_time_column(1, cell, model, iter_)
    
    def _on_subtitle_changed(self):
        self._set_unsaved(True)

    def _on_mnu_run_script_activate(self, widget):
        filechooser = self._new_open_filechooser(
                                          _('Please choose Submod-script file'))
        folder = Settings().get(self, 'script_folder')
        if folder is not None:
            filechooser.set_current_folder(folder)
        filter_scripts = Gtk.FileFilter()
        filter_scripts.set_name(_('Submod-script files')+' (*.submod)')
        filter_scripts.add_pattern('*.submod')
        filechooser.add_filter(filter_scripts)
        res = filechooser.run()
        file_ = filechooser.get_filename()
        filechooser.destroy_dialog()
        if res == Gtk.ResponseType.OK and path.isfile(file_):
            dir_, filename = path.split(file_)
            Settings().set(self, 'script_folder', dir_)
            run_dlg = ScriptRunDialog(self._window, file_)
            res = run_dlg.run()
            run_dlg.destroy_dialog()
        
    def _on_mnu_export_script_activate(self, widget):
        if self._submod is None:
            return
        filechooser = Gtk.FileChooserDialog(
            _('Where should the Submod-script be saved?'), self._window,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        folder = Settings().get(self, 'script_folder')
        if folder is not None:
            filechooser.set_current_folder(folder)
        filter_scripts = Gtk.FileFilter()
        filter_scripts.set_name(_('Submod-script files')+' (*.submod)')
        filter_scripts.add_pattern('*.submod')
        filechooser.add_filter(filter_scripts)
        res = filechooser.run()
        file_ = filechooser.get_filename()
        filechooser.destroy()
        if res != Gtk.ResponseType.OK:
            return
        if not file_.lower().endswith('.submod'):
            file_ = file_ + '.submod'
        cuts = None
        if self._cuts is not None:
            dialog = Gtk.MessageDialog(self._window, 0,
                                 Gtk.MessageType.QUESTION,
                                 Gtk.ButtonsType.NONE,
                                 _('You opened a cutlist file. Do you want to e'
                                   'xport timings for the cut or uncut video? I'
                                   'f you export timings for the uncut video on'
                                   'e can choose a cutlist when running the Sub'
                                   'mod-script.'))
            dialog.add_buttons(_('cut'), Gtk.ResponseType.CANCEL,
                               _('uncut'), Gtk.ResponseType.OK)
            dialog.set_default_response(Gtk.ResponseType.OK)
            res = dialog.run()
            dialog.destroy()
            if res == Gtk.ResponseType.OK:
                cuts = self._cuts

        dir_, filename = path.split(file_)
        Settings().set(self, 'script_folder', dir_)
        # export Submod-script
        subtitle_list = self._subtitle_list_model.data
        self._submod.generate_script(subtitle_list, cuts)
        self._submod.save_script(file_)
        dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, _('Submod-script exported successfully!'))
        dialog.run()
        dialog.destroy()

    def _on_mnu_exit_activate(self, widget):
        self._try_quit()
    
    def _on_mnu_about_activate(self, widget):
        dialog = AboutDialog(self._window)
        dialog.run()
        dialog.destroy_dialog()

    def _on_mnu_change_fps_activate(self, widget):
        if self._subtitle_list_model is None:
            dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.ERROR,
                         Gtk.ButtonsType.OK,
                         _('Please open a subtitle file first!'))
            dialog.run()
            dialog.destroy()
            return
        dialog = ChangeFpsDialog(self._window)
        res = dialog.run()
        dialog.destroy_dialog()
        if res == Gtk.ResponseType.OK:
            self._subtitle_list_model.change_fps(dialog.fps_from, dialog.fps_to)
            dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.INFO,
                         Gtk.ButtonsType.OK,
                         _('The timestamps of the subtitles were successfully '
                           'adapted for the new FPS!'))
            dialog.run()
            dialog.destroy()

    def _on_btn_add_subtitle_clicked(self, widget):
        if self._subtitle_list_model is None:
            return
        millis = long(self._adj_position.get_value()) / 1000000
        subtitle = Subtitle(millis, millis)
        dlg = SubtitleDialog(self._window, subtitle)
        res = dlg.run()
        dlg.destroy_dialog()
        if res == Gtk.ResponseType.OK:
            self._subtitle_list_model.add_subtitle(subtitle)

    def _on_btn_remove_subtitle_clicked(self, widget):
        __, iter_ = self._selection_subtitle.get_selected()
        if iter_ != None:
            self._subtitle_list_model.remove_subtitle(iter_)

    def _on_btn_edit_subtitle_clicked(self, widget, edit=True):
        __, iter_ = self._selection_subtitle.get_selected()
        if iter_ != None:
            # Pass a copy of the subtitle to the SubtitleDialog because
            # it should not modify the original subtitle. The subtitle
            # is then modified using SubtitleListTreeModel to reflect
            # changes to the GUI.
            subtitle = copy.copy(self._subtitle_list_model.get_item(iter_))
            dlg = SubtitleDialog(self._window, subtitle, edit=True)
            res = dlg.run()
            dlg.destroy_dialog()
            if res == Gtk.ResponseType.OK:
                self._subtitle_list_model.edit_subtitle(iter_, subtitle)
        

