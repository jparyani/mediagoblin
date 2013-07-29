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

from mediagoblin.tools.response import render_to_response, render_404, redirect
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.decorators import (uses_pagination, get_user_media_entry,
    get_media_entry_by_id,
    require_active_login, user_may_delete_media, user_may_alter_collection,
    get_user_collection, get_user_collection_item, active_user_from_url)

from mediagoblin import messages

from mediagoblin.notifications import add_comment_subscription, \
        silence_comment_subscription

from werkzeug.exceptions import BadRequest

@get_user_media_entry
@require_active_login
def subscribe_comments(request, media):

    add_comment_subscription(request.user, media)

    messages.add_message(request,
                         messages.SUCCESS,
                         _('Subscribed to comments on %s!')
                         % media.title)

    return redirect(request, location=media.url_for_self(request.urlgen))

@get_user_media_entry
@require_active_login
def silence_comments(request, media):
    silence_comment_subscription(request.user, media)

    messages.add_message(request,
                         messages.SUCCESS,
                         _('You will not receive notifications for comments on'
                           ' %s.') % media.title)

    return redirect(request, location=media.url_for_self(request.urlgen))
