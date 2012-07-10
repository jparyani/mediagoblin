# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
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

import os
import sys
import logging
import urllib
import multiprocessing
import gobject
import pygst
pygst.require('0.10')
import gst
import struct
import Image

from gst.extend import discoverer

_log = logging.getLogger(__name__)

gobject.threads_init()

CPU_COUNT = 2

try:
    CPU_COUNT = multiprocessing.cpu_count()
except NotImplementedError:
    _log.warning('multiprocessing.cpu_count not implemented')

os.putenv('GST_DEBUG_DUMP_DOT_DIR', '/tmp')


def pixbuf_to_pilbuf(buf):
    data = list()
    for i in range(0, len(buf), 3):
        r, g, b = struct.unpack('BBB', buf[i:i + 3])
        data.append((r, g, b))

    return data


class VideoThumbnailer:
    # Declaration of thumbnailer states
    STATE_NULL = 0
    STATE_HALTING = 1
    STATE_PROCESSING = 2

    # The current thumbnailer state
    state = STATE_NULL

    # This will contain the thumbnailing pipeline
    thumbnail_pipeline = None

    buffer_probes = {}

    def __init__(self, source_path, dest_path):
        '''
        Set up playbin pipeline in order to get video properties.

        Initializes and runs the gobject.MainLoop()

        Abstract
        - Set up a playbin with a fake audio sink and video sink. Load the video
          into the playbin
        - Initialize
        '''
        self.errors = []

        self.source_path = source_path
        self.dest_path = dest_path

        self.loop = gobject.MainLoop()

        # Set up the playbin. It will be used to discover certain
        # properties of the input file
        self.playbin = gst.element_factory_make('playbin')

        self.videosink = gst.element_factory_make('fakesink', 'videosink')
        self.playbin.set_property('video-sink', self.videosink)

        self.audiosink = gst.element_factory_make('fakesink', 'audiosink')
        self.playbin.set_property('audio-sink', self.audiosink)

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()
        self.watch_id = self.bus.connect('message', self._on_bus_message)

        self.playbin.set_property('uri', 'file:{0}'.format(
                urllib.pathname2url(self.source_path)))

        self.playbin.set_state(gst.STATE_PAUSED)

        self.run()

    def run(self):
        self.loop.run()

    def _on_bus_message(self, bus, message):
        _log.debug(' thumbnail playbin: {0}'.format(message))

        if message.type == gst.MESSAGE_ERROR:
            _log.error('thumbnail playbin: {0}'.format(message))
            gobject.idle_add(self._on_bus_error)

        elif message.type == gst.MESSAGE_STATE_CHANGED:
            # The pipeline state has changed
            # Parse state changing data
            _prev, state, _pending = message.parse_state_changed()

            _log.debug('State changed: {0}'.format(state))

            if state == gst.STATE_PAUSED:
                if message.src == self.playbin:
                    gobject.idle_add(self._on_bus_paused)

    def _on_bus_paused(self):
        '''
        Set up thumbnailing pipeline
        '''
        current_video = self.playbin.get_property('current-video')

        if current_video == 0:
            _log.debug('Found current video from playbin')
        else:
            _log.error('Could not get any current video from playbin!')

        self.duration = self._get_duration(self.playbin)
        _log.info('Video length: {0}'.format(self.duration / gst.SECOND))

        _log.info('Setting up thumbnailing pipeline')
        self.thumbnail_pipeline = gst.parse_launch(
            'filesrc location="{0}" ! decodebin ! '
            'ffmpegcolorspace ! videoscale ! '
            'video/x-raw-rgb,depth=24,bpp=24,pixel-aspect-ratio=1/1,width=180 ! '
            'fakesink signal-handoffs=True'.format(self.source_path))

        self.thumbnail_bus = self.thumbnail_pipeline.get_bus()
        self.thumbnail_bus.add_signal_watch()
        self.thumbnail_watch_id = self.thumbnail_bus.connect(
            'message', self._on_thumbnail_bus_message)

        self.thumbnail_pipeline.set_state(gst.STATE_PAUSED)

        #gobject.timeout_add(3000, self._on_timeout)

        return False

    def _on_thumbnail_bus_message(self, bus, message):
        _log.debug('thumbnail: {0}'.format(message))

        if message.type == gst.MESSAGE_ERROR:
            _log.error(message)
            gobject.idle_add(self._on_bus_error)

        if message.type == gst.MESSAGE_STATE_CHANGED:
            _log.debug('State changed')
            _prev, state, _pending = message.parse_state_changed()

            if (state == gst.STATE_PAUSED and
                not self.state == self.STATE_PROCESSING and
                message.src == self.thumbnail_pipeline):
                _log.info('Pipeline paused, processing')
                self.state = self.STATE_PROCESSING

                for sink in self.thumbnail_pipeline.sinks():
                    name = sink.get_name()
                    factoryname = sink.get_factory().get_name()

                    if factoryname == 'fakesink':
                        sinkpad = sink.get_pad('sink')

                        self.buffer_probes[name] = sinkpad.add_buffer_probe(
                            self.buffer_probe_handler, name)

                        _log.info('Added buffer probe')

                        break

                # Apply the wadsworth constant, fallback to 1 second
                # TODO: Will break if video is shorter than 1 sec
                seek_amount = max(self.duration / 100 * 30, 1 * gst.SECOND)

                _log.debug('seek amount: {0}'.format(seek_amount))

                seek_result = self.thumbnail_pipeline.seek(
                    1.0,
                    gst.FORMAT_TIME,
                    gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE,
                    gst.SEEK_TYPE_SET,
                    seek_amount,
                    gst.SEEK_TYPE_NONE,
                    0)

                if not seek_result:
                    self.errors.append('COULD_NOT_SEEK')
                    _log.error('Couldn\'t seek! result: {0}'.format(
                            seek_result))
                    _log.info(message)
                    self.shutdown()
                else:
                    _log.debug('Seek successful')
                    self.thumbnail_pipeline.set_state(gst.STATE_PAUSED)
            else:
                _log.debug('Won\'t seek: \t{0}\n\t{1}'.format(
                    self.state,
                    message.src))

    def buffer_probe_handler_real(self, pad, buff, name):
        '''
        Capture buffers as gdk_pixbufs when told to.
        '''
        _log.info('Capturing frame')
        try:
            caps = buff.caps
            if caps is None:
                _log.error('No caps passed to buffer probe handler!')
                self.shutdown()
                return False

            _log.debug('caps: {0}'.format(caps))

            filters = caps[0]
            width = filters["width"]
            height = filters["height"]

            im = Image.new('RGB', (width, height))

            data = pixbuf_to_pilbuf(buff.data)

            im.putdata(data)

            im.save(self.dest_path)

            _log.info('Saved thumbnail')

            self.shutdown()

        except gst.QueryError as e:
            _log.error('QueryError: {0}'.format(e))

        return False

    def buffer_probe_handler(self, pad, buff, name):
        '''
        Proxy function for buffer_probe_handler_real
        '''
        _log.debug('Attaching real buffer handler to gobject idle event')
        gobject.idle_add(
            lambda: self.buffer_probe_handler_real(pad, buff, name))

        return True

    def _get_duration(self, pipeline, retries=0):
        '''
        Get the duration of a pipeline.

        Retries 5 times.
        '''
        if retries == 5:
            return 0

        try:
            return pipeline.query_duration(gst.FORMAT_TIME)[0]
        except gst.QueryError:
            return self._get_duration(pipeline, retries + 1)

    def _on_timeout(self):
        _log.error('Timeout in thumbnailer!')
        self.shutdown()

    def _on_bus_error(self, *args):
        _log.error('AHAHAHA! Error! args: {0}'.format(args))

    def shutdown(self):
        '''
        Tell gobject to call __halt when the mainloop is idle.
        '''
        _log.info('Shutting down')
        self.__halt()

    def __halt(self):
        '''
        Halt all pipelines and shut down the main loop
        '''
        _log.info('Halting...')
        self.state = self.STATE_HALTING

        self.__disconnect()

        gobject.idle_add(self.__halt_final)

    def __disconnect(self):
        _log.debug('Disconnecting...')
        if not self.playbin is None:
            self.playbin.set_state(gst.STATE_NULL)
            for sink in self.playbin.sinks():
                name = sink.get_name()
                factoryname = sink.get_factory().get_name()

                _log.debug('Disconnecting {0}'.format(name))

                if factoryname == "fakesink":
                    pad = sink.get_pad("sink")
                    pad.remove_buffer_probe(self.buffer_probes[name])
                    del self.buffer_probes[name]

        self.playbin = None

        if self.bus is not None:
            self.bus.disconnect(self.watch_id)
            self.bus = None

    def __halt_final(self):
        _log.info('Done')
        if self.errors:
            _log.error(','.join(self.errors))

        self.loop.quit()


