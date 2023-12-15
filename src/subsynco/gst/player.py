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

import sys

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gdk
from gi.repository import Gst
from gi.repository import Gtk
# Needed for window.get_xid(), xvimagesink.set_window_handle(),
# respectively:
if sys.platform == 'linux':
    from gi.repository import GdkX11
from gi.repository import GstVideo

import ctypes
import re
# Import TimeClbFilter so that the plugin gets registered:
from subsynco.gst.filter import TimeClbFilter
from subsynco.media.text_formatter import TextFormatter
from subsynco.utils.logger import Logger


class MultimediaPlayer(object):
    def __init__(self, drawing_area):
        self._drawing_area = drawing_area;
        self._subtitle = None
        self._position_changed_callback = None
        self._duration_changed_callback = None
        self._subtitle_list = None
        self._cur_subtitle = None
        self._duration = None
        self._position = 0
        self._file_uri = None

        self._drawing_area.connect('realize', self._on_video_realize)
        self._drawing_area.connect('unrealize', self._on_video_unrealize)
        self._drawing_area.connect('draw', self._on_video_draw)

        # GStreamer setup
        # ---------------
        self._player = Gst.ElementFactory.make('playbin', 'MultimediaPlayer')

        # PlayBin uses autovideosink by default but we need to wrap it
        # in a Bin so that we can use timeclbfilter and textoverlay.
        video_sink = Gst.ElementFactory.make('autovideosink')

        # Create the following bin:
        #   timeclbfilter ! textoverlay ! autovideosink
        # video_bin is then set as self._player's video-sink
        self._textoverlay = Gst.ElementFactory.make('textoverlay',
                                                    'textoverlay')
        timeclbfilter = Gst.ElementFactory.make('timeclbfilter',
                                                'timeclbfilter')
        video_bin = Gst.Bin.new('timer-text-video-bin')
        video_bin.add(timeclbfilter)
        video_bin.add(self._textoverlay)
        video_bin.add(video_sink)
        sink_pad = Gst.GhostPad.new('sink',
                                    timeclbfilter.get_static_pad('sink'))
        video_bin.add_pad(sink_pad)
        timeclbfilter.link(self._textoverlay)
        self._textoverlay.link(video_sink)

        timeclbfilter.set_timer_callback(self._on_timer_tick)

        self._textoverlay.set_property('font-desc', 'Sans 28')
        self._textoverlay.set_property('color', 0xffffe400)
        self._textoverlay.set_property('outline-color', 0xff333333)

        self._player.set_property('video-sink', video_bin)

        bus = self._player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('message', self._on_player_message)
        bus.connect('sync-message::element', self._on_player_sync_message)
        
        self._text_formatter = TextFormatter()

    def _on_timer_tick(self, nanos):
        self._position = nanos
        # If a SubtitleList is set we show/hide the subtitles here
        # based on the time.
        if (self._subtitle_list is not None):
            millis = nanos / 1000000
            __, subtitle = self._subtitle_list.get_subtitle(millis)
            if (subtitle is not self._cur_subtitle):
                if (subtitle is None):
                    txt = ''
                else:
                    txt = self._text_formatter.fix_format(subtitle.text,
                                                          pango_markup=True)
                self._textoverlay.set_property('text', txt)
                self._cur_subtitle = subtitle
        # Invoke users position_changed callback if any.
        if (self._position_changed_callback is not None):
            self._position_changed_callback(nanos)

    def _on_video_realize(self, widget):
        # The window handle must be retrieved in GUI-thread and before
        # playing pipeline.
        video_window = self._drawing_area.get_property('window')
        if sys.platform == 'win32':
            # On Windows we need a "hack" to get the native window
            # handle.
            # See http://stackoverflow.com/questions/23021327/how-i-can-
            # get-drawingarea-window-handle-in-gtk3/27236258#27236258
            if not video_window.ensure_native():
                Logger.error(
                          _('[Player] Video playback requires a native window'))
                return
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
            video_window_gpointer = ctypes.pythonapi.PyCapsule_GetPointer(
                                                video_window.__gpointer__, None)
            gdkdll = ctypes.CDLL ('libgdk-3-0.dll')
            self._video_window_handle = gdkdll.gdk_win32_window_get_handle(
                                                          video_window_gpointer)
        elif sys.platform == 'darwin':
            if not video_window.ensure_native():
               Logger.error(
                         _('[Player] Video playback requires a native window'))
               return
            
            #x = Gtk.Window.list_toplevels()
            #for y in x:
            #    if y.get_realized():
            #        print(y.get_property('window').get_property('Handle'))
            
            #print(video_window.__gpointer__)
            #print(self._drawing_area.get_realized())

            #ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            #ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
            #video_window_gpointer = ctypes.pythonapi.PyCapsule_GetPointer(video_window.__gpointer__, None)
            #gdkdll = ctypes.CDLL ('libgdk-3.0.dylib')
            #self._video_window_handle = gdkdll.gdk_quartz_window_get_nswindow(video_window_gpointer)
            #print(self._video_window_handle)
        else:
            self._video_window_handle = video_window.get_xid()

    def _on_video_unrealize(self, widget):
        # To prevent race conditions when closing the window while
        # playing
        self._player.set_state(Gst.State.NULL)

    def _on_video_draw(self, drawing_area, cairo_context):
        """This method is called when the player's DrawingArea emits the
        draw-signal.
        
        Usually the playbin will render the currently opened video in
        the DrawingArea. But if no video is opened we take care of
        drawing.
        """
        if self._file_uri is not None:
            # A video is already opened. So playbin will take care of
            # showing the video inside the DrawingArea.
            return False
        # No video is opened. So we draw a simple black background.
        width = drawing_area.get_allocated_width()
        height = drawing_area.get_allocated_height()
        cairo_context.rectangle(0, 0, width, height)
        cairo_context.set_source_rgb(0.15, 0.15, 0.15)
        cairo_context.fill()
        text = _('no video loaded')
        cairo_context.set_font_size(14)
        x_bearing, y_bearing, txt_width, txt_height, x_advance, y_advance = (
                                               cairo_context.text_extents(text))
        cairo_context.move_to(width/2 - txt_width/2 - x_bearing, height/2 - 
                              y_bearing/2)
        cairo_context.set_source_rgb(1.0, 1.0, 1.0)
        cairo_context.show_text(text)
        return True
    
    def _on_player_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            # We pause the video instead of stop, because we may still
            # want to seek.
            self.pause()
        elif message.type == Gst.MessageType.ERROR:
            self.stop()
            (err, debug) = message.parse_error()
            Logger.error(_('[Player] {}').format(err), debug)
        elif message.type == Gst.MessageType.ASYNC_DONE:
            # TODO Don't try to get duration at each ASYNC_DONE, only
            #      on new file and real state change.
            self._query_duration()
        # TODO Gst.MessageType.DURATION_CHANGED: query_duration would
        #      fail if ASYNC_DONE was not received

    def _on_player_sync_message(self, bus, message):
        # For more information see here:
        # http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-p
        # lugins-base-libs/html/gst-plugins-base-libs-gstvideooverlay.ht
        # ml
        if message.get_structure() is None:
            return
        if not GstVideo.is_video_overlay_prepare_window_handle_message(message):
            return
        imagesink = message.src
        imagesink.set_property('force-aspect-ratio', True)
        imagesink.set_window_handle(self._video_window_handle)
            
    def _query_duration(self):
        if self._duration is not None:
            return True
        ok, dur = self._player.query_duration(Gst.Format.TIME)
        self._duration = dur
        if (self._duration_changed_callback is not None):
            self._duration_changed_callback(self._duration)
        return ok

    def set_position_changed_callback(self, callback):
        self._position_changed_callback = callback

    def set_duration_changed_callback(self, callback):
        self._duration_changed_callback = callback

    def set_subtitle_list(self, subtitle_list):
        """Set the subsynco.media.subtitle.SubtitleList to be used for
        showing subtitles.
        """
        self._textoverlay.set_property('text', '')
        self._cur_subtitle = None
        self._subtitle_list = subtitle_list

    def pause(self):
        if self._file_uri is not None:
            self._player.set_state(Gst.State.PAUSED)

    def play(self):
        if self._file_uri is not None:
            self._player.set_state(Gst.State.PLAYING)

    def stop(self):
        self._player.set_state(Gst.State.NULL)
        self._duration = None
        self._position = 0
        if (self._duration_changed_callback is not None):
            self._duration_changed_callback(0)
        if (self._position_changed_callback is not None):
            self._position_changed_callback(0)

    def set_file(self, file_uri):
        self.stop()
        self._file_uri = file_uri
        if file_uri is None:
            # The DrawingArea may still show the old video (if any was
            # opened before). So we force a draw-signal which will lead
            # to a call to _on_video_draw.
            self._drawing_area.queue_draw()
        else:
            self._player.set_property('uri', file_uri)

    def seek(self, nanos):
        if self._file_uri is None:
            return
        # The duration should have been already queried when the file
        # was loaded. However ensure that we have a duration!
        ok = self._query_duration()
        if not ok:
            Logger.warn(
                  _('Warning - [Player] Failed to get duration. Seek aborted!'))
            return
        if (nanos < 0):
            nanos = 0
        elif (nanos > self._duration):
            nanos = self._duration # TODO: duration is inaccurate!!!
        if (nanos == self._position):
            return
        ok = self._player.seek_simple(Gst.Format.TIME, 
                                   Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                                   nanos)
        if not ok:
            Logger.warn(_('Warning - [Player] Failed to seek.'))

    def seek_relative(self, nanos):
        self.seek(self._position + nanos)

