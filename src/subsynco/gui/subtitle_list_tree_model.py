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

from subsynco.gui.tree_model import ListTreeModel

class SubtitleListTreeModel(ListTreeModel):
    """A Gtk TreeModel for SubtitleList-objects.
    
    Any changes to the subtitles of the SubtitleList should be made
    using SubtitleListTreeModel, so that the GUI gets updated and shows
    always the correct data.
    """
    def __init__(self, subtitle_list, on_change_callback, use_orig_text=False):
        self._on_change_callback = on_change_callback
        column_config = [(long, 'start'), (long, 'end'),
                         (str, 'orig_text') if use_orig_text else (str, 'text')]
        super(SubtitleListTreeModel, self).__init__(subtitle_list,
                                                    column_config)

    # TODO remember changes in a stack to support undo/redo
    # TODO maybe show duration

    def add_subtitle(self, subtitle):
        i = self.data.add_subtitle(subtitle)
        self.signal_row_inserted(i)
        self._on_change_callback()

    def remove_subtitle(self, iter_):
        i = self.get_item_index(iter_)
        self.data.remove_subtitle(i)
        self.signal_row_deleted(i)
        self._on_change_callback()

    def edit_subtitle(self, iter_, new_subtitle):
        i = self.get_item_index(iter_)
        old_subtitle = self.get_item(iter_)
        if (old_subtitle.start == new_subtitle.start and
                old_subtitle.end == new_subtitle.end):
            if old_subtitle.text != new_subtitle.text:
                old_subtitle.text = new_subtitle.text
                self.signal_row_changed(i)
                self._on_change_callback()
        else:
            # NOTE: Since new_subtitle should be a copy of the original
            #       subtitle it will contain the orig_*-values, too. So
            #       removing and adding the subtitle will result in an
            #       update-entry inside the submod-file (not remove/add-
            #       entries).
            self.data.remove_subtitle(i)
            new_i = self.data.add_subtitle(new_subtitle)
            if i == new_i:
                self.signal_row_changed(i)
            else:
                self.signal_row_moved(i, new_i)
            self._on_change_callback()

    def move_subtitle_by(self, iter_, millis, move_subsequent):
        """Move the subtile identified by iter_ by millis milliseconds.
        
        If move_subsequent is True then all subsequent subtitles are
        also moved. Returns a Gtk.TreePath that contains the new
        position of the moved subtitle identified by iter_.
        """
        new_path = self.get_path(iter_)
        if millis == 0:
            return new_path

        # The order of subtitle moving is important. For example if
        # adding a positive time value we must start moving with the
        # last subtitle.
        # If we would start with the first subtitle, let's say the 
        # subtitle at index 0 and move it to index 2 then we would have
        # to consider that the next subtitle we need to move (which was
        # at index 1) is now at index 0 (and so on).
        
        # By using self.data.move_subtitle we ensure the correct order
        # of subtitles based on their time.
        # For example: We have the following three subtitles:
        #    1. 00:00:01.000
        #    2. 00:00:02.000
        #    3. 00:00:03.000
        # We now move subtitle 2 (and subsequent) by -1.500, which
        # results in the following list (note the new order):
        #    2. 00:00:00.500
        #    1. 00:00:01.000
        #    3. 00:00:01.500
        
        i = self.get_item_index(iter_)
        reversed_ = millis > 0
        max_j = len(self.data) if move_subsequent else i+1
        j = len(self.data)-1 if reversed_ and move_subsequent else i
        while ((not reversed_ and j < max_j)
                or (reversed_ and j >= i)):
            new_j = self.data.move_subtitle(j, millis)
            if new_j == j:
                self.signal_row_changed(j)
            else:
                self.signal_row_moved(j, new_j)
                if j == i:
                    # The first (maybe selected) row moved!
                    new_path, __ = self.get_path_iter_by_row(new_j)
            j += -1 if reversed_ else 1
        self._on_change_callback()
        return new_path

    def move_subtitle_to(self, iter_, millis, move_subsequent):
        diff = millis - self.get_item(iter_).start
        return self.move_subtitle_by(iter_, diff, move_subsequent)

    def change_fps(self, fps_from, fps_to):
        num_changed = self.data.change_fps(fps_from, fps_to)
        for i in range(0, num_changed):
            self.signal_row_changed(i)
        self._on_change_callback()
    

