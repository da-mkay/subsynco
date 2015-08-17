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

import threading


class ThreadHelpers(object):
    @staticmethod
    def run_in_thread(func):
        """ThreadHelpers.run_in_thread can be used as a function
        decorator to force execution in a new thread.
        """
        def callback(*args):
            thread = threading.Thread(target=func, args=args)
            thread.start()   
        return callback

