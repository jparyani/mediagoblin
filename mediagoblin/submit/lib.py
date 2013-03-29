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
import uuid
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from mediagoblin.processing import mark_entry_failed
from mediagoblin.processing.task import process_media


_log = logging.getLogger(__name__)


def check_file_field(request, field_name):
    """Check if a file field meets minimal criteria"""
    retval = (field_name in request.files
              and isinstance(request.files[field_name], FileStorage)
              and request.files[field_name].stream)
    if not retval:
        _log.debug("Form did not contain proper file field %s", field_name)
    return retval


def prepare_queue_task(app, entry, filename):
    """
    Prepare a MediaEntry for the processing queue and get a queue file
    """
    # We generate this ourselves so we know what the taks id is for
    # retrieval later.

    # (If we got it off the task's auto-generation, there'd be
    # a risk of a race condition when we'd save after sending
    # off the task)
    task_id = unicode(uuid.uuid4())
    entry.queued_task_id = task_id

    # Now store generate the queueing related filename
    queue_filepath = app.queue_store.get_unique_filepath(
        ['media_entries',
         task_id,
         secure_filename(filename)])

    # queue appropriately
    queue_file = app.queue_store.get_file(
        queue_filepath, 'wb')

    # Add queued filename to the entry
    entry.queued_media_file = queue_filepath

    return queue_file


def run_process_media(entry, feed_url=None):
    """Process the media asynchronously

    :param entry: MediaEntry() instance to be processed.
    :param feed_url: A string indicating the feed_url that the PuSH servers
        should be notified of. This will be sth like: `request.urlgen(
            'mediagoblin.user_pages.atom_feed',qualified=True,
            user=request.user.username)`"""
    try:
        process_media.apply_async(
            [entry.id, feed_url], {},
            task_id=entry.queued_task_id)
    except BaseException as exc:
        # The purpose of this section is because when running in "lazy"
        # or always-eager-with-exceptions-propagated celery mode that
        # the failure handling won't happen on Celery end.  Since we
        # expect a lot of users to run things in this way we have to
        # capture stuff here.
        #
        # ... not completely the diaper pattern because the
        # exception is re-raised :)
        mark_entry_failed(entry.id, exc)
        # re-raise the exception
        raise
