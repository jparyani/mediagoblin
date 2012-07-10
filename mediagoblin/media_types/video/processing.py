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

import tempfile
import logging

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import \
    create_pub_filepath, FilenameBuilder, BaseProcessingFail, ProgressCallback
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

from . import transcoders

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)


class VideoTranscodingFail(BaseProcessingFail):
    '''
    Error raised if video transcoding fails
    '''
    general_message = _(u'Video transcoding failed')


def sniff_handler(media_file, **kw):
    transcoder = transcoders.VideoTranscoder()
    data = transcoder.discover(media_file.name)

    _log.debug('Discovered: {0}'.format(data))

    if not data:
        _log.error('Could not discover {0}'.format(
                kw.get('media')))
        return False

    if data['is_video'] == True:
        return True

    return False


def process_video(entry):
    """
    Process a video entry, transcode the queued media files (originals) and
    create a thumbnail for the entry.
    """
    video_config = mgg.global_config['media_type:mediagoblin.media_types.video']

    workbench = mgg.workbench_manager.create_workbench()

    queued_filepath = entry.queued_media_file
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')
    name_builder = FilenameBuilder(queued_filename)

    medium_filepath = create_pub_filepath(
        entry, name_builder.fill('{basename}-640p.webm'))

    thumbnail_filepath = create_pub_filepath(
        entry, name_builder.fill('{basename}.thumbnail.jpg'))

    # Create a temporary file for the video destination
    tmp_dst = tempfile.NamedTemporaryFile()

    with tmp_dst:
        # Transcode queued file to a VP8/vorbis file that fits in a 640x640 square
        progress_callback = ProgressCallback(entry)
        transcoder = transcoders.VideoTranscoder()
        transcoder.transcode(queued_filename, tmp_dst.name,
                vp8_quality=video_config['vp8_quality'],
                vp8_threads=video_config['vp8_threads'],
                vorbis_quality=video_config['vorbis_quality'],
                progress_callback=progress_callback)

        # Push transcoded video to public storage
        _log.debug('Saving medium...')
        mgg.public_store.get_file(medium_filepath, 'wb').write(
            tmp_dst.read())
        _log.debug('Saved medium')

        entry.media_files['webm_640'] = medium_filepath

        # Save the width and height of the transcoded video
        entry.media_data_init(
            width=transcoder.dst_data.videowidth,
            height=transcoder.dst_data.videoheight)

    # Create a temporary file for the video thumbnail
    tmp_thumb = tempfile.NamedTemporaryFile(suffix='.jpg')

    with tmp_thumb:
        # Create a thumbnail.jpg that fits in a 180x180 square
        transcoders.VideoThumbnailer(queued_filename, tmp_thumb.name)

        # Push the thumbnail to public storage
        _log.debug('Saving thumbnail...')
        mgg.public_store.get_file(thumbnail_filepath, 'wb').write(
            tmp_thumb.read())
        _log.debug('Saved thumbnail')

        entry.media_files['thumb'] = thumbnail_filepath

    if video_config['keep_original']:
        # Push original file to public storage
        queued_file = file(queued_filename, 'rb')

        with queued_file:
            original_filepath = create_pub_filepath(
                entry,
                queued_filepath[-1])

            with mgg.public_store.get_file(original_filepath, 'wb') as \
                    original_file:
                _log.debug('Saving original...')
                original_file.write(queued_file.read())
                _log.debug('Saved original')

                entry.media_files['original'] = original_filepath

    mgg.queue_store.delete_file(queued_filepath)

    # Save the MediaEntry
    entry.save()
