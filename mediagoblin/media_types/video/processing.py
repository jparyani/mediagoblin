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

import tempfile
import logging
import os

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import mark_entry_failed, \
    THUMB_SIZE, MEDIUM_SIZE, create_pub_filepath
from . import transcoders

logging.basicConfig()

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)


def process_video(entry):
    """
    Code to process a video

    Much of this code is derived from the arista-transcoder script in
    the arista PyPI package and changed to match the needs of
    MediaGoblin

    This function sets up the arista video encoder in some kind of new thread
    and attaches callbacks to that child process, hopefully, the
    entry-complete callback will be called when the video is done.
    """
    video_config = mgg.global_config['media_type:mediagoblin.media_types.video']

    workbench = mgg.workbench_manager.create_workbench()

    queued_filepath = entry.queued_media_file
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    medium_filepath = create_pub_filepath(
        entry,
        '{original}-640p.webm'.format(
            original=os.path.splitext(
                queued_filepath[-1])[0]  # Select the 
            ))

    thumbnail_filepath = create_pub_filepath(
        entry, 'thumbnail.jpg')


    # Create a temporary file for the video destination
    tmp_dst = tempfile.NamedTemporaryFile()

    with tmp_dst:
        # Transcode queued file to a VP8/vorbis file that fits in a 640x640 square
        transcoder = transcoders.VideoTranscoder(queued_filename, tmp_dst.name)

        # Push transcoded video to public storage
        _log.debug('Saving medium...')
        mgg.public_store.get_file(medium_filepath, 'wb').write(
            tmp_dst.read())
        _log.debug('Saved medium')

        entry.media_files['webm_640'] = medium_filepath

        # Save the width and height of the transcoded video
        entry.media_data['video'] = {
            u'width': transcoder.dst_data.videowidth,
            u'height': transcoder.dst_data.videoheight}

    # Create a temporary file for the video thumbnail
    tmp_thumb = tempfile.NamedTemporaryFile()

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
