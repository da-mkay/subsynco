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

import inspect
import json
import os
from os import path


class Settings(object):
    def __init__(self):
        # The first Settings()-call will invoke __init__. Since the
        # name "Settings" will be overwritten (see end of file) further
        # Settings()-calls will invoke __call__ instead which returns
        # the singleton instance.
        self._settings = {}
        self.loaded = False

    def __call__(self):
        # Singleton() is called after the Singleton instance was
        # created. So we can return the instance here.
        return self
    
    def load(self, file_):
        if not path.exists(file_):
            return
        with open(file_) as f:
            try:
                json_data = json.load(f)
                if isinstance(json_data, dict):
                    self._settings = json_data
            except ValueError:
                pass

    def save(self, file_):
        dir_, filename = path.split(file_)
        if not path.exists(dir_):
            os.makedirs(dir_)
        with open(file_, 'w') as f:
            json.dump(self._settings, f, indent=2, sort_keys=True)

    def set(self, obj, name, value):
        key = self._generate_key(obj, name)
        self._settings[key] = value

    def get(self, obj, name, default=None):
        key = self._generate_key(obj, name)
        return self._settings.get(key, default)

    def _generate_key(self, obj, name):
        # Use full module path of the object obj to create the lookup
        # key.
        return inspect.getmodule(obj).__name__ + '.' + name


# Settings is a singleton, so we create one (!) instance of the
# Settings-class and overwrite the name "Settings" so that it points
# to that instance.
Settings = Settings()
