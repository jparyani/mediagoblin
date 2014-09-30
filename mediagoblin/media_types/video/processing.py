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
import os.path
import logging
import datetime

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import (
    FilenameBuilder, BaseProcessingFail,
    ProgressCallback, MediaProcessor,
    ProcessingManager, request_from_args,
    get_process_filename, store_public,
    copy_original)
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

from . import transcoders
from .util import skip_transcode

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

MEDIA_TYPE = 'mediagoblin.media_types.video'


class VideoTranscodingFail(BaseProcessingFail):
    '''
    Error raised if video transcoding fails
    '''
    general_message = _(u'Video transcoding failed')


EXCLUDED_EXTS = ["nef", "cr2"]

def sniff_handler(media_file, filename):
    name, ext = os.path.splitext(filename)
    clean_ext = ext.lower()[1:]

    if clean_ext in EXCLUDED_EXTS:
        # We don't handle this filetype, though gstreamer might think we can
        return None

    transcoder = transcoders.VideoTranscoder()
    data = transcoder.discover(media_file.name)

    _log.info('Sniffing {0}'.format(MEDIA_TYPE))
    _log.debug('Discovered: {0}'.format(data))

    if not data:
        _log.error('Could not discover {0}'.format(filename))
        return None

    if data['is_video'] is True:
        return MEDIA_TYPE

    return None


def store_metadata(media_entry, metadata):
    """
    Store metadata from this video for this media entry.
    """
    # Let's pull out the easy, not having to be converted ones first
    stored_metadata = dict(
        [(key, metadata[key])
         for key in [
             "videoheight", "videolength", "videowidth",
             "audiorate", "audiolength", "audiochannels", "audiowidth",
             "mimetype"]
         if key in metadata])

    # We have to convert videorate into a sequence because it's a
    # special type normally..

    if "videorate" in metadata:
        videorate = metadata["videorate"]
        stored_metadata["videorate"] = [videorate.num, videorate.denom]

    # Also make a whitelist conversion of the tags.
    if "tags" in metadata:
        tags_metadata = metadata['tags']

        # we don't use *all* of these, but we know these ones are
        # safe...
        tags = dict(
            [(key, tags_metadata[key])
             for key in [
                 "application-name", "artist", "audio-codec", "bitrate",
                 "container-format", "copyright", "encoder",
                 "encoder-version", "license", "nominal-bitrate", "title",
                 "video-codec"]
             if key in tags_metadata])
        if 'date' in tags_metadata:
            date = tags_metadata['date']
            tags['date'] = "%s-%s-%s" % (
                date.year, date.month, date.day)

        # TODO: handle timezone info; gst.get_time_zone_offset +
        #   python's tzinfo should help
        if 'datetime' in tags_metadata:
            dt = tags_metadata['datetime']
            tags['datetime'] = datetime.datetime(
                dt.get_year(), dt.get_month(), dt.get_day(), dt.get_hour(),
                dt.get_minute(), dt.get_second(),
                dt.get_microsecond()).isoformat()

        stored_metadata['tags'] = tags

    # Only save this field if there's something to save
    if len(stored_metadata):
        media_entry.media_data_init(
            orig_metadata=stored_metadata)


