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

from os.path import splitext
from cgi import FieldStorage

from webob import Response, exc
from werkzeug.utils import secure_filename

from mediagoblin.decorators import require_active_login
from mediagoblin.submit import forms as submit_forms
from mediagoblin.process_media import process_media_initial


@require_active_login
def submit_start(request):
    """
    First view for submitting a file.
    """
    submit_form = submit_forms.SubmitStartForm(request.POST)

    if request.method == 'POST' and submit_form.validate():
        if not (request.POST.has_key('file')
                and isinstance(request.POST['file'], FieldStorage)
                and request.POST['file'].file):
            submit_form.file.errors.append(
                u'You must provide a file.')
        else:
            filename = request.POST['file'].filename

            # create entry and save in database
            entry = request.db.MediaEntry()
            entry['title'] = request.POST['title'] or unicode(splitext(filename)[0])
            entry['description'] = request.POST.get('description')
            entry['media_type'] = u'image' # heh
            entry['uploader'] = request.user['_id']

            # Save, just so we can get the entry id for the sake of using
            # it to generate the file path
            entry.save(validate=False)

            # Generate a slug from the title
            entry.generate_slug()

            # Now store generate the queueing related filename
            queue_filepath = request.app.queue_store.get_unique_filepath(
                ['media_entries',
                 unicode(entry['_id']),
                 secure_filename(filename)])

            # queue appropriately
            queue_file = request.app.queue_store.get_file(
                queue_filepath, 'wb')

            with queue_file:
                queue_file.write(request.POST['file'].file.read())

            # Add queued filename to the entry
            entry['queued_media_file'] = queue_filepath
            entry.save(validate=True)

            # queue it for processing
            process_media_initial.delay(unicode(entry['_id']))

            # redirect
            return exc.HTTPFound(
                location=request.urlgen("mediagoblin.submit.success"))

    # render
    template = request.template_env.get_template(
        'mediagoblin/submit/start.html')
    return Response(
        template.render(
            {'request': request,
             'submit_form': submit_form}))


def submit_success(request):
    # render
    template = request.template_env.get_template(
        'mediagoblin/submit/success.html')
    return Response(
        template.render(
            {'request': request}))
