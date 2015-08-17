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
from gi.repository import GObject
from gi.repository import Gtk


class ListTreeModel(GObject.GObject, Gtk.TreeModel):
    """ListTreeModel is a simple but flexible Gtk.TreeModel for existing
    list-like data models.

    ListTreeModel can be used to provide the data of existing list-like
    data models to a TreeView without using a separate storage like
    ListStorage. Instead the original data model and its elements are
    referenced.

    Therefore the data model itself must implement __len__ and
    __getitem__.

    The column_config passed to the constructor specifies the number and
    type of columns and the mapping of the columns to the attributes/
    methods of the model-items.

    Example:
    Let data be a list of Book-objects. Each Book-object has an
    attribute title and a method get_stock.
    One might use the following column_config:
    [(str, 'title'), (int, 'get_stock')]

    Note: You can omit the second argument of a column-definition. Then
          the value of that column will be the item itself.
          Example: [(object, ), (str, 'title')]
    
    You can use the signal_* methods to send a signal for the given row
    For example: signal_row_changed(0).
    
    Usually you will subclass ListTreeModel. All modifications to the
    data models should then be done using your subclass to reflect
    changes to the GUI (ViewModel-like behavior).
    """
 
    def __init__(self, data, column_config):
        """Create a new ListTreeModel instance.

        data must be an object that implements the __len__ and
        __getitem__ methods. column_config is a list of tuples each
        specifying the column's data type and the mapping to an
        attribute/method of a model-item. However the mapping can be
        omitted. See class description for more details.
        """
        super(ListTreeModel, self).__init__()
        self.data = data
        self._column_config = column_config

    def get_item(self, iter_):
        """Get the item from data based on the given Gtk.TreeIter.
        """
        return self.data[iter_.user_data]

    def get_item_index(self, iter_):
        """Get the index of the item based on the given Gtk.TreeIter.
        """
        return iter_.user_data
    
    def get_path_iter_by_row(self, i):
        path = Gtk.TreePath.new_from_string(str(i))
        return (path, self.get_iter(path))

    def signal_row_changed(self, i):
        path, iter_ = self.get_path_iter_by_row(i)
        self.row_changed(path, iter_)

    def signal_row_inserted(self, i):
        path, iter_ = self.get_path_iter_by_row(i)
        self.row_inserted(path, iter_)

    def signal_row_deleted(self, i):
        path = Gtk.TreePath.new_from_string(str(i))
        self.row_deleted(path)

    def signal_row_moved(self, from_i, to_j):
        self.signal_row_deleted(from_i)
        self.signal_row_inserted(to_j)

    def do_get_iter(self, path):
        """Get a Gtk.TreeIter pointing to path.

        Returns a (bool, iter) tuple. If path does not exist, iter is
        set to an invalid iterator and bool is set to False.
        """
        indices = path.get_indices()
        # Since the data is only a list, not a tree (so no childs) we
        # only look at the first index.
        if indices[0] < len(self.data):
            iter_ = Gtk.TreeIter()
            iter_.user_data = indices[0]
            return (True, iter_)
        else:
            return (False, None)
 
    def do_iter_next(self, iter_):
        """Get a Gtk.TreeIter pointing to the next node.

        Returns a (bool, iter) tuple. If there is no next node, iter is
        set to an invalid iterator and bool is set to False.
        """
        count = len(self.data)
        if iter_.user_data is None and count != 0:
            iter_.user_data = 0
            return (True, iter_)
        elif iter_.user_data < count - 1:
            iter_.user_data += 1
            return (True, iter_)
        else:
            return (False, None)
 
    def do_iter_has_child(self, iter_):
        """Returns False since this is a list-model which has no childs.
        """
        return False
 
    def do_iter_nth_child(self, iter_, n):
        """Get a Gtk.TreeIter pointing to the n-th root node.

        Returns a (bool, iter) tuple. Since data is a flat list, the
        passed Gtk.TreeIterator will always be None. So iter is always
        set to the n-th root node.
        """
        iter_ = Gtk.TreeIter()
        iter_.user_data = n
        return (True, iter_)
 
    def do_get_path(self, iter_):
        """Returns tree path references by iter.
        """
        if iter_.user_data is not None:
            path = Gtk.TreePath((iter_.user_data,))
            return path
        else:
            return None
 
    def do_get_value(self, iter_, column):
        """Returns the value for the given Gtk.TreeIterator and column.
        """
        item = self.get_item(iter_)
        conf = self._column_config[column]
        if (len(conf)<2):
            # No attribute/method mapping: return item itself
            return item
        item_attr = getattr(item, conf[1])
        return item_attr() if callable(item_attr) else item_attr
 
    def do_get_n_columns(self):
        """Returns the number of columns.
        """
        return len(self._column_config)
 
    def do_get_column_type(self, column):
        """Returns the type of the column based on the column_config.
        """
        return self._column_config[column][0]
 
    def do_get_flags(self):
        """Returns the flags supported by this interface.
        """
        return Gtk.TreeModelFlags.LIST_ONLY

 
if __name__ == '__main__':
    # Example:

    import random
 
    class Book(object):
        def __init__(self, title, stock):
            self.title = title
            self._stock = stock

        def get_stock(self):
            return self._stock

    # The base for the ListTreeModel will be a list of 100 Book-objects.
    count = 100
    data = [
        Book('Book ' + str(i), random.randint(1, 100)) for i in range(count)]

    # Create a ListTreeModel based on the Book-list. The first column
    # with type str is mapped to the title-attribute of a Book-object.
    # The second column of type int is mapped to the get_stock method.
    model = ListTreeModel(
        data,
        [(str, 'title'), (int, 'get_stock')]
    )
 
    # Create/Init TreeView
    view = Gtk.TreeView()
    view.set_model(model)
    # NOTE: You may want to use Gtk.TreeViewColumn's method
    #       set_cell_data_func to format the text being shown.
    view.append_column(Gtk.TreeViewColumn('Title', Gtk.CellRendererText(),
                                          text=0))
    view.append_column(Gtk.TreeViewColumn('Stock', Gtk.CellRendererText(),
                                          text=1))
 
    # Create a window showing the Gtk.TreeView.
    win = Gtk.Window()
    win.connect('destroy', Gtk.main_quit)
    sw = Gtk.ScrolledWindow()
    sw.add(view)
    win.add(sw)
    win.resize(500, 500)
    win.show_all()
    Gtk.main()