class CommonVideoProcessor(MediaProcessor):
    """
    Provides a base for various video processing steps
    """
    acceptable_files = ['original', 'best_quality', 'webm_video']

    def common_setup(self):
        self.video_config = mgg \
            .global_config['plugins'][MEDIA_TYPE]

        # Pull down and set up the processing file
        self.process_filename = get_process_filename(
            self.entry, self.workbench, self.acceptable_files)
        self.name_builder = FilenameBuilder(self.process_filename)

        self.transcoder = transcoders.VideoTranscoder()
        self.did_transcode = False

    def copy_original(self):
        # If we didn't transcode, then we need to keep the original
        if not self.did_transcode or \
           (self.video_config['keep_original'] and self.did_transcode):
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
                    self.entry.media_files.get('webm_video'):
                self.entry.media_files['best_quality'] = self.entry \
                    .media_files['webm_video']

    def _skip_processing(self, keyname, **kwargs):
        file_metadata = self.entry.get_file_metadata(keyname)

        if not file_metadata:
            return False
        skip = True

        if keyname == 'webm_video':
            if kwargs.get('medium_size') != file_metadata.get('medium_size'):
                skip = False
            elif kwargs.get('vp8_quality') != file_metadata.get('vp8_quality'):
                skip = False
            elif kwargs.get('vp8_threads') != file_metadata.get('vp8_threads'):
                skip = False
            elif kwargs.get('vorbis_quality') != \
                    file_metadata.get('vorbis_quality'):
                skip = False
        elif keyname == 'thumb':
            if kwargs.get('thumb_size') != file_metadata.get('thumb_size'):
                skip = False

        return skip


    def transcode(self, medium_size=None, vp8_quality=None, vp8_threads=None,
                  vorbis_quality=None):
        progress_callback = ProgressCallback(self.entry)
        tmp_dst = os.path.join(self.workbench.dir,
                               self.name_builder.fill('{basename}.medium.webm'))

        if not medium_size:
            medium_size = (
                mgg.global_config['media:medium']['max_width'],
                mgg.global_config['media:medium']['max_height'])
        if not vp8_quality:
            vp8_quality = self.video_config['vp8_quality']
        if not vp8_threads:
            vp8_threads = self.video_config['vp8_threads']
        if not vorbis_quality:
            vorbis_quality = self.video_config['vorbis_quality']

        file_metadata = {'medium_size': medium_size,
                         'vp8_threads': vp8_threads,
                         'vp8_quality': vp8_quality,
                         'vorbis_quality': vorbis_quality}

        if self._skip_processing('webm_video', **file_metadata):
            return

        # Extract metadata and keep a record of it
        metadata = self.transcoder.discover(self.process_filename)
        store_metadata(self.entry, metadata)

        # Figure out whether or not we need to transcode this video or
        # if we can skip it
        if skip_transcode(metadata, medium_size):
            _log.debug('Skipping transcoding')

            dst_dimensions = metadata['videowidth'], metadata['videoheight']

            # If there is an original and transcoded, delete the transcoded
            # since it must be of lower quality then the original
            if self.entry.media_files.get('original') and \
               self.entry.media_files.get('webm_video'):
                self.entry.media_files['webm_video'].delete()

        else:
            self.transcoder.transcode(self.process_filename, tmp_dst,
                                      vp8_quality=vp8_quality,
                                      vp8_threads=vp8_threads,
                                      vorbis_quality=vorbis_quality,
                                      progress_callback=progress_callback,
                                      dimensions=tuple(medium_size))

            dst_dimensions = self.transcoder.dst_data.videowidth,\
                self.transcoder.dst_data.videoheight

            self._keep_best()

            # Push transcoded video to public storage
            _log.debug('Saving medium...')
            store_public(self.entry, 'webm_video', tmp_dst,
                         self.name_builder.fill('{basename}.medium.webm'))
            _log.debug('Saved medium')

            self.entry.set_file_metadata('webm_video', **file_metadata)

            self.did_transcode = True

        # Save the width and height of the transcoded video
        self.entry.media_data_init(
            width=dst_dimensions[0],
            height=dst_dimensions[1])

    def generate_thumb(self, thumb_size=None):
        # Temporary file for the video thumbnail (cleaned up with workbench)
        tmp_thumb = os.path.join(self.workbench.dir,
                                 self.name_builder.fill(
                                     '{basename}.thumbnail.jpg'))

        if not thumb_size:
            thumb_size = (mgg.global_config['media:thumb']['max_width'],)

        if self._skip_processing('thumb', thumb_size=thumb_size):
            return

        # We will only use the width so that the correct scale is kept
        transcoders.VideoThumbnailerMarkII(
            self.process_filename,
            tmp_thumb,
            thumb_size[0])

        # Checking if the thumbnail was correctly created.  If it was not,
        # then just give up.
        if not os.path.exists (tmp_thumb):
            return

        # Push the thumbnail to public storage
        _log.debug('Saving thumbnail...')
        store_public(self.entry, 'thumb', tmp_thumb,
                     self.name_builder.fill('{basename}.thumbnail.jpg'))

        self.entry.set_file_metadata('thumb', thumb_size=thumb_size)

class InitialProcessor(CommonVideoProcessor):
    """
    Initial processing steps for new video
    """
    name = "initial"
    description = "Initial processing"

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
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
            '--medium_size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        parser.add_argument(
            '--vp8_quality',
            type=int,
            help='Range 0..10')

        parser.add_argument(
            '--vp8_threads',
            type=int,
            help='0 means number_of_CPUs - 1')

        parser.add_argument(
            '--vorbis_quality',
            type=float,
            help='Range -0.1..1')

        parser.add_argument(
            '--thumb_size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['medium_size', 'vp8_quality', 'vp8_threads',
                   'vorbis_quality', 'thumb_size'])

    def process(self, medium_size=None, vp8_threads=None, vp8_quality=None,
                vorbis_quality=None, thumb_size=None):
        self.common_setup()

        self.transcode(medium_size=medium_size, vp8_quality=vp8_quality,
                       vp8_threads=vp8_threads, vorbis_quality=vorbis_quality)

        self.copy_original()
        self.generate_thumb(thumb_size=thumb_size)
        self.delete_queue_file()


class Resizer(CommonVideoProcessor):
    """
    Video thumbnail resizing process steps for processed media
    """
    name = 'resize'
    description = 'Resize thumbnail'
    thumb_size = 'thumb_size'

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
            '--thumb_size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        # Needed for gmg reprocess thumbs to work
        parser.add_argument(
            'file',
            nargs='?',
            default='thumb',
            choices=['thumb'])

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['thumb_size', 'file'])

    def process(self, thumb_size=None, file=None):
        self.common_setup()
        self.generate_thumb(thumb_size=thumb_size)


class Transcoder(CommonVideoProcessor):
    """
    Transcoding processing steps for processed video
    """
    name = 'transcode'
    description = 'Re-transcode video'

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
            '--medium_size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        parser.add_argument(
            '--vp8_quality',
            type=int,
            help='Range 0..10')

        parser.add_argument(
            '--vp8_threads',
            type=int,
            help='0 means number_of_CPUs - 1')

        parser.add_argument(
            '--vorbis_quality',
            type=float,
            help='Range -0.1..1')

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['medium_size', 'vp8_threads', 'vp8_quality',
                   'vorbis_quality'])

    def process(self, medium_size=None, vp8_quality=None, vp8_threads=None,
                vorbis_quality=None):
        self.common_setup()
        self.transcode(medium_size=medium_size, vp8_threads=vp8_threads,
                       vp8_quality=vp8_quality, vorbis_quality=vorbis_quality)


class VideoProcessingManager(ProcessingManager):
    def __init__(self):
        super(VideoProcessingManager, self).__init__()
        self.add_processor(InitialProcessor)
        self.add_processor(Resizer)
        self.add_processor(Transcoder)
