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

import logging
try:
    from PIL import Image
except ImportError:
    import Image

from mediagoblin.processing import BadMediaFail
from mediagoblin.media_types.audio import audioprocessing


_log = logging.getLogger(__name__)

CPU_COUNT = 2  # Just assuming for now

# IMPORT MULTIPROCESSING
try:
    import multiprocessing
    try:
        CPU_COUNT = multiprocessing.cpu_count()
    except NotImplementedError:
        _log.warning('multiprocessing.cpu_count not implemented!\n'
                     'Assuming 2 CPU cores')
except ImportError:
    _log.warning('Could not import multiprocessing, assuming 2 CPU cores')

# IMPORT GOBJECT
try:
    import gobject
    gobject.threads_init()
except ImportError:
    raise Exception('gobject could not be found')

# IMPORT PYGST
try:
    import pygst

    # We won't settle for less. For now, this is an arbitrary limit
    # as we have not tested with > 0.10
    pygst.require('0.10')

    import gst

    import gst.extend.discoverer
except ImportError:
    raise Exception('gst/pygst >= 0.10 could not be imported')

import numpy


class AudioThumbnailer(object):
    def __init__(self):
        _log.info('Initializing {0}'.format(self.__class__.__name__))

    def spectrogram(self, src, dst, **kw):
        width = kw['width']
        height = int(kw.get('height', float(width) * 0.3))
        fft_size = kw.get('fft_size', 2048)
        callback = kw.get('progress_callback')

        processor = audioprocessing.AudioProcessor(
            src,
            fft_size,
            numpy.hanning)

        samples_per_pixel = processor.audio_file.nframes / float(width)

        spectrogram = audioprocessing.SpectrogramImage(width, height, fft_size)

        for x in range(width):
            if callback and x % (width / 10) == 0:
                callback((x * 100) / width)

            seek_point = int(x * samples_per_pixel)

            (spectral_centroid, db_spectrum) = processor.spectral_centroid(
                seek_point)

            spectrogram.draw_spectrum(x, db_spectrum)

        if callback:
            callback(100)

        spectrogram.save(dst)

    def thumbnail_spectrogram(self, src, dst, thumb_size):
        '''
        Takes a spectrogram and creates a thumbnail from it
        '''
        if not (type(thumb_size) == tuple and len(thumb_size) == 2):
            raise Exception('thumb_size argument should be a tuple(width, height)')

        im = Image.open(src)

        im_w, im_h = [float(i) for i in im.size]
        th_w, th_h = [float(i) for i in thumb_size]

        wadsworth_position = im_w * 0.3

        start_x = max((
                wadsworth_position - ((im_h * (th_w / th_h)) / 2.0),
                0.0))

        stop_x = start_x + (im_h * (th_w / th_h))

        th = im.crop((
                int(start_x), 0,
                int(stop_x), int(im_h)))

        th.thumbnail(thumb_size, Image.ANTIALIAS)

        th.save(dst)


class AudioTranscoder(object):
    def __init__(self):
        _log.info('Initializing {0}'.format(self.__class__.__name__))

        # Instantiate MainLoop
        self._loop = gobject.MainLoop()
        self._failed = None

    def discover(self, src):
        self._src_path = src
        _log.info('Discovering {0}'.format(src))
        self._discovery_path = src

        self._discoverer = gst.extend.discoverer.Discoverer(
            self._discovery_path)
        self._discoverer.connect('discovered', self.__on_discovered)
        self._discoverer.discover()

        self._loop.run()  # Run MainLoop

        if self._failed:
            raise self._failed

        # Once MainLoop has returned, return discovery data
        return getattr(self, '_discovery_data', False)

    def __on_discovered(self, data, is_media):
        if not is_media:
            self._failed = BadMediaFail()
            _log.error('Could not discover {0}'.format(self._src_path))
            self.halt()

        _log.debug('Discovered: {0}'.format(data.__dict__))

        self._discovery_data = data

        # Gracefully shut down MainLoop
        self.halt()

    def transcode(self, src, dst, **kw):
        _log.info('Transcoding {0} into {1}'.format(src, dst))
        self._discovery_data = kw.get('data', self.discover(src))

        self.__on_progress = kw.get('progress_callback')

        quality = kw.get('quality', 0.3)

        mux_string = kw.get(
            'mux_string',
            'vorbisenc quality={0} ! webmmux'.format(quality))

        # Set up pipeline
        self.pipeline = gst.parse_launch(
            'filesrc location="{src}" ! '
            'decodebin2 ! queue ! audiorate tolerance={tolerance} ! '
            'audioconvert ! audio/x-raw-float,channels=2 ! '
            '{mux_string} ! '
            'progressreport silent=true ! '
            'filesink location="{dst}"'.format(
                src=src,
                tolerance=80000000,
                mux_string=mux_string,
                dst=dst))

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.__on_bus_message)

        self.pipeline.set_state(gst.STATE_PLAYING)

        self._loop.run()

    def __on_bus_message(self, bus, message):
        _log.debug(message)

        if (message.type == gst.MESSAGE_ELEMENT
            and message.structure.get_name() == 'progress'):
            data = dict(message.structure)

            if self.__on_progress:
                self.__on_progress(data.get('percent'))

            _log.info('{0}% done...'.format(
                    data.get('percent')))
        elif message.type == gst.MESSAGE_EOS:
            _log.info('Done')
            self.halt()

    def halt(self):
        if getattr(self, 'pipeline', False):
            self.pipeline.set_state(gst.STATE_NULL)
            del self.pipeline
        _log.info('Quitting MainLoop gracefully...')
        gobject.idle_add(self._loop.quit)

if __name__ == '__main__':
    import sys
    logging.basicConfig()
    _log.setLevel(logging.INFO)

    #transcoder = AudioTranscoder()
    #data = transcoder.discover(sys.argv[1])
    #res = transcoder.transcode(*sys.argv[1:3])

    thumbnailer = AudioThumbnailer()

    thumbnailer.spectrogram(*sys.argv[1:], width=640)