class VideoTranscoder:
    '''
    Video transcoder

    Transcodes the SRC video file to a VP8 WebM video file at DST

     - Does the same thing as VideoThumbnailer, but produces a WebM vp8
       and vorbis video file.
     - The VideoTranscoder exceeds the VideoThumbnailer in the way
       that it was refined afterwards and therefore is done more
       correctly.
    '''
    def __init__(self):
        _log.info('Initializing VideoTranscoder...')

        self.loop = gobject.MainLoop()

    def transcode(self, src, dst, **kwargs):
        '''
        Transcode a video file into a 'medium'-sized version.
        '''
        self.source_path = src
        self.destination_path = dst

        # vp8enc options
        self.destination_dimensions = kwargs.get('dimensions', (640, 640))
        self.vp8_quality = kwargs.get('vp8_quality', 8)
        # Number of threads used by vp8enc:
        # number of real cores - 1 as per recommendation on
        # <http://www.webmproject.org/tools/encoder-parameters/#6-multi-threaded-encode-and-decode>
        self.vp8_threads = kwargs.get('vp8_threads', CPU_COUNT - 1)

        # 0 means auto-detect, but dict.get() only falls back to CPU_COUNT
        # if value is None, this will correct our incompatibility with
        # dict.get()
        # This will also correct cases where there's only 1 CPU core, see
        # original self.vp8_threads assignment above.
        if self.vp8_threads == 0:
            self.vp8_threads = CPU_COUNT

        # vorbisenc options
        self.vorbis_quality = kwargs.get('vorbis_quality', 0.3)

        self._progress_callback = kwargs.get('progress_callback') or None

        if not type(self.destination_dimensions) == tuple:
            raise Exception('dimensions must be tuple: (width, height)')

        self._setup()
        self._run()

    def discover(self, src):
        '''
        Discover properties about a media file
        '''
        _log.info('Discovering {0}'.format(src))

        self.source_path = src
        self._setup_discover(discovered_callback=self.__on_discovered)

        self.discoverer.discover()

        self.loop.run()

        if hasattr(self, '_discovered_data'):
            return self._discovered_data.__dict__
        else:
            return None

    def __on_discovered(self, data, is_media):
        _log.debug('Discovered: {0}'.format(data))
        if not is_media:
            self.__stop()
            raise Exception('Could not discover {0}'.format(self.source_path))

        self._discovered_data = data

        self.__stop_mainloop()

    def _setup(self):
        self._setup_discover()
        self._setup_pipeline()

    def _run(self):
        _log.info('Discovering...')
        self.discoverer.discover()
        _log.info('Done')

        _log.debug('Initializing MainLoop()')
        self.loop.run()

    def _setup_discover(self, **kw):
        _log.debug('Setting up discoverer')
        self.discoverer = discoverer.Discoverer(self.source_path)

        # Connect self.__discovered to the 'discovered' event
        self.discoverer.connect(
            'discovered',
            kw.get('discovered_callback', self.__discovered))

    def __discovered(self, data, is_media):
        '''
        Callback for media discoverer.
        '''
        if not is_media:
            self.__stop()
            raise Exception('Could not discover {0}'.format(self.source_path))

        _log.debug('__discovered, data: {0}'.format(data.__dict__))

        self.data = data

        # Launch things that should be done after discovery
        self._link_elements()
        self.__setup_videoscale_capsfilter()

        # Tell the transcoding pipeline to start running
        self.pipeline.set_state(gst.STATE_PLAYING)
        _log.info('Transcoding...')

    def _setup_pipeline(self):
        _log.debug('Setting up transcoding pipeline')
        # Create the pipeline bin.
        self.pipeline = gst.Pipeline('VideoTranscoderPipeline')

        # Create all GStreamer elements, starting with
        # filesrc & decoder
        self.filesrc = gst.element_factory_make('filesrc', 'filesrc')
        self.filesrc.set_property('location', self.source_path)
        self.pipeline.add(self.filesrc)

        self.decoder = gst.element_factory_make('decodebin2', 'decoder')
        self.decoder.connect('new-decoded-pad', self._on_dynamic_pad)
        self.pipeline.add(self.decoder)

        # Video elements
        self.videoqueue = gst.element_factory_make('queue', 'videoqueue')
        self.pipeline.add(self.videoqueue)

        self.videorate = gst.element_factory_make('videorate', 'videorate')
        self.pipeline.add(self.videorate)

        self.ffmpegcolorspace = gst.element_factory_make(
            'ffmpegcolorspace', 'ffmpegcolorspace')
        self.pipeline.add(self.ffmpegcolorspace)

        self.videoscale = gst.element_factory_make('ffvideoscale', 'videoscale')
        #self.videoscale.set_property('method', 2)  # I'm not sure this works
        #self.videoscale.set_property('add-borders', 0)
        self.pipeline.add(self.videoscale)

        self.capsfilter = gst.element_factory_make('capsfilter', 'capsfilter')
        self.pipeline.add(self.capsfilter)

        self.vp8enc = gst.element_factory_make('vp8enc', 'vp8enc')
        self.vp8enc.set_property('quality', self.vp8_quality)
        self.vp8enc.set_property('threads', self.vp8_threads)
        self.vp8enc.set_property('max-latency', 25)
        self.pipeline.add(self.vp8enc)

        # Audio elements
        self.audioqueue = gst.element_factory_make('queue', 'audioqueue')
        self.pipeline.add(self.audioqueue)

        self.audiorate = gst.element_factory_make('audiorate', 'audiorate')
        self.audiorate.set_property('tolerance', 80000000)
        self.pipeline.add(self.audiorate)

        self.audioconvert = gst.element_factory_make('audioconvert', 'audioconvert')
        self.pipeline.add(self.audioconvert)

        self.audiocapsfilter = gst.element_factory_make('capsfilter', 'audiocapsfilter')
        audiocaps = ['audio/x-raw-float']
        self.audiocapsfilter.set_property(
            'caps',
            gst.caps_from_string(
                ','.join(audiocaps)))
        self.pipeline.add(self.audiocapsfilter)

        self.vorbisenc = gst.element_factory_make('vorbisenc', 'vorbisenc')
        self.vorbisenc.set_property('quality', self.vorbis_quality)
        self.pipeline.add(self.vorbisenc)

        # WebMmux & filesink
        self.webmmux = gst.element_factory_make('webmmux', 'webmmux')
        self.pipeline.add(self.webmmux)

        self.filesink = gst.element_factory_make('filesink', 'filesink')
        self.filesink.set_property('location', self.destination_path)
        self.pipeline.add(self.filesink)

        # Progressreport
        self.progressreport = gst.element_factory_make(
            'progressreport', 'progressreport')
        # Update every second
        self.progressreport.set_property('update-freq', 1)
        self.progressreport.set_property('silent', True)
        self.pipeline.add(self.progressreport)

    def _link_elements(self):
        '''
        Link all the elements

        This code depends on data from the discoverer and is called
        from __discovered
        '''
        _log.debug('linking elements')
        # Link the filesrc element to the decoder. The decoder then emits
        # 'new-decoded-pad' which links decoded src pads to either a video
        # or audio sink
        self.filesrc.link(self.decoder)

        # Link all the video elements in a row to webmmux
        gst.element_link_many(
            self.videoqueue,
            self.videorate,
            self.ffmpegcolorspace,
            self.videoscale,
            self.capsfilter,
            self.vp8enc,
            self.webmmux)

        if self.data.is_audio:
            # Link all the audio elements in a row to webmux
            gst.element_link_many(
                self.audioqueue,
                self.audiorate,
                self.audioconvert,
                self.audiocapsfilter,
                self.vorbisenc,
                self.webmmux)

        gst.element_link_many(
            self.webmmux,
            self.progressreport,
            self.filesink)

        # Setup the message bus and connect _on_message to the pipeline
        self._setup_bus()

    def _on_dynamic_pad(self, dbin, pad, islast):
        '''
        Callback called when ``decodebin2`` has a pad that we can connect to
        '''
        # Intersect the capabilities of the video sink and the pad src
        # Then check if they have no common capabilities.
        if self.ffmpegcolorspace.get_pad_template('sink')\
                .get_caps().intersect(pad.get_caps()).is_empty():
            # It is NOT a video src pad.
            pad.link(self.audioqueue.get_pad('sink'))
        else:
            # It IS a video src pad.
            pad.link(self.videoqueue.get_pad('sink'))

    def _setup_bus(self):
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self._on_message)

    def __setup_videoscale_capsfilter(self):
        '''
        Sets up the output format (width, height) for the video
        '''
        caps = ['video/x-raw-yuv', 'pixel-aspect-ratio=1/1', 'framerate=30/1']

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
                ','.join(caps)))

    def _on_message(self, bus, message):
        _log.debug((bus, message, message.type))

        t = message.type

        if message.type == gst.MESSAGE_EOS:
            self._discover_dst_and_stop()
            _log.info('Done')

        elif message.type == gst.MESSAGE_ELEMENT:
            if message.structure.get_name() == 'progress':
                data = dict(message.structure)

                if self._progress_callback:
                    self._progress_callback(data.get('percent'))

                _log.info('{percent}% done...'.format(
                        percent=data.get('percent')))
                _log.debug(data)

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

        if hasattr(self, 'pipeline'):
            # Stop executing the pipeline
            self.pipeline.set_state(gst.STATE_NULL)

        # This kills the loop, mercifully
        gobject.idle_add(self.__stop_mainloop)

    def __stop_mainloop(self):
        '''
        Wrapper for gobject.MainLoop.quit()

        This wrapper makes us able to see if self.loop.quit has been called
        '''
        _log.info('Terminating MainLoop')

        self.loop.quit()


if __name__ == '__main__':
    os.nice(19)
    logging.basicConfig()
    from optparse import OptionParser

    parser = OptionParser(
        usage='%prog [-v] -a [ video | thumbnail | discover ] SRC [ DEST ]')

    parser.add_option('-a', '--action',
                      dest='action',
                      help='One of "video", "discover" or "thumbnail"')

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

    if not len(args) == 2 and not options.action == 'discover':
        parser.print_help()
        sys.exit()

    transcoder = VideoTranscoder()

    if options.action == 'thumbnail':
        VideoThumbnailer(*args)
    elif options.action == 'video':
        def cb(data):
            print('I\'m a callback!')
        transcoder.transcode(*args, progress_callback=cb)
    elif options.action == 'discover':
        print transcoder.discover(*args).__dict__
