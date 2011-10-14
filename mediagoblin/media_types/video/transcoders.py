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

from __future__ import division
import sys
import logging
import pdb

_log = logging.getLogger(__name__)
logging.basicConfig()
_log.setLevel(logging.DEBUG)

try:
    import gobject
    gobject.threads_init()
except:
    _log.error('Could not import gobject')
    raise Exception()

try:
    import pygst
    pygst.require('0.10')
    import gst
    from gst import pbutils
    from gst.extend import discoverer
except:
    _log.error('pygst could not be imported')
    raise Exception()


class VideoThumbnailer:
    '''
    Creates a video thumbnail

     - Sets up discoverer & transcoding pipeline.
       Discoverer finds out information about the media file
     - Launches gobject.MainLoop, this triggers the discoverer to start running
     - Once the discoverer is done, it calls the __discovered callback function
     - The __discovered callback function launches the transcoding process
     - The _on_message callback is called from the transcoding process until it gets a 
       message of type gst.MESSAGE_EOS, then it calls __stop which shuts down the
       gobject.MainLoop
    '''
    def __init__(self, src, dst, **kwargs):
        _log.info('Initializing VideoThumbnailer...')

        self.loop = gobject.MainLoop()
        self.source_path = src
        self.destination_path = dst

        self.destination_dimensions = kwargs.get('dimensions') or (180, 180)

        if not type(self.destination_dimensions) == tuple:
            raise Exception('dimensions must be tuple: (width, height)')

        self._setup()
        self._run()

    def _setup(self):
        self._setup_pass()
        self._setup_discover()

    def _run(self):
        _log.info('Discovering...')
        self.discoverer.discover()
        _log.info('Done')

        _log.debug('Initializing MainLoop()')
        self.loop.run()

    def _setup_discover(self):
        self.discoverer = discoverer.Discoverer(self.source_path)

        # Connect self.__discovered to the 'discovered' event
        self.discoverer.connect('discovered', self.__discovered)

    def __discovered(self, data, is_media):
        '''
        Callback for media discoverer.
        '''
        if not is_media:
            self.__stop()
            raise Exception('Could not discover {0}'.format(self.source_path))

        _log.debug('__discovered, data: {0}'.format(data))

        self.data = data

        self._on_discovered()

        # Tell the transcoding pipeline to start running
        self.pipeline.set_state(gst.STATE_PLAYING)
        _log.info('Transcoding...')

    def _on_discovered(self):
        self.__setup_capsfilter()

    def _setup_pass(self):
        self.pipeline = gst.Pipeline('VideoThumbnailerPipeline')

        self.filesrc = gst.element_factory_make('filesrc', 'filesrc')
        self.filesrc.set_property('location', self.source_path)
        self.pipeline.add(self.filesrc)

        self.decoder = gst.element_factory_make('decodebin2', 'decoder')

        self.decoder.connect('new-decoded-pad', self._on_dynamic_pad)
        self.pipeline.add(self.decoder)

        self.ffmpegcolorspace = gst.element_factory_make('ffmpegcolorspace', 'ffmpegcolorspace')
        self.pipeline.add(self.ffmpegcolorspace)

        self.videoscale = gst.element_factory_make('videoscale', 'videoscale')
        self.videoscale.set_property('method', 'bilinear')
        self.pipeline.add(self.videoscale)

        self.capsfilter = gst.element_factory_make('capsfilter', 'capsfilter')
        self.pipeline.add(self.capsfilter)

        self.jpegenc = gst.element_factory_make('jpegenc', 'jpegenc')
        self.pipeline.add(self.jpegenc)

        self.filesink = gst.element_factory_make('filesink', 'filesink')
        self.filesink.set_property('location', self.destination_path)
        self.pipeline.add(self.filesink)

        # Link all the elements together
        self.filesrc.link(self.decoder)
        self.ffmpegcolorspace.link(self.videoscale)
        self.videoscale.link(self.capsfilter)
        self.capsfilter.link(self.jpegenc)
        self.jpegenc.link(self.filesink)

        self._setup_bus()

    def _setup_bus(self):
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self._on_message)

    def __setup_capsfilter(self):
        thumbsizes = self.calculate_resize()  # Returns tuple with (width, height)

        self.capsfilter.set_property(
            'caps',
            gst.caps_from_string('video/x-raw-rgb, width={width}, height={height}'.format(
                    width=thumbsizes[0],
                    height=thumbsizes[1]
                    )))

    def calculate_resize(self):
        x_ratio = self.destination_dimensions[0] / self.data.videowidth
        y_ratio = self.destination_dimensions[1] / self.data.videoheight

        if self.data.videoheight > self.data.videowidth:
            # We're dealing with a portrait!
            dimensions = (
                int(self.data.videowidth * y_ratio),
                180)
        else:
            dimensions = (
                180,
                int(self.data.videoheight * x_ratio))

        return dimensions

    def _on_message(self, bus, message):
        _log.debug((bus, message))

        t = message.type

        if t == gst.MESSAGE_EOS:
            self.__stop()
            _log.info('Done')
        elif t == gst.MESSAGE_ERROR:
            _log.error((bus, message))
            self.__stop()

    def _on_dynamic_pad(self, dbin, pad, islast):
        '''
        Callback called when ``decodebin2`` has a pad that we can connect to
        '''
        pad.link(
            self.ffmpegcolorspace.get_pad('sink'))

    def __stop(self):
        _log.debug(self.loop)

        self.pipeline.set_state(gst.STATE_NULL)

        gobject.idle_add(self.loop.quit)


