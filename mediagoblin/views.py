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

import datetime

from webob import Response, exc
import wtforms
from mongokit import ObjectId
from mediagoblin import models

def root_view(request):
    media_entries = request.db.MediaEntry.find(
        {u'state': u'processed'})
    
    template = request.template_env.get_template(
        'mediagoblin/root.html')
    return Response(
        template.render(
            {'request': request,
             'media_entries': media_entries}))


class ImageSubmitForm(wtforms.Form):
    title = wtforms.TextField(
        'Title',
        [wtforms.validators.Length(min=1, max=500)])
    description = wtforms.TextAreaField('Description of this work')
    file = wtforms.FileField('File')


def submit_test(request):
    image_form = ImageSubmitForm(request.POST)
    if request.method == 'POST' and image_form.validate():
        # create entry and save in database

        entry = request.db.MediaEntry()
        entry['title'] = request.POST['title']
        entry['description'] = request.POST.get(['description'])
        entry['media_type'] = u'image'

        # TODO this does NOT look save, we should clean the filename somenow?
        entry['file_store'] = request.POST['file'].filename

        entry.save(validate=True)

        # save file to disk
        ## TODO
        #open('/tmp/read_file.png', 'wb').write(request.POST['file'].file.read())


        # resize if necessary
        ## Hm.  This should be done on a separate view?

        # redirect
        pass



    # render
    template = request.template_env.get_template(
        'mediagoblin/test_submit.html')
    return Response(
        template.render(
            {'request': request,
             'image_form': image_form}))
