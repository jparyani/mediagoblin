# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

import Image

from contextlib import contextmanager
from celery.task import Task
from celery import registry

from mediagoblin.db.util import ObjectId
from mediagoblin import mg_globals as mgg
from mediagoblin.process_media.errors import BaseProcessingFail, BadMediaFail


THUMB_SIZE = 180, 180
MEDIUM_SIZE = 640, 640


def create_pub_filepath(entry, filename):
    return mgg.public_store.get_unique_filepath(
            ['media_entries',
             unicode(entry['_id']),
             filename])


@contextmanager
def closing(callback):
    try:
        yield callback
    finally:
        pass


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
            process_image(entry)
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


def process_image(entry):
    """
    Code to process an image
    """
    workbench = mgg.workbench_manager.create_workbench()

    queued_filepath = entry['queued_media_file']
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    try:
        thumb = Image.open(queued_filename)
    except IOError:
        raise BadMediaFail()

    thumb.thumbnail(THUMB_SIZE, Image.ANTIALIAS)
    # ensure color mode is compatible with jpg
    if thumb.mode != "RGB":
        thumb = thumb.convert("RGB")

    thumb_filepath = create_pub_filepath(entry, 'thumbnail.jpg')
    thumb_file = mgg.public_store.get_file(thumb_filepath, 'w')

    with closing(thumb_file):
        thumb.save(thumb_file, "JPEG", quality=90)

    # If the size of the original file exceeds the specified size of a `medium`
    # file, a `medium.jpg` files is created and later associated with the media
    # entry.
    medium = Image.open(queued_filename)
    medium_processed = False

    if medium.size[0] > MEDIUM_SIZE[0] or medium.size[1] > MEDIUM_SIZE[1]:
        medium.thumbnail(MEDIUM_SIZE, Image.ANTIALIAS)

        if medium.mode != "RGB":
            medium = medium.convert("RGB")

        medium_filepath = create_pub_filepath(entry, 'medium.jpg')
        medium_file = mgg.public_store.get_file(medium_filepath, 'w')

        with closing(medium_file):
            medium.save(medium_file, "JPEG", quality=90)
            medium_processed = True

    # we have to re-read because unlike PIL, not everything reads
    # things in string representation :)
    queued_file = file(queued_filename, 'rb')

    with queued_file:
        original_filepath = create_pub_filepath(entry, queued_filepath[-1])
        
        with closing(mgg.public_store.get_file(original_filepath, 'wb')) as original_file:
            original_file.write(queued_file.read())

    mgg.queue_store.delete_file(queued_filepath)
    entry['queued_media_file'] = []
    media_files_dict = entry.setdefault('media_files', {})
    media_files_dict['thumb'] = thumb_filepath
    media_files_dict['original'] = original_filepath
    if medium_processed:
        media_files_dict['medium'] = medium_filepath

    # clean up workbench
    workbench.destroy_self()
