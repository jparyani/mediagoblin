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


from webob import Response, exc

from mediagoblin.edit import forms
from mediagoblin.edit.lib import may_edit_media
from mediagoblin.decorators import require_active_login, get_user_media_entry


@get_user_media_entry
@require_active_login
def edit_media(request, media):
    if not may_edit_media(request, media):
        return exc.HTTPForbidden()

    form = forms.EditForm(request.POST,
        title = media['title'],
        slug = media['slug'],
        description = media['description'])

    if request.method == 'POST' and form.validate():
        media['title'] = request.POST['title']
        media['description'] = request.POST['description']
        media['slug'] = request.POST['slug']
        try:
            media.save()
        except Exception as e:
            return exc.HTTPConflict(detail = str(e))

        # redirect
        return exc.HTTPFound(
            location=request.urlgen("mediagoblin.user_pages.media_home",
                user=media.uploader()['username'], media=media['_id']))

    # render
    template = request.template_env.get_template(
        'mediagoblin/edit/edit.html')
    return Response(
        template.render(
            {'request': request,
             'media': media,
             'form': form}))
