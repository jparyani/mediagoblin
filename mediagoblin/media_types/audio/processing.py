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

import argparse
import logging
import os

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import (
    BadMediaFail, FilenameBuilder,
    ProgressCallback, MediaProcessor, ProcessingManager,
    request_from_args, get_process_filename,
    store_public, copy_original)

from mediagoblin.media_types.audio.transcoders import (
    AudioTranscoder, AudioThumbnailer)

_log = logging.getLogger(__name__)

MEDIA_TYPE = 'mediagoblin.media_types.audio'


def sniff_handler(media_file, filename):
    _log.info('Sniffing {0}'.format(MEDIA_TYPE))
    try:
        transcoder = AudioTranscoder()
        data = transcoder.discover(media_file.name)
    except BadMediaFail:
        _log.debug('Audio discovery raised BadMediaFail')
        return None

    if data.is_audio is True and data.is_video is False:
        return MEDIA_TYPE

    return None


class CommonAudioProcessor(MediaProcessor):
    """
    Provides a base for various audio processing steps
    """
    acceptable_files = ['original', 'best_quality', 'webm_audio']

    def common_setup(self):
        """
        Setup the workbench directory and pull down the original file, add
        the audio_config, transcoder, thumbnailer and spectrogram_tmp path
        """
        self.audio_config = mgg \
            .global_config['plugins']['mediagoblin.media_types.audio']

        # Pull down and set up the processing file
        self.process_filename = get_process_filename(
            self.entry, self.workbench, self.acceptable_files)
        self.name_builder = FilenameBuilder(self.process_filename)

        self.transcoder = AudioTranscoder()
        self.thumbnailer = AudioThumbnailer()

    def copy_original(self):
        if self.audio_config['keep_original']:
            copy_original(
                self.entry, self.process_filename,
                self.name_builder.fill('{basename}{ext}'))

    def _keep_best(self):
        """
        If there is no original, keep the best file that we have
        """
        if not self.entry.media_files.get('best_quality'):
            # Save the best quality file if no original?
            if not self.entry.media_files.get('original') and \
                    self.entry.media_files.get('webm_audio'):
                self.entry.media_files['best_quality'] = self.entry \
                    .media_files['webm_audio']

    def _skip_processing(self, keyname, **kwargs):
        file_metadata = self.entry.get_file_metadata(keyname)
        skip = True

        if not file_metadata:
            return False

        if keyname == 'webm_audio':
            if kwargs.get('quality') != file_metadata.get('quality'):
                skip = False
        elif keyname == 'spectrogram':
            if kwargs.get('max_width') != file_metadata.get('max_width'):
                skip = False
            elif kwargs.get('fft_size') != file_metadata.get('fft_size'):
                skip = False
        elif keyname == 'thumb':
            if kwargs.get('size') != file_metadata.get('size'):
                skip = False

        return skip

    def transcode(self, quality=None):
        if not quality:
            quality = self.audio_config['quality']

        if self._skip_processing('webm_audio', quality=quality):
            return

        progress_callback = ProgressCallback(self.entry)
        webm_audio_tmp = os.path.join(self.workbench.dir,
                                      self.name_builder.fill(
                                          '{basename}{ext}'))

        self.transcoder.transcode(
            self.process_filename,
            webm_audio_tmp,
            quality=quality,
            progress_callback=progress_callback)

        self.transcoder.discover(webm_audio_tmp)

        self._keep_best()

        _log.debug('Saving medium...')
        store_public(self.entry, 'webm_audio', webm_audio_tmp,
                     self.name_builder.fill('{basename}.medium.webm'))

        self.entry.set_file_metadata('webm_audio', **{'quality': quality})

    def create_spectrogram(self, max_width=None, fft_size=None):
        if not max_width:
            max_width = mgg.global_config['media:medium']['max_width']
        if not fft_size:
            fft_size = self.audio_config['spectrogram_fft_size']

        if self._skip_processing('spectrogram', max_width=max_width,
                                 fft_size=fft_size):
            return

        wav_tmp = os.path.join(self.workbench.dir, self.name_builder.fill(
            '{basename}.ogg'))

        _log.info('Creating OGG source for spectrogram')
        self.transcoder.transcode(
            self.process_filename,
            wav_tmp,
            mux_string='vorbisenc quality={0} ! oggmux'.format(
                self.audio_config['quality']))

        spectrogram_tmp = os.path.join(self.workbench.dir,
                                       self.name_builder.fill(
                                           '{basename}-spectrogram.jpg'))

        self.thumbnailer.spectrogram(
            wav_tmp,
            spectrogram_tmp,
            width=max_width,
            fft_size=fft_size)

        _log.debug('Saving spectrogram...')
        store_public(self.entry, 'spectrogram', spectrogram_tmp,
                     self.name_builder.fill('{basename}.spectrogram.jpg'))

        file_metadata = {'max_width': max_width,
                         'fft_size': fft_size}
        self.entry.set_file_metadata('spectrogram', **file_metadata)

    def generate_thumb(self, size=None):
        if not size:
            max_width = mgg.global_config['media:thumb']['max_width']
            max_height = mgg.global_config['media:thumb']['max_height']
            size = (max_width, max_height)

        if self._skip_processing('thumb', size=size):
            return

        thumb_tmp = os.path.join(self.workbench.dir, self.name_builder.fill(
            '{basename}-thumbnail.jpg'))

        # We need the spectrogram to create a thumbnail
        spectrogram = self.entry.media_files.get('spectrogram')
        if not spectrogram:
            _log.info('No spectrogram found, we will create one.')
            self.create_spectrogram()
            spectrogram = self.entry.media_files['spectrogram']

        spectrogram_filepath = mgg.public_store.get_local_path(spectrogram)

        self.thumbnailer.thumbnail_spectrogram(
            spectrogram_filepath,
            thumb_tmp,
            tuple(size))

        store_public(self.entry, 'thumb', thumb_tmp,
                     self.name_builder.fill('{basename}.thumbnail.jpg'))

        self.entry.set_file_metadata('thumb', **{'size': size})


