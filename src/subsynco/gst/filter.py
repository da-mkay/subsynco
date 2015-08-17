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
from gi.repository import GObject
from gi.repository import Gst
from gi.repository import GstVideo


class TimeClbFilter(GstVideo.VideoFilter):
    """A VideoFilter that does no modifications but invokes a callback
    method for each frames timestamp.
    """

    # based on textoverlay.get_static_pad('video_sink')
    #              .query_caps(None).to_string())
    _caps = ('video/x-raw, format=(string){ BGRx, RGBx, xRGB, xBGR, RGBA, BGRA,'
             ' ARGB, ABGR, RGB, BGR, I420, YV12, AYUV, YUY2, UYVY, v308, Y41B, '
             'Y42B, Y444, NV12, NV21, A420, YUV9, YVU9, IYU1, GRAY8 }, '
             'width=(int)[ 1, 2147483647 ], height=(int)[ 1, 2147483647 ], '
             'framerate=(fraction)[ 0/1, 2147483647/1 ]')

    __gstmetadata__ = (
        'TimeClbFilter plugin', # longname
        'Filter/Video', # classification
        ("A VideoFilter that does no modifications but invokes a callback "
        "method for each frame's timestamp."), # description
        'da-mkay@subsynco.org' # contact
    )

    _srctemplate = Gst.PadTemplate.new(
        'src', # must be 'src' for a VideoFilter
        Gst.PadDirection.SRC,
        Gst.PadPresence.ALWAYS,
        Gst.caps_from_string(_caps)
    )

    _sinktemplate = Gst.PadTemplate.new(
        'sink', # must be 'sink' for a VideoFilter
        Gst.PadDirection.SINK,
        Gst.PadPresence.ALWAYS,
        Gst.caps_from_string(_caps)
    )
    
    # register pad templates
    __gsttemplates__ = (_sinktemplate, _srctemplate)

    def __init__(self, timer_callback=None):
        super(TimeClbFilter, self).__init__()
        self.set_passthrough(True)
        self.set_timer_callback(timer_callback)

    def set_timer_callback(self, callback):
        """Set the callback function that will be called for each
        frame's timestamp (in nanoseconds).
        """
        self._timer_callback = callback

    def do_transform_frame_ip(self, frame):
        # Invoke timer callback (if any) and forward buffer to src
        if (self._timer_callback is not None):
            self._timer_callback(frame.buffer.pts) # nanos
        return Gst.FlowReturn.OK


def _init_plugin(plugin, userarg):
    # Before registering the filter plugin we must ensure that the
    # plugin's metadata and pad templates are set.
    # Usually the data should be set automatically based on the
    # __gstmetadata__ and __gsttemplates__ attributes. This works as
    # expected on:
    #   Xubuntu 14.04
    #     (python-gst-1.0 [1.2.0-1], gstreamer1.0-x [1.2.4-1])
    #   Xubuntu 15.05
    #     (python-gst-1.0 [1.2.1-1.1], gstreamer1.0-x [1.4.5-1])
    # However on Windows 7 running PyGI 3.14.0 AIO rev19 (including
    # gstreamer 1.4.5) these values must be set explicitly using
    # set_metadata and add_pad_template. If we would not set the values
    # explicitly we would get the following warning/error:
    #   GStreamer-WARNING **: Element factory metadata for
    #   'timeclbfilter' has no valid long-name field
    #   CRITICAL **: gst_base_transform_init: assertion 'pad_template !=
    #   NULL' failed
    try:
        TimeClbFilter.set_metadata(*TimeClbFilter.__gstmetadata__)
        TimeClbFilter.add_pad_template(TimeClbFilter._sinktemplate)
        TimeClbFilter.add_pad_template(TimeClbFilter._srctemplate)
    except AttributeError:
        pass
    TimeClbFilterType = GObject.type_register(TimeClbFilter)
    Gst.Element.register(plugin, 'timeclbfilter', 0, TimeClbFilterType)
    return True

version = Gst.version()
Gst.Plugin.register_static_full(
    version[0],  # GST_VERSION_MAJOR
    version[1],  # GST_VERSION_MINOR
    'TimeClbFilter plugin',
    ("A VideoFilter that does no modifications but invokes a callback method "
     "for each frame's timestamp."),
    _init_plugin,
    '1.0',
    'GPL',
    'filter',
    'subsynco.gst',
    'http://subsynco.org',
    None
)

