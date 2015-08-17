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

from gi.repository import GObject
from gi.repository import Gtk
from subsynco.utils.time import Time

class SpinEntry(Gtk.Entry):
    """SpinEntry is a replacement for the faulty Gtk.SpinButton which
    currently does not work properly with input/output signals.
    (See https://bugzilla.gnome.org/show_bug.cgi?id=665551)
    
    It uses clickable primary/secondary icons to change the value of
    the underlying Gtk.Adjustment. Moreover the up/down/page up/
    page down keys can be used to change the value.
    
    You can customize the displayed text and handle text input using
    the output and input signals.
    """

    __gsignals__ = {
        'output': (GObject.SIGNAL_RUN_LAST, bool, (float,)),
        'input': (GObject.SIGNAL_RUN_LAST, int, (str,))
    }

    def __init__(self):
        super(SpinEntry, self).__init__()
        self.set_alignment(0.5)

        # Set the increment/decrement icons.
        # This should be as easy as:
        #   self.set_property('primary-icon-name', 'gtk-remove')
        #   self.set_property('secondary-icon-name', 'gtk-add')
        # However this does not work on Windows. As a workaround
        # we set the PixBuf directly instead of the icon name:
        primary_pixbuf = self.render_icon('gtk-remove', Gtk.IconSize.MENU)
        secondary_pixbuf = self.render_icon('gtk-add', Gtk.IconSize.MENU)
        self.set_property('primary-icon-pixbuf', primary_pixbuf)
        self.set_property('secondary-icon-pixbuf', secondary_pixbuf)
        
        self.connect('icon-release', self._on_icon_release)
        self.connect('key-press-event', self._on_key_press)
        self.connect('focus-out-event', self._on_focus_out)
        self._adjustment = None
        self._adjustment_value_handler_id = None

    def set_adjustment(self, adjustment):
        if self._adjustment_value_handler_id is not None:
            self._adjustment.disconnect(self._adjustment_value_handler_id)
        self._adjustment = adjustment
        self._adjustment_value_handler_id = self._adjustment.connect(
                             'value-changed', self._on_adjustment_value_changed)
        self._update_text()

    def _on_icon_release(self, widget, icon_pos, event):
        if (icon_pos == Gtk.EntryIconPosition.PRIMARY):
            self._decrement()
        else:
            self._increment()

    def _on_key_press(self, widget, event):
        if event.keyval == 65362:
            self._increment()
        elif event.keyval == 65364:
            self._decrement()
        elif event.keyval == 65365:
            self._increment(True)
        elif event.keyval == 65366:
            self._decrement(True)
        elif event.keyval == 65293:
            self._update_value()

        if ((event.keyval >= 65364 and event.keyval <= 65366) or 
                event.keyval == 65362 or event.keyval == 65293):
            return True
        return False
        
    def _on_focus_out(self, widget, event):
        self._update_value()
    
    def _on_adjustment_value_changed(self, adjustment):
        self._update_text()

    def _update_text(self):
        if self._adjustment is None:
            return
        handled = self.emit('output', self._adjustment.get_value())
        if not handled:
            self.set_text(str(self._adjustment.get_value()))
            
    def _update_value(self):
        if self._adjustment is None:
            return
        handled = self.emit('input', self.get_text())
        if handled == 0:
            # Try to cast the text to a float and set the value on the
            # adjustment which leads to a call of _update_text.
            try:
                value = float(self.get_text())
                self.set_value(value)
            except ValueError:
                handled = Gtk.INPUT_ERROR
        if handled == Gtk.INPUT_ERROR:
            # restore old text
            self._update_text()
        # else: handled==1 (True) --> handler should have called
        #       adjustment.set_value which triggers _update_text 

    def _change_value(self, amount):
        value = self._adjustment.get_value()

        # overflow-free check if upper/lower bound is reached
        if (amount >= 0):
            if (self._adjustment.get_upper() - amount  < value):
                new_value = self._adjustment.get_upper()
            else:
                new_value = value + amount
        else:
            if (self._adjustment.get_lower() - amount  > value):
                new_value = self._adjustment.get_lower()
            else:
                new_value = value + amount

        if (new_value == value):
            return # unchanged
        self._adjustment.set_value(new_value)

    def _increment(self, page=False):
        if self._adjustment is None:
            return
        self._change_value(self._get_amount(page))
        
    def _decrement(self, page=False):
        if self._adjustment is None:
            return
        self._change_value(- self._get_amount(page))

    def _get_amount(self, page=False):
        if page:
            return self._adjustment.get_page_increment()
        return self._adjustment.get_step_increment()

    def set_value(self, value):
        if self._adjustment is None:
            return
        if (value > self._adjustment.get_upper()
                or value < self._adjustment.get_lower()
                or value == self._adjustment.get_value()):
            # The value is unchanged. But the Gtk.Entry may contain
            # text that the user has entered. So we need to update
            # the text manually since set_value is not called.
            self._update_text()
        else:
            self._adjustment.set_value(value)


class TimeEntry(SpinEntry):                                        
    def __init__(self):
        super(TimeEntry, self).__init__()
        self.connect('output', self._on_output)
        self.connect('input', self._on_input)
    
    def _on_output(self, widget, value):
        time = Time.format(value)
        widget.set_text(time)
        return True
    
    def _on_input(self, widget, text):
        try:
            millis = Time.millis_from_str(text)
        except TypeError:
            return Gtk.INPUT_ERROR
        self.set_value(millis)
        return True



if __name__ == '__main__':
    win = Gtk.Window()
    win.connect('delete-event', Gtk.main_quit)

    adj = Gtk.Adjustment(0, 0, 3600000, 10, 50)

    def on_output(widget, val):
        widget.set_text(str(int(val)).rjust(4, '0'))
        return True

    def on_input(widget, text):
        if (len(text) != 4):
            return Gtk.INPUT_ERROR
        try:
            value = float(text)
            adj.set_value(value)
        except ValueError:
            return Gtk.INPUT_ERROR
        return True

    spin = SpinEntry()
    spin.connect('output', on_output)
    spin.connect('input', on_input)

    spin.set_adjustment(adj)

    win.add(spin)
    win.show_all()
    Gtk.main()
