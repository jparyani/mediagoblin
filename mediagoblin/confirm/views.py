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

import uuid

from webob import exc
from string import split

from mediagoblin import messages
from mediagoblin import mg_globals
from mediagoblin.util import (
    render_to_response, redirect, clean_html, convert_to_tag_list_of_dicts,
    media_tags_as_string, cleaned_markdown_conversion)
from mediagoblin.util import pass_to_ugettext as _
from mediagoblin.confirm import forms
from mediagoblin.confirm.lib import may_delete_media
from mediagoblin.decorators import require_active_login, get_user_media_entry


@get_user_media_entry
@require_active_login
def confirm_delete(request, media):
    if not may_delete_media(request, media):
        return exc.HTTPForbidden()

    form = forms.ConfirmDeleteForm(request.POST)

    if request.method == 'POST' and form.validate():
        if request.POST.get('confirm') == 'True':
            username = media.uploader()['username']
            media.delete()
            return redirect(request, "mediagoblin.user_pages.user_home",
                user=username)
        else:
            return redirect(request, "mediagoblin.user_pages.media_home",
                            user=media.uploader()['username'],
                            media=media['slug'])

    return render_to_response(
        request,
        'mediagoblin/confirm/confirm_delete.html',
        {'media': media,
         'form': form})
