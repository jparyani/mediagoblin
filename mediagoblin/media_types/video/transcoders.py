# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import logging

_log = logging.getLogger(__name__)
logging.basicConfig()
_log.setLevel(logging.INFO)

try:
    import gobject
except:
    _log.error('Could not import gobject')

try:
    import pygst
    pygst.require('0.10')
    import gst
except:
    _log.error('pygst could not be imported')


class VideoThumbnailer:
    def __init__(self, src, dst):
        self._set_up_pass(src, dst)

        self.loop = gobject.MainLoop()
        self.loop.run()

    def _set_up_pass(self, src, dst):
        self.pipeline = gst.Pipeline('TranscodingPipeline')

        _log.debug('Pipeline: {0}'.format(self.pipeline))

        self.filesrc = gst.element_factory_make('filesrc', 'filesrc')
        self.filesrc.set_property('location', src)
        self.pipeline.add(self.filesrc)

        self.decoder = gst.element_factory_make('decodebin2', 'decoder')

        self.decoder.connect('new-decoded-pad', self._on_dynamic_pad)
        self.pipeline.add(self.decoder)

        self.ffmpegcolorspace = gst.element_factory_make('ffmpegcolorspace', 'ffmpegcolorspace')
        self.pipeline.add(self.ffmpegcolorspace)

        self.videoscale = gst.element_factory_make('videoscale', 'videoscale')
        self.pipeline.add(self.videoscale)

        self.capsfilter = gst.element_factory_make('capsfilter', 'capsfilter')
        # FIXME: videoscale doesn't care about original ratios
        self.capsfilter.set_property('caps', gst.caps_from_string('video/x-raw-rgb, width=180, height=100'))
        self.pipeline.add(self.capsfilter)

        self.jpegenc = gst.element_factory_make('jpegenc', 'jpegenc')
        self.pipeline.add(self.jpegenc)

        self.filesink = gst.element_factory_make('filesink', 'filesink')
        self.filesink.set_property('location', dst)
        self.pipeline.add(self.filesink)

        # Link all the elements together
        self.filesrc.link(self.decoder)
        self.ffmpegcolorspace.link(self.videoscale)
        self.videoscale.link(self.capsfilter)
        self.capsfilter.link(self.jpegenc)
        self.jpegenc.link(self.filesink)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_message)

        self.pipeline.set_state(gst.STATE_PLAYING)


    def _on_message(self, bus, message):
        _log.info((bus, message))

        t = message.type

        if t == gst.MESSAGE_EOS:
            self.__shutdown()

    def _on_dynamic_pad(self, dbin, pad, islast):
        '''
        Callback called when ``decodebin2`` has a pad that we can connect to
        '''
        pad.link(
            self.ffmpegcolorspace.get_pad('sink'))

    def __shutdown(self):
        _log.debug(self.loop)

        self.pipeline.set_state(gst.STATE_NULL)

        gobject.idle_add(self.loop.quit)


if __name__ == '__main__':
    VideoThumbnailer('/home/joar/Dropbox/Public/blender/fluid-box.mp4', '/tmp/dest.jpg')
    VideoThumbnailer('/home/joar/Dropbox/iPhone/Video 2011-10-05 21 58 03.mov', '/tmp/dest2.jpg')