class VideoTranscoder:
    '''
    Video transcoder

    Transcodes the SRC video file to a VP8 WebM video file at DST

    TODO:
    - Audio pipeline
    '''
    def __init__(self, src, dst, **kwargs):
        _log.info('Initializing VideoTranscoder...')

        self.loop = gobject.MainLoop()
        self.source_path = src
        self.destination_path = dst

        self.destination_dimensions = kwargs.get('dimensions') or (640, 640)

        if not type(self.destination_dimensions) == tuple:
            raise Exception('dimensions must be tuple: (width, height)')

        self._setup()
        self._run()

    def _setup(self):
        self._setup_pass()
        self._setup_discover()

    def _run(self):
        _log.info('Discovering...')
        self.discoverer.discover()
        _log.info('Done')

        _log.debug('Initializing MainLoop()')
        self.loop.run()

    def _setup_discover(self):
        self.discoverer = discoverer.Discoverer(self.source_path)

        # Connect self.__discovered to the 'discovered' event
        self.discoverer.connect('discovered', self.__discovered)

    def __discovered(self, data, is_media):
        '''
        Callback for media discoverer.
        '''
        if not is_media:
            self.__stop()
            raise Exception('Could not discover {0}'.format(self.source_path))

        _log.debug('__discovered, data: {0}'.format(data))

        self.data = data

        self._on_discovered()

        # Tell the transcoding pipeline to start running
        self.pipeline.set_state(gst.STATE_PLAYING)
        _log.info('Transcoding...')

    def _on_discovered(self):
        self.__setup_videoscale_capsfilter()

    def _setup_pass(self):
        self.pipeline = gst.Pipeline('VideoTranscoderPipeline')

        self.filesrc = gst.element_factory_make('filesrc', 'filesrc')
        self.filesrc.set_property('location', self.source_path)
        self.pipeline.add(self.filesrc)

        self.decoder = gst.element_factory_make('decodebin2', 'decoder')

        self.decoder.connect('new-decoded-pad', self._on_dynamic_pad)
        self.pipeline.add(self.decoder)

        self.ffmpegcolorspace = gst.element_factory_make('ffmpegcolorspace', 'ffmpegcolorspace')
        self.pipeline.add(self.ffmpegcolorspace)

        self.videoscale = gst.element_factory_make('videoscale', 'videoscale')
        self.videoscale.set_property('method', 2)  # I'm not sure this works
        self.videoscale.set_property('add-borders', 0)
        self.pipeline.add(self.videoscale)

        self.capsfilter = gst.element_factory_make('capsfilter', 'capsfilter')
        self.pipeline.add(self.capsfilter)

        self.vp8enc = gst.element_factory_make('vp8enc', 'vp8enc')
        self.vp8enc.set_property('quality', 6)
        self.vp8enc.set_property('threads', 2)
        self.vp8enc.set_property('speed', 2)
        self.pipeline.add(self.vp8enc)


        # Audio
        self.audioconvert = gst.element_factory_make('audioconvert', 'audioconvert')
        self.pipeline.add(self.audioconvert)

        self.vorbisenc = gst.element_factory_make('vorbisenc', 'vorbisenc')
        self.vorbisenc.set_property('quality', 0.7)
        self.pipeline.add(self.vorbisenc)


        self.webmmux = gst.element_factory_make('webmmux', 'webmmux')
        self.pipeline.add(self.webmmux)

        self.filesink = gst.element_factory_make('filesink', 'filesink')
        self.filesink.set_property('location', self.destination_path)
        self.pipeline.add(self.filesink)

        self.filesrc.link(self.decoder)
        self.ffmpegcolorspace.link(self.videoscale)
        self.videoscale.link(self.capsfilter)
        self.capsfilter.link(self.vp8enc)
        self.vp8enc.link(self.webmmux)

        # Audio
        self.audioconvert.link(self.vorbisenc)
        self.vorbisenc.link(self.webmmux)

        self.webmmux.link(self.filesink)

        self._setup_bus()

    def _on_dynamic_pad(self, dbin, pad, islast):
        '''
        Callback called when ``decodebin2`` has a pad that we can connect to
        '''
        _log.debug('Linked {0}'.format(pad))

        #pdb.set_trace()

        if self.ffmpegcolorspace.get_pad_template('sink')\
                .get_caps().intersect(pad.get_caps()).is_empty():
            pad.link(
                self.audioconvert.get_pad('sink'))
        else:
            pad.link(
                self.ffmpegcolorspace.get_pad('sink'))

    def _setup_bus(self):
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self._on_message)

    def __setup_videoscale_capsfilter(self):
        caps = ['video/x-raw-yuv', 'pixel-aspect-ratio=1/1']

        if self.data.videoheight > self.data.videowidth:
            # Whoa! We have ourselves a portrait video!
            caps.append('height={0}'.format(
                    self.destination_dimensions[1]))
        else:
            # It's a landscape, phew, how normal.
            caps.append('width={0}'.format(
                    self.destination_dimensions[0]))

        self.capsfilter.set_property(
            'caps',
            gst.caps_from_string(
                ', '.join(caps)))
        gst.DEBUG_BIN_TO_DOT_FILE (
            self.pipeline,
            gst.DEBUG_GRAPH_SHOW_ALL,
            'supersimple-debug-graph')

    def _on_message(self, bus, message):
        _log.debug((bus, message))

        t = message.type

        if t == gst.MESSAGE_EOS:
            self._discover_dst_and_stop()
            _log.info('Done')
        elif t == gst.MESSAGE_ERROR:
            _log.error((bus, message))
            self.__stop()

    def _discover_dst_and_stop(self):
        self.dst_discoverer = discoverer.Discoverer(self.destination_path)

        self.dst_discoverer.connect('discovered', self.__dst_discovered)

        self.dst_discoverer.discover()


    def __dst_discovered(self, data, is_media):
        self.dst_data = data

        self.__stop()

    def __stop(self):
        _log.debug(self.loop)

        self.pipeline.set_state(gst.STATE_NULL)

        gobject.idle_add(self.loop.quit)


if __name__ == '__main__':
    import os
    os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/tmp"
    os.putenv('GST_DEBUG_DUMP_DOT_DIR', '/tmp')
    from optparse import OptionParser

    parser = OptionParser(
        usage='%prog [-v] -a [ video | thumbnail ] SRC DEST')

    parser.add_option('-a', '--action',
                      dest='action',
                      help='One of "video" or "thumbnail"')

    parser.add_option('-v',
                      dest='verbose',
                      action='store_true',
                      help='Output debug information')

    parser.add_option('-q',
                      dest='quiet',
                      action='store_true',
                      help='Dear program, please be quiet unless *error*')

    (options, args) = parser.parse_args()

    if options.verbose:
        _log.setLevel(logging.DEBUG)
    else:
        _log.setLevel(logging.INFO)

    if options.quiet:
        _log.setLevel(logging.ERROR)

    _log.debug(args)

    if not len(args) == 2:
        parser.print_help()
        sys.exit()

    if options.action == 'thumbnail':
        VideoThumbnailer(*args)
    elif options.action == 'video':
        transcoder = VideoTranscoder(*args)
        pdb.set_trace()
