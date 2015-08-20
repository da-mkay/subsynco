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

from distutils.core import setup

setup(name='SubSynco',
      version='0.2.0',
      description='SubSynco is a tool for synchronizing subtitle files.',
      author='da-mkay',
      author_email='da-mkay@subsynco.org',
      license='GPL-3',
      platforms='all',
      url='http://subsynco.org',
      packages=['subsynco', 'subsynco.gst', 'subsynco.gui', 'subsynco.media',
                'subsynco.utils'
      ],
      package_dir={'subsynco': 'src/subsynco'},
      package_data={'subsynco': [
                        'LICENSE',
                        'data/locale/*/LC_MESSAGES/*.mo',
                        'data/gui/glade/*.glade',
                        'data/gui/icons/*/*/*.ico',
                        'data/gui/icons/*/*/*/*.png',
                        'data/gui/icons/*/*/*/*.svg',
                        'data/gui/logo/*.png'
                    ]
      },
      data_files = [('share/applications/', ['subsynco.desktop']),
                    ('share/subsynco/', ['src/subsynco/data/gui/icons/hicolor/s'
                                         'calable/apps/subsynco.svg'])
      ],
      scripts=['src/subsynco-gtk'],
      # NOTE windows-version requires chardet instead of magic
      #requires=['magic']
)
