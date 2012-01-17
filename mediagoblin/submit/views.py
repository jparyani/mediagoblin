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

import mediagoblin.mg_globals as mg_globals
import uuid
from os.path import splitext
from cgi import FieldStorage

from celery import registry
import urllib,urllib2
import logging

_log = logging.getLogger(__name__)

from werkzeug.utils import secure_filename

from mediagoblin.db.util import ObjectId
from mediagoblin.tools.text import cleaned_markdown_conversion, convert_to_tag_list_of_dicts
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.response import render_to_response, redirect
from mediagoblin.decorators import require_active_login
from mediagoblin.submit import forms as submit_forms, security
from mediagoblin.processing import mark_entry_failed, ProcessMedia
from mediagoblin.messages import add_message, SUCCESS
from mediagoblin.media_types import get_media_type_and_manager, \
    InvalidFileType, FileTypeNotSupported


@require_active_login
def submit_start(request):
    """
    First view for submitting a file.
    """
    submit_form = submit_forms.SubmitStartForm(request.POST)

    if request.method == 'POST' and submit_form.validate():
        if not ('file' in request.POST
                and isinstance(request.POST['file'], FieldStorage)
                and request.POST['file'].file):
            submit_form.file.errors.append(
                _(u'You must provide a file.'))
        else:
            try:
                filename = request.POST['file'].filename
                media_type, media_manager = get_media_type_and_manager(filename)

                # create entry and save in database
                entry = request.db.MediaEntry()
                entry['_id'] = ObjectId()
                entry.media_type = unicode(media_type)
                entry.title = (
                    unicode(request.POST['title'])
                    or unicode(splitext(filename)[0]))

                entry.description = unicode(request.POST.get('description'))
                entry.description_html = cleaned_markdown_conversion(
                    entry.description)

                entry.uploader = request.user._id

                # Process the user's folksonomy "tags"
                entry['tags'] = convert_to_tag_list_of_dicts(
                    request.POST.get('tags'))

                # Generate a slug from the title
                entry.generate_slug()


                # Now store generate the queueing related filename
                queue_filepath = request.app.queue_store.get_unique_filepath(
                    ['media_entries',
                     unicode(entry._id),
                     secure_filename(filename)])

                # queue appropriately
                queue_file = request.app.queue_store.get_file(
                    queue_filepath, 'wb')

                with queue_file:
                    queue_file.write(request.POST['file'].file.read())

                # Add queued filename to the entry
                entry.queued_media_file = queue_filepath

                # We generate this ourselves so we know what the taks id is for
                # retrieval later.

                # (If we got it off the task's auto-generation, there'd be
                # a risk of a race condition when we'd save after sending
                # off the task)
                task_id = unicode(uuid.uuid4())
                entry['queued_task_id'] = task_id

                # Save now so we have this data before kicking off processing
                entry.save(validate=True)

                # Pass off to processing
                #
                # (... don't change entry after this point to avoid race
                # conditions with changes to the document via processing code)
                process_media = registry.tasks[ProcessMedia.name]
                try:
                    process_media.apply_async(
                        [unicode(entry._id)], {},
                        task_id=task_id)
                except BaseException as exc:
                    # The purpose of this section is because when running in "lazy"
                    # or always-eager-with-exceptions-propagated celery mode that
                    # the failure handling won't happen on Celery end.  Since we
                    # expect a lot of users to run things in this way we have to
                    # capture stuff here.
                    #
                    # ... not completely the diaper pattern because the
                    # exception is re-raised :)
                    mark_entry_failed(entry._id, exc)
                    # re-raise the exception
                    raise

                if mg_globals.app_config["push_urls"]:
                    feed_url=request.urlgen(
                                       'mediagoblin.user_pages.atom_feed',
                                       qualified=True,user=request.user.username)
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

                add_message(request, SUCCESS, _('Woohoo! Submitted!'))

                return redirect(request, "mediagoblin.user_pages.user_home",
                                user=request.user.username)
            except Exception as e:
                '''
                This section is intended to catch exceptions raised in 
                mediagobling.media_types
                '''

                if isinstance(e, InvalidFileType) or \
                        isinstance(e, FileTypeNotSupported):
                    submit_form.file.errors.append(
                        e)
                else:
                    raise

    return render_to_response(
        request,
        'mediagoblin/submit/start.html',
        {'submit_form': submit_form,
         'app_config': mg_globals.app_config})