class InitialProcessor(CommonAudioProcessor):
    """
    Initial processing steps for new audio
    """
    name = "initial"
    description = "Initial processing"

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
        """
        Determine if this media type is eligible for processing
        """
        if not state:
            state = entry.state
        return state in (
            "unprocessed", "failed")

    @classmethod
    def generate_parser(cls):
        parser = argparse.ArgumentParser(
            description=cls.description,
            prog=cls.name)

        parser.add_argument(
            '--quality',
            type=float,
            help='vorbisenc quality. Range: -0.1..1')

        parser.add_argument(
            '--fft_size',
            type=int,
            help='spectrogram fft size')

        parser.add_argument(
            '--thumb_size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int,
            help='minimum size is 100 x 100')

        parser.add_argument(
            '--medium_width',
            type=int,
            help='The width of the spectogram')

        parser.add_argument(
            '--create_spectrogram',
            action='store_true',
            help='Create spectogram and thumbnail, will default to config')

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['create_spectrogram', 'quality', 'fft_size',
                   'thumb_size', 'medium_width'])

    def process(self, quality=None, fft_size=None, thumb_size=None,
                create_spectrogram=None, medium_width=None):
        self.common_setup()

        if not create_spectrogram:
            create_spectrogram = self.audio_config['create_spectrogram']

        self.transcode(quality=quality)
        self.copy_original()

        if create_spectrogram:
            self.create_spectrogram(max_width=medium_width, fft_size=fft_size)
            self.generate_thumb(size=thumb_size)
        self.delete_queue_file()


class Resizer(CommonAudioProcessor):
    """
    Thumbnail and spectogram resizing process steps for processed audio
    """
    name = 'resize'
    description = 'Resize thumbnail or spectogram'
    thumb_size = 'thumb_size'

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
        """
        Determine if this media entry is eligible for processing
        """
        if not state:
            state = entry.state
        return state in 'processed'

    @classmethod
    def generate_parser(cls):
        parser = argparse.ArgumentParser(
            description=cls.description,
            prog=cls.name)

        parser.add_argument(
            '--fft_size',
            type=int,
            help='spectrogram fft size')

        parser.add_argument(
            '--thumb_size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int,
            help='minimum size is 100 x 100')

        parser.add_argument(
            '--medium_width',
            type=int,
            help='The width of the spectogram')

        parser.add_argument(
            'file',
            choices=['thumb', 'spectrogram'])

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['thumb_size', 'file', 'fft_size', 'medium_width'])

    def process(self, file, thumb_size=None, fft_size=None,
                medium_width=None):
        self.common_setup()

        if file == 'thumb':
            self.generate_thumb(size=thumb_size)
        elif file == 'spectrogram':
            self.create_spectrogram(max_width=medium_width, fft_size=fft_size)


class Transcoder(CommonAudioProcessor):
    """
    Transcoding processing steps for processed audio
    """
    name = 'transcode'
    description = 'Re-transcode audio'

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
        if not state:
            state = entry.state
        return state in 'processed'

    @classmethod
    def generate_parser(cls):
        parser = argparse.ArgumentParser(
            description=cls.description,
            prog=cls.name)

        parser.add_argument(
            '--quality',
            help='vorbisenc quality. Range: -0.1..1')

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['quality'])

    def process(self, quality=None):
        self.common_setup()
        self.transcode(quality=quality)


class AudioProcessingManager(ProcessingManager):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.add_processor(InitialProcessor)
        self.add_processor(Resizer)
        self.add_processor(Transcoder)
