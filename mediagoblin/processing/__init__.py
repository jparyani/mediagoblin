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

from mediagoblin.db.util import atomic_update
from mediagoblin import mg_globals as mgg

from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

_log = logging.getLogger(__name__)


class ProgressCallback(object):
    def __init__(self, entry):
        self.entry = entry

    def __call__(self, progress):
        if progress:
            self.entry.transcoding_progress = progress
            self.entry.save()


def create_pub_filepath(entry, filename):
    return mgg.public_store.get_unique_filepath(
            ['media_entries',
             unicode(entry.id),
             filename])


class FilenameBuilder(object):
    """Easily slice and dice filenames.

    Initialize this class with an original file path, then use the fill()
    method to create new filenames based on the original.

    """
    MAX_FILENAME_LENGTH = 255  # VFAT's maximum filename length

    def __init__(self, path):
        """Initialize a builder from an original file path."""
        self.dirpath, self.basename = os.path.split(path)
        self.basename, self.ext = os.path.splitext(self.basename)
        self.ext = self.ext.lower()

    def fill(self, fmtstr):
        """Build a new filename based on the original.

        The fmtstr argument can include the following:
        {basename} -- the original basename, with the extension removed
        {ext} -- the original extension, always lowercase

        If necessary, {basename} will be truncated so the filename does not
        exceed this class' MAX_FILENAME_LENGTH in length.

        """
        basename_len = (self.MAX_FILENAME_LENGTH -
                        len(fmtstr.format(basename='', ext=self.ext)))
        return fmtstr.format(basename=self.basename[:basename_len],
                             ext=self.ext)


class ProcessingState(object):
    def __init__(self, entry):
        self.entry = entry
        self.workbench = None
        self.queued_filename = None

    def set_workbench(self, wb):
        self.workbench = wb

    def get_queued_filename(self):
        """
        Get the a filename for the original, on local storage
        """
        if self.queued_filename is not None:
            return self.queued_filename
        queued_filepath = self.entry.queued_media_file
        queued_filename = self.workbench.localized_file(
            mgg.queue_store, queued_filepath,
            'source')
        self.queued_filename = queued_filename
        return queued_filename

    def copy_original(self, target_name, keyname=u"original"):
        self.store_public(keyname, self.get_queued_filename(), target_name)

    def store_public(self, keyname, local_file, target_name=None):
        if target_name is None:
            target_name = os.path.basename(local_file)
        target_filepath = create_pub_filepath(self.entry, target_name)
        if keyname in self.entry.media_files:
            _log.warn("store_public: keyname %r already used for file %r, "
                      "replacing with %r", keyname,
                      self.entry.media_files[keyname], target_filepath)
        mgg.public_store.copy_local_to_storage(local_file, target_filepath)
        self.entry.media_files[keyname] = target_filepath

    def delete_queue_file(self):
        queued_filepath = self.entry.queued_media_file
        mgg.queue_store.delete_file(queued_filepath)
        self.entry.queued_media_file = []


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
            {'id': entry_id},
            {u'state': u'failed',
             u'fail_error': unicode(exc.exception_path),
             u'fail_metadata': exc.metadata})
    else:
        _log.warn("No idea what happened here, but it failed: %r", exc)
        # Looks like no, so just mark it as failed and don't record a
        # failure_error (we'll assume it wasn't handled) and don't record
        # metadata (in fact overwrite it if somehow it had previous info
        # here)
        atomic_update(mgg.database.MediaEntry,
            {'id': entry_id},
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
