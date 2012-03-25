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
import os

from celery.task import Task

from mediagoblin.db.util import ObjectId, atomic_update
from mediagoblin import mg_globals as mgg

from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

from mediagoblin.media_types import get_media_manager

_log = logging.getLogger(__name__)

THUMB_SIZE = 180, 180
MEDIUM_SIZE = 640, 640


def create_pub_filepath(entry, filename):
    return mgg.public_store.get_unique_filepath(
            ['media_entries',
             unicode(entry._id),
             filename])


################################
# Media processing initial steps
################################

class FilenameMunger(object):
    """Easily slice and dice filenames.

    Initialize this class with an original filename, then use the munge()
    method to create new filenames based on the original.

    """
    MAX_FILENAME_LENGTH = 255  # VFAT's maximum filename length

    def __init__(self, path):
        """Initialize a munger with one original filename."""
        self.dirpath, self.basename = os.path.split(path)
        self.basename, self.ext = os.path.splitext(self.basename)
        self.ext = self.ext.lower()

    def munge(self, fmtstr):
        """Return a new filename based on the initialized original.

        The fmtstr argumentcan include {basename} and {ext}, which will
        fill in components of the original filename.  The extension will
        always be lowercased.  The filename will also be trunacted to this
        class' MAX_FILENAME_LENGTH characters.

        """
        basename_len = (self.MAX_FILENAME_LENGTH -
                        len(fmtstr.format(basename='', ext=self.ext)))
        return fmtstr.format(basename=self.basename[:basename_len],
                             ext=self.ext)


class ProcessMedia(Task):
    """
    DEPRECATED -- This now resides in the individual media plugins

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
            #__import__(entry.media_type)
            manager = get_media_manager(entry.media_type)
            _log.debug('Processing {0}'.format(entry))
            manager['processor'](entry)
        except BaseProcessingFail, exc:
            mark_entry_failed(entry._id, exc)
            return
        except ImportError, exc:
            _log.error(
                'Entry {0} failed to process due to an import error: {1}'\
                    .format(
                    entry.title,
                    exc))

            mark_entry_failed(entry._id, exc)

        entry.state = u'processed'
        entry.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        If the processing failed we should mark that in the database.

        Assuming that the exception raised is a subclass of
        BaseProcessingFail, we can use that to get more information
        about the failure and store that for conveying information to
        users about the failure, etc.
        """
        entry_id = args[0]
        mark_entry_failed(entry_id, exc)


def mark_entry_failed(entry_id, exc):
    """
    Mark a media entry as having failed in its conversion.

    Uses the exception that was raised to mark more information.  If
    the exception is a derivative of BaseProcessingFail then we can
    store extra information that can be useful for users telling them
    why their media failed to process.

    Args:
     - entry_id: The id of the media entry

    """
    # Was this a BaseProcessingFail?  In other words, was this a
    # type of error that we know how to handle?
    if isinstance(exc, BaseProcessingFail):
        # Looks like yes, so record information about that failure and any
        # metadata the user might have supplied.
        atomic_update(mgg.database.MediaEntry,
            {'_id': entry_id},
            {u'state': u'failed',
             u'fail_error': exc.exception_path,
             u'fail_metadata': exc.metadata})
    else:
        _log.warn("No idea what happened here, but it failed: %r", exc)
        # Looks like no, so just mark it as failed and don't record a
        # failure_error (we'll assume it wasn't handled) and don't record
        # metadata (in fact overwrite it if somehow it had previous info
        # here)
        atomic_update(mgg.database.MediaEntry,
            {'_id': entry_id},
            {u'state': u'failed',
             u'fail_error': None,
             u'fail_metadata': {}})


class BaseProcessingFail(Exception):
    """
    Base exception that all other processing failure messages should
    subclass from.

    You shouldn't call this itself; instead you should subclass it
    and provid the exception_path and general_message applicable to
    this error.
    """
    general_message = u''

    @property
    def exception_path(self):
        return u"%s:%s" % (
            self.__class__.__module__, self.__class__.__name__)

    def __init__(self, **metadata):
        self.metadata = metadata or {}


class BadMediaFail(BaseProcessingFail):
    """
    Error that should be raised when an inappropriate file was given
    for the media type specified.
    """
    general_message = _(u'Invalid file given for media type.')
