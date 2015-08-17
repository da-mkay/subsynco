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

import copy

from subsynco.gui.subtitle_dialog import SubtitleDialog
from subsynco.gui.subtitle_list_tree_model import SubtitleListTreeModel
from subsynco.utils.resources import Resources
from subsynco.utils.time import Time

class FormatCheckDialog(object):

    def __init__(self, parent, subtitle_list):
        self._subtitle_list = subtitle_list
        
        self._builder = Gtk.Builder()
        glade_file = Resources.find(path.join('data', 'gui', 'glade',
                                              'format_check_dialog.glade'))
        self._builder.add_from_file(glade_file)
        self._dialog = self._builder.get_object('format_check_dialog')
        self._dialog.set_transient_for(parent)
        self._builder.connect_signals(self)
        self._tree_subtitles_old = self._builder.get_object(
                                                           'tree_subtitles_old')
        self._tree_subtitles_new = self._builder.get_object(
                                                           'tree_subtitles_new')
        self._selection_subtitle_old = self._builder.get_object(
                                                       'selection_subtitle_old')
        self._selection_subtitle_new = self._builder.get_object(
                                                       'selection_subtitle_new')

        self._subtitle_list_model_old = SubtitleListTreeModel(subtitle_list,
                                                      self._on_subtitle_changed,
                                                      True)
        self._subtitle_list_model_new = SubtitleListTreeModel(subtitle_list,
                                                      self._on_subtitle_changed)
        self._tree_subtitles_old.set_model(self._subtitle_list_model_old)
        self._tree_subtitles_new.set_model(self._subtitle_list_model_new)

        # The start/end time should be displayed as hh:mm:ss.iii
        # TODO same as in main_window --> outsource
        cellrenderer_start_new = self._builder.get_object(
                                                       'cellrenderer_start_new')
        column_start_new = self._builder.get_object('column_start_new')
        column_start_new.set_cell_data_func(cellrenderer_start_new,
                                        self._format_start_time_column)

        cellrenderer_end_new = self._builder.get_object('cellrenderer_end_new')
        column_end_new = self._builder.get_object('column_end_new')
        column_end_new.set_cell_data_func(cellrenderer_end_new,
                                      self._format_end_time_column)

        cellrenderer_start_old = self._builder.get_object(
                                                       'cellrenderer_start_old')
        column_start_old = self._builder.get_object('column_start_old')
        column_start_old.set_cell_data_func(cellrenderer_start_old,
                                        self._format_start_time_column)

        cellrenderer_end_old = self._builder.get_object('cellrenderer_end_old')
        column_end_old = self._builder.get_object('column_end_old')
        column_end_old.set_cell_data_func(cellrenderer_end_old,
                                      self._format_end_time_column)

    def _on_subtitle_changed(self):
        pass
    
    def _on_cursor_changed_old(self, widget):
        """Is called when an item on the "old" subtitle list is selected.
        
        Selects the same row on the "new" subtitle list.
        """
        __, iter_ = self._selection_subtitle_old.get_selected()
        if iter_ != None:
            i = self._subtitle_list_model_old.get_item_index(iter_)
            __, iter_ = self._subtitle_list_model_new.get_path_iter_by_row(i)
            self._selection_subtitle_new.select_iter(iter_)
    
    def _on_cursor_changed_new(self, widget):
        """Is called when an item on the "new" subtitle list is selected.
        
        Selects the same row on the "old" subtitle list.
        """
        __, iter_ = self._selection_subtitle_new.get_selected()
        if iter_ != None:
            i = self._subtitle_list_model_new.get_item_index(iter_)
            __, iter_ = self._subtitle_list_model_old.get_path_iter_by_row(i)
            self._selection_subtitle_old.select_iter(iter_)
    
    def _on_tree_subtitles_row_activated(self, tree, path, column):
        iter_ = self._subtitle_list_model_new.get_iter(path)
        self._show_subtitle_edit_dialog(iter_)
    
    # TODO same as in main_window --> outsource
    def _format_time_column(self, column_num, cell, model, iter_):
        time = model.get_value(iter_, column_num)
        val = Time.format(time)
        cell.set_property('text', val)

    # TODO same as in main_window --> outsource
    def _format_start_time_column(self, column, cell, model, iter_, user_data):
        self._format_time_column(0, cell, model, iter_)
        
    # TODO same as in main_window --> outsource
    def _format_end_time_column(self, column, cell, model, iter_, user_data):
        self._format_time_column(1, cell, model, iter_)

    def _on_btn_edit_subtitle_clicked(self, widget, edit=True):
        __, iter_ = self._selection_subtitle_new.get_selected()
        self._show_subtitle_edit_dialog(iter_)

    def _show_subtitle_edit_dialog(self, iter_):
        if iter_ != None:
            # Pass a copy of the subtitle to the SubtitleDialog because
            # it should not modify the original subtitle. The subtitle
            # is then modified using SubtitleListTreeModel to reflect
            # changes to the GUI.
            subtitle = copy.copy(self._subtitle_list_model_new.get_item(iter_))
            dlg = SubtitleDialog(self._dialog, subtitle, edit=True,
                                 allow_edit_time=False)
            res = dlg.run()
            dlg.destroy_dialog()
            if res == Gtk.ResponseType.OK:
                self._subtitle_list_model_new.edit_subtitle(iter_, subtitle)    

    def run(self):
        return self._dialog.run()

    def destroy_dialog(self):
        return self._dialog.destroy()

