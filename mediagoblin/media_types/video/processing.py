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
import pkg_resources
import os
import logging

from celery.task import Task
from celery import registry

from mediagoblin.db.util import ObjectId
from mediagoblin import mg_globals as mgg
from mediagoblin.util import lazy_pass_to_ugettext as _
from mediagoblin.process_media.errors import BaseProcessingFail, BadMediaFail
from mediagoblin.process_media import mark_entry_failed
from . import transcoders

THUMB_SIZE = 180, 180
MEDIUM_SIZE = 640, 640

loop = None  # Is this even used?

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)


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
    workbench = mgg.workbench_manager.create_workbench()

    queued_filepath = entry['queued_media_file']
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    medium_filepath = create_pub_filepath(
        entry, '640p.webm')

    thumbnail_filepath = create_pub_filepath(
        entry, 'thumbnail.jpg')


    # Create a temporary file for the video destination
    tmp_dst = tempfile.NamedTemporaryFile()

    with tmp_dst:
        # Transcode queued file to a VP8/vorbis file that fits in a 640x640 square
        transcoder = transcoders.VideoTranscoder(queued_filename, tmp_dst.name)

        # Push transcoded video to public storage
        mgg.public_store.get_file(medium_filepath, 'wb').write(
            tmp_dst.read())

        entry['media_files']['webm_640'] = medium_filepath

        # Save the width and height of the transcoded video
        entry['media_data']['video'] = {
            u'width': transcoder.dst_data.videowidth,
            u'height': transcoder.dst_data.videoheight}

    # Create a temporary file for the video thumbnail
    tmp_thumb = tempfile.NamedTemporaryFile()

    with tmp_thumb:
        # Create a thumbnail.jpg that fits in a 180x180 square
        transcoders.VideoThumbnailer(queued_filename, tmp_thumb.name)

        # Push the thumbnail to public storage
        mgg.public_store.get_file(thumbnail_filepath, 'wb').write(
            tmp_thumb.read())

        entry['media_files']['thumb'] = thumbnail_filepath


    # Push original file to public storage
    queued_file = file(queued_filename, 'rb')

    with queued_file:
        original_filepath = create_pub_filepath(
            entry,
            queued_filepath[-1])

        with mgg.public_store.get_file(original_filepath, 'wb') as \
                original_file:
            original_file.write(queued_file.read())

            entry['media_files']['original'] = original_filepath

    mgg.queue_store.delete_file(queued_filepath)


    # Save the MediaEntry
    entry.save()
    

def __create_thumbnail(info):
    thumbnail = tempfile.NamedTemporaryFile()

    logger.info('thumbnailing...')
    transcoders.VideoThumbnailer(info['tmp_file'].name, thumbnail.name)
    logger.debug('Done thumbnailing')

    os.remove(info['tmp_file'].name)

    mgg.public_store.get_file(info['thumb_filepath'], 'wb').write(
        thumbnail.read())


    info['entry']['media_files']['thumb'] = info['thumb_filepath']
    info['entry'].save()


def __close_processing(queue, qentry, info, **kwargs):
    '''
    Updates MediaEntry, moves files, handles errors
    '''
    if not kwargs.get('error'):
        logger.info('Transcoding successful')

        qentry.transcoder.stop()
        gobject.idle_add(info['loop'].quit)
        info['loop'].quit()  # Do I have to do this again?

        logger.info('Saving files...')

        # Write the transcoded media to the storage system
        with info['tmp_file'] as tmp_file:
            mgg.public_store.get_file(info['medium_filepath'], 'wb').write(
                tmp_file.read())
            info['entry']['media_files']['medium'] = info['medium_filepath']

        # we have to re-read because unlike PIL, not everything reads
        # things in string representation :)
        queued_file = file(info['queued_filename'], 'rb')

        with queued_file:
            original_filepath = create_pub_filepath(
                info['entry'],
                info['queued_filepath'][-1])

            with mgg.public_store.get_file(original_filepath, 'wb') as \
                    original_file:
                original_file.write(queued_file.read())

        mgg.queue_store.delete_file(info['queued_filepath'])


        logger.debug('...Done')

        info['entry']['queued_media_file'] = []
        media_files_dict = info['entry'].setdefault('media_files', {})
        media_files_dict['original'] = original_filepath

        info['entry']['state'] = u'processed'
        info['entry']['media_data'][u'preset'] = info['preset'].name
        __create_thumbnail(info)
        info['entry'].save()

    else:
        qentry.transcoder.stop()
        gobject.idle_add(info['loop'].quit)
        info['loop'].quit()
        info['entry']['state'] = u'failed'
        info['entry'].save()

    # clean up workbench
    info['workbench'].destroy_self()


