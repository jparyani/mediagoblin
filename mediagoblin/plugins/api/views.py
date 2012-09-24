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

import json
import logging
import uuid

from os.path import splitext
from webob import exc, Response
from cgi import FieldStorage
from werkzeug.utils import secure_filename
from celery import registry

from mediagoblin.db.util import ObjectId
from mediagoblin.decorators import require_active_login
from mediagoblin.processing import mark_entry_failed
from mediagoblin.processing.task import ProcessMedia
from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.media_types import sniff_media, InvalidFileType, \
        FileTypeNotSupported
from mediagoblin.plugins.api.tools import api_auth, get_entry_serializable, \
        json_response

from mediagoblin.plugins.api import config

_log = logging.getLogger(__name__)


@csrf_exempt
@api_auth
@require_active_login
def post_entry(request):
    _log.debug('Posting entry')

    if request.method == 'OPTIONS':
        return json_response({'status': 200})

    if request.method != 'POST':
        _log.debug('Must POST against post_entry')
        return exc.HTTPBadRequest()

    if not 'file' in request.POST \
            or not isinstance(request.POST['file'], FieldStorage) \
            or not request.POST['file'].file:
        _log.debug('File field not found')
        return exc.HTTPBadRequest()

    media_file = request.POST['file']

    media_type, media_manager = sniff_media(media_file)

    entry = request.db.MediaEntry()
    entry.id = ObjectId()
    entry.media_type = unicode(media_type)
    entry.title = unicode(request.POST.get('title')
            or splitext(media_file.filename)[0])

    entry.description = unicode(request.POST.get('description'))
    entry.license = unicode(request.POST.get('license', ''))

    entry.uploader = request.user.id

    entry.generate_slug()

    task_id = unicode(uuid.uuid4())

    # Now store generate the queueing related filename
    queue_filepath = request.app.queue_store.get_unique_filepath(
        ['media_entries',
            task_id,
            secure_filename(media_file.filename)])

    # queue appropriately
    queue_file = request.app.queue_store.get_file(
        queue_filepath, 'wb')

    with queue_file:
        queue_file.write(request.POST['file'].file.read())

    # Add queued filename to the entry
    entry.queued_media_file = queue_filepath

    entry.queued_task_id = task_id

    # Save now so we have this data before kicking off processing
    entry.save(validate=True)

    if request.POST.get('callback_url'):
        metadata = request.db.ProcessingMetaData()
        metadata.media_entry = entry
        metadata.callback_url = unicode(request.POST['callback_url'])
        metadata.save()

    # Pass off to processing
    #
    # (... don't change entry after this point to avoid race
    # conditions with changes to the document via processing code)
    process_media = registry.tasks[ProcessMedia.name]
    try:
        process_media.apply_async(
            [unicode(entry._id)], {},
            task_id=task_id)
    except BaseException as e:
        # The purpose of this section is because when running in "lazy"
        # or always-eager-with-exceptions-propagated celery mode that
        # the failure handling won't happen on Celery end.  Since we
        # expect a lot of users to run things in this way we have to
        # capture stuff here.
        #
        # ... not completely the diaper pattern because the
        # exception is re-raised :)
        mark_entry_failed(entry._id, e)
        # re-raise the exception
        raise

    return json_response(get_entry_serializable(entry, request.urlgen))


@api_auth
def api_test(request):
    if not request.user:
        return exc.HTTPForbidden()

    user_data = {
            'username': request.user.username,
            'email': request.user.email}

    return Response(json.dumps(user_data))


def get_entries(request):
    entries = request.db.MediaEntry.query

    # TODO: Make it possible to fetch unprocessed media, or media in-processing
    entries = entries.filter_by(state=u'processed')

    # TODO: Add sort order customization
    entries = entries.order_by(request.db.MediaEntry.created.desc())

    # TODO: Fetch default and upper limit from config
    entries = entries.limit(int(request.GET.get('limit') or 10))

    entries_serializable = []

    for entry in entries:
        entries_serializable.append(get_entry_serializable(entry, request.urlgen))

    return json_response(entries_serializable)
