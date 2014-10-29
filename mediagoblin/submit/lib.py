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
from os.path import splitext

import six

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from mediagoblin import mg_globals
from mediagoblin.tools.response import json_response
from mediagoblin.tools.text import convert_to_tag_list_of_dicts
from mediagoblin.tools.federation import create_activity
from mediagoblin.db.models import MediaEntry, ProcessingMetaData
from mediagoblin.processing import mark_entry_failed
from mediagoblin.processing.task import ProcessMedia
from mediagoblin.notifications import add_comment_subscription
from mediagoblin.media_types import sniff_media


_log = logging.getLogger(__name__)


def check_file_field(request, field_name):
    """Check if a file field meets minimal criteria"""
    retval = (field_name in request.files
              and isinstance(request.files[field_name], FileStorage)
              and request.files[field_name].stream)
    if not retval:
        _log.debug("Form did not contain proper file field %s", field_name)
    return retval


def new_upload_entry(user):
    """
    Create a new MediaEntry for uploading
    """
    entry = MediaEntry()
    entry.uploader = user.id
    entry.license = user.license_preference
    return entry


def get_upload_file_limits(user):
    """
    Get the upload_limit and max_file_size for this user
    """
    if user.upload_limit is not None and user.upload_limit >= 0:  # TODO: debug this
        upload_limit = user.upload_limit
    else:
        upload_limit = mg_globals.app_config.get('upload_limit', None)

    max_file_size = mg_globals.app_config.get('max_file_size', None)

    return upload_limit, max_file_size


class UploadLimitError(Exception):
    """
    General exception for when an upload will be over some upload limit
    """
    pass


class FileUploadLimit(UploadLimitError):
    """
    This file is over the site upload limit
    """
    pass


class UserUploadLimit(UploadLimitError):
    """
    This file is over the user's particular upload limit
    """
    pass


class UserPastUploadLimit(UploadLimitError):
    """
    The user is *already* past their upload limit!
    """
    pass



def submit_media(mg_app, user, submitted_file, filename,
                 title=None, description=None,
                 license=None, metadata=None, tags_string=u"",
                 upload_limit=None, max_file_size=None,
                 callback_url=None,
                 # If provided we'll do the feed_url update, otherwise ignore
                 urlgen=None,):
    """
    Args:
     - mg_app: The MediaGoblinApp instantiated for this process
     - user: the user object this media entry should be associated with
     - submitted_file: the file-like object that has the
       being-submitted file data in it (this object should really have
       a .name attribute which is the filename on disk!)
     - filename: the *original* filename of this.  Not necessarily the
       one on disk being referenced by submitted_file.
     - title: title for this media entry
     - description: description for this media entry
     - license: license for this media entry
     - tags_string: comma separated string of tags to be associated
       with this entry
     - upload_limit: size in megabytes that's the per-user upload limit
     - max_file_size: maximum size each file can be that's uploaded
     - callback_url: possible post-hook to call after submission
     - urlgen: if provided, used to do the feed_url update
    """
    if upload_limit and user.uploaded >= upload_limit:
        raise UserPastUploadLimit()

    # If the filename contains non ascii generate a unique name
    if not all(ord(c) < 128 for c in filename):
        filename = six.text_type(uuid.uuid4()) + splitext(filename)[-1]

    # Sniff the submitted media to determine which
    # media plugin should handle processing
    media_type, media_manager = sniff_media(submitted_file, filename)

    # create entry and save in database
    entry = new_upload_entry(user)
    entry.media_type = media_type
    entry.title = (title or six.text_type(splitext(filename)[0]))

    entry.description = description or u""

    entry.license = license or None

    entry.media_metadata = metadata or {}

    # Process the user's folksonomy "tags"
    entry.tags = convert_to_tag_list_of_dicts(tags_string)

    # Generate a slug from the title
    entry.generate_slug()

    queue_file = prepare_queue_task(mg_app, entry, filename)

    with queue_file:
        queue_file.write(submitted_file.read())

    # Get file size and round to 2 decimal places
    file_size = mg_app.queue_store.get_file_size(
        entry.queued_media_file) / (1024.0 * 1024)
    file_size = float('{0:.2f}'.format(file_size))

    # Check if file size is over the limit
    if max_file_size and file_size >= max_file_size:
        raise FileUploadLimit()

    # Check if user is over upload limit
    if upload_limit and (user.uploaded + file_size) >= upload_limit:
        raise UserUploadLimit()

    user.uploaded = user.uploaded + file_size
    user.save()

    entry.file_size = file_size

    # Save now so we have this data before kicking off processing
    entry.save()

    # Various "submit to stuff" things, callbackurl and this silly urlgen
    # thing
    if callback_url:
        metadata = ProcessingMetaData()
        metadata.media_entry = entry
        metadata.callback_url = callback_url
        metadata.save()

    if urlgen:
        feed_url = urlgen(
            'mediagoblin.user_pages.atom_feed',
            qualified=True, user=user.username)
    else:
        feed_url = None

    add_comment_subscription(user, entry)

    # Create activity
    create_activity("post", entry, entry.uploader)
    entry.save()

    # Pass off to processing
    #
    # (... don't change entry after this point to avoid race
    # conditions with changes to the document via processing code)
    run_process_media(entry, feed_url)

    return entry


def prepare_queue_task(app, entry, filename):
    """
    Prepare a MediaEntry for the processing queue and get a queue file
    """
    # We generate this ourselves so we know what the task id is for
    # retrieval later.

    # (If we got it off the task's auto-generation, there'd be
    # a risk of a race condition when we'd save after sending
    # off the task)
    task_id = six.text_type(uuid.uuid4())
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


def run_process_media(entry, feed_url=None,
                      reprocess_action="initial", reprocess_info=None):
    """Process the media asynchronously

    :param entry: MediaEntry() instance to be processed.
    :param feed_url: A string indicating the feed_url that the PuSH servers
        should be notified of. This will be sth like: `request.urlgen(
            'mediagoblin.user_pages.atom_feed',qualified=True,
            user=request.user.username)`
    :param reprocess_action: What particular action should be run.
    :param reprocess_info: A dict containing all of the necessary reprocessing
        info for the given media_type"""
    try:
        ProcessMedia().apply_async(
            [entry.id, feed_url, reprocess_action, reprocess_info], {},
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


def api_upload_request(request, file_data, entry):
    """ This handles a image upload request """
    # Use the same kind of method from mediagoblin/submit/views:submit_start
    entry.title = file_data.filename

    # This will be set later but currently we just don't have enough information
    entry.slug = None

    queue_file = prepare_queue_task(request.app, entry, file_data.filename)
    with queue_file:
        queue_file.write(request.data)

    entry.save()
    return json_response(entry.serialize(request))

def api_add_to_feed(request, entry):
    """ Add media to Feed """
    feed_url = request.urlgen(
        'mediagoblin.user_pages.atom_feed',
        qualified=True, user=request.user.username
    )

    add_comment_subscription(request.user, entry)

    # Create activity
    create_activity("post", entry, entry.uploader)
    entry.save()
    run_process_media(entry, feed_url)

    return json_response(entry.serialize(request))
