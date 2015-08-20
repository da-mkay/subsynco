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

import site
import sys
import os

from cx_Freeze import setup, Executable


# This is a list of files that cx_freeze includes in the build. Each
# entry is a tuple of source and destination.
include_files = []

# Usually C:\Python27\lib\site-packages\gnome
gnome_dir = os.path.join(site.getsitepackages()[1], "gnome")

# Required Gnome DLLs
gnome_dlls = ['libaerial-0.dll',
              'libatk-1.0-0.dll',
              'libcairo-gobject-2.dll',
              'libcurl-4.dll',
              'libffi-6.dll',
              'libfftw3.dll',
              'libfluidsynth-1.dll',
              'libfontconfig-1.dll',
              'libfreetype-6.dll',
              'libgdk-3-0.dll',
              'libgdk_pixbuf-2.0-0.dll',
              'libgio-2.0-0.dll',
              'libgirepository-1.0-1.dll',
              'libglib-2.0-0.dll',
              'libgmodule-2.0-0.dll',
              'libgnutls-26.dll',
              'libgobject-2.0-0.dll',
              'libgraphene-1.0-0.dll',
              'libgstapp-1.0-0.dll',
              'libgstaudio-1.0-0.dll',
              'libgstbadbase-1.0-0.dll',
              'libgstbadvideo-1.0-0.dll',
              'libgstbase-1.0-0.dll',
              'libgstbasecamerabinsrc-1.0-0.dll',
              'libgstcodecparsers-1.0-0.dll',
              'libgstcontroller-1.0-0.dll',
              'libgstfft-1.0-0.dll',
              'libgstgl-1.0-0.dll',
              'libgstmpegts-1.0-0.dll',
              'libgstnet-1.0-0.dll',
              'libgstpbutils-1.0-0.dll',
              'libgstphotography-1.0-0.dll',
              'libgstreamer-1.0-0.dll',
              'libgstriff-1.0-0.dll',
              'libgstrtp-1.0-0.dll',
              'libgstrtsp-1.0-0.dll',
              'libgstsdp-1.0-0.dll',
              'libgsttag-1.0-0.dll',
              'libgsturidownloader-1.0-0.dll',
              'libgstvideo-1.0-0.dll',
              'libgtk-3-0.dll',
              'libharfbuzz-gobject-0.dll',
              'libidn-11.dll',
              'libintl-8.dll',
              'libjack.dll',
              'libjasper-1.dll',
              'libjpeg-8.dll',
              'libopenexr-2.dll',
              'libopenjp2.dll',
              'liborc-0.4-0.dll',
              'liborc-test-0.4-0.dll',
              'libp11-kit-0.dll',
              'libpango-1.0-0.dll',
              'libpangocairo-1.0-0.dll',
              'libpangoft2-1.0-0.dll',
              'libpangowin32-1.0-0.dll','libpng16-16.dll',
              'libproxy.dll',
              'librsvg-2-2.dll',
              'libsoup-2.4-1.dll',
              'libsqlite3-0.dll',
              'libvisual-0.4-0.dll',
              'libwebp-5.dll',
              'libwinpthread-1.dll',
              'libxmlxpat.dll',
              'libzzz.dll'
]
for dll in gnome_dlls:
    include_files.append((os.path.join(gnome_dir, dll), dll))

# We need some more Gnome files (theme, icons, translation, ...).
gnome_folders = ['etc\\fonts',
                 'etc\\gtk-3.0',
                 'lib\\girepository-1.0',
                 'lib\\gstreamer-1.0',
                 'lib\\gst-validate-launcher',
                 'share\\glib-2.0',
                 'share\\icons\\Adwaita',
                 'share\\icons\\hicolor',
                 'share\\locale\\de',
                 'share\\locale\\en',
                 'share\\themes\\Vertex-Light',
]
for folder in gnome_folders:
    include_files.append((os.path.join(gnome_dir, folder), folder))
include_files.append((os.path.join(gnome_dir, 'license'), 'license-gnome'))

def filter_file(file_):
    return (file_.endswith('.glade') or
            file_.endswith('.png') or
            file_.endswith('.svg') or
            file_.endswith('.mo'))

# Include SubSynco files (icons, translations, glade-files)
subsynco_folders = ['subsynco\\data']
for folder in subsynco_folders:
    for root, dirs, files in os.walk(folder):
        for file_ in filter(filter_file, files):
            path = os.path.join(root, file_)
            include_files.append((path, path[9:]))
include_files.append(('LICENSE', 'LICENSE'))
    
base = None
# Do not open the console while running SubSynco.
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable("subsynco-gtk", base=base, icon=r'subsynco\data\gui\icons\hicolor\ico\subsynco.ico')
]

build_options = {
    'build_exe': 'build',
    'compressed': False,
    'includes': ['gi', 'cairo'],
    'packages': ['gi', 'cairo'],
    'include_files': include_files
}

setup(name = "SubSynco",
      version = "0.2.0",
      description = 'SubSynco is a tool for synchronizing subtitle files.',
      author = 'da-mkay',
      license = 'GPL-3',
      platforms = 'all',
      url='http://subsynco.org',
      options = {'build_exe': build_options},
      executables = executables
)
