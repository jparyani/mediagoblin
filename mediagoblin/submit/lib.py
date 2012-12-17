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

import urllib
import urllib2
import logging
import uuid
from celery import registry
from werkzeug.utils import secure_filename

from mediagoblin import mg_globals
from mediagoblin.processing import mark_entry_failed
from mediagoblin.processing.task import ProcessMedia


_log = logging.getLogger(__name__)


def prepare_entry(request, entry, filename):
    # We generate this ourselves so we know what the taks id is for
    # retrieval later.

    # (If we got it off the task's auto-generation, there'd be
    # a risk of a race condition when we'd save after sending
    # off the task)
    task_id = unicode(uuid.uuid4())
    entry.queued_task_id = task_id

    # Now store generate the queueing related filename
    queue_filepath = request.app.queue_store.get_unique_filepath(
        ['media_entries',
         task_id,
         secure_filename(filename)])

    # queue appropriately
    queue_file = request.app.queue_store.get_file(
        queue_filepath, 'wb')

    # Add queued filename to the entry
    entry.queued_media_file = queue_filepath

    return queue_file


def run_process_media(entry):
    process_media = registry.tasks[ProcessMedia.name]
    try:
        process_media.apply_async(
            [unicode(entry.id)], {},
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


def handle_push_urls(request):
    if mg_globals.app_config["push_urls"]:
        feed_url = request.urlgen(
                           'mediagoblin.user_pages.atom_feed',
                           qualified=True,
                           user=request.user.username)
        hubparameters = {
            'hub.mode': 'publish',
            'hub.url': feed_url}
        hubdata = urllib.urlencode(hubparameters)
        hubheaders = {
            "Content-type": "application/x-www-form-urlencoded",
            "Connection": "close"}
        for huburl in mg_globals.app_config["push_urls"]:
            hubrequest = urllib2.Request(huburl, hubdata, hubheaders)
            try:
                hubresponse = urllib2.urlopen(hubrequest)
            except urllib2.HTTPError as exc:
                # This is not a big issue, the item will be fetched
                # by the PuSH server next time we hit it
                _log.warning(
                    "push url %r gave error %r", huburl, exc.code)
            except urllib2.URLError as exc:
                _log.warning(
                    "push url %r is unreachable %r", huburl, exc.reason)