def _transcoding_start(queue, qentry, info):
    logger.info('-> Starting transcoding')
    logger.debug((queue, qentry, info))


def _transcoding_complete(*args):
    __close_processing(*args)
    logger.debug(*args)


def _transcoding_error(queue, qentry, arg, info):
    logger.info('Error')
    __close_processing(queue, qentry, info, error=True)


def _transcoding_pass_setup(queue, qentry, options):
    logger.info('Pass setup')
    logger.debug((queue, qentry, options))


def check_interrupted():
    """
        Check whether we have been interrupted by Ctrl-C and stop the
        transcoder.
    """
    if interrupted:
        try:
            source = transcoder.pipe.get_by_name("source")
            source.send_event(gst.event_new_eos())
        except:
            # Something pretty bad happened... just exit!
            gobject.idle_add(loop.quit)

        return False
    return True


def create_pub_filepath(entry, filename):
    return mgg.public_store.get_unique_filepath(
            ['media_entries',
             unicode(entry['_id']),
             filename])


################################
# Media processing initial steps
################################

class ProcessMedia(Task):
    """
    Pass this entry off for processing.
    """
    def run(self, media_id):
        """
        Pass the media entry off to the appropriate processing function
        (for now just process_image...)
        """
        entry = mgg.database.MediaEntry.one(
            {'_id': ObjectId(media_id)})

        # Try to process, and handle expected errors.
        try:
            process_video(entry)
        except BaseProcessingFail, exc:
            mark_entry_failed(entry[u'_id'], exc)
            return

        entry['state'] = u'processed'
        entry.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        If the processing failed we should mark that in the database.

        Assuming that the exception raised is a subclass of BaseProcessingFail,
        we can use that to get more information about the failure and store that
        for conveying information to users about the failure, etc.
        """
        entry_id = args[0]
        mark_entry_failed(entry_id, exc)


process_media = registry.tasks[ProcessMedia.name]


def mark_entry_failed(entry_id, exc):
    """
    Mark a media entry as having failed in its conversion.

    Uses the exception that was raised to mark more information.  If the
    exception is a derivative of BaseProcessingFail then we can store extra
    information that can be useful for users telling them why their media failed
    to process.

    Args:
     - entry_id: The id of the media entry

    """
    # Was this a BaseProcessingFail?  In other words, was this a
    # type of error that we know how to handle?
    if isinstance(exc, BaseProcessingFail):
        # Looks like yes, so record information about that failure and any
        # metadata the user might have supplied.
        mgg.database['media_entries'].update(
            {'_id': entry_id},
            {'$set': {u'state': u'failed',
                      u'fail_error': exc.exception_path,
                      u'fail_metadata': exc.metadata}})
    else:
        # Looks like no, so just mark it as failed and don't record a
        # failure_error (we'll assume it wasn't handled) and don't record
        # metadata (in fact overwrite it if somehow it had previous info
        # here)
        mgg.database['media_entries'].update(
            {'_id': entry_id},
            {'$set': {u'state': u'failed',
                      u'fail_error': None,
                      u'fail_metadata': {}}})
