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

from mediagoblin import mg_globals
from mediagoblin.db.models import MediaEntry
from mediagoblin.tools.pagination import Pagination
from mediagoblin.tools.pluginapi import hook_handle
from mediagoblin.tools.response import render_to_response, render_404
from mediagoblin.decorators import uses_pagination, user_not_banned


@user_not_banned
@uses_pagination
def default_root_view(request, page):
    cursor = MediaEntry.query.filter_by(state=u'processed').\
        order_by(MediaEntry.created.desc())

    pagination = Pagination(page, cursor)
    media_entries = pagination()
    return render_to_response(
        request, 'mediagoblin/root.html',
        {'media_entries': media_entries,
         'allow_registration': mg_globals.app_config["allow_registration"],
         'pagination': pagination})



def root_view(request):
    """
    Proxies to the real root view that's displayed
    """
    view = hook_handle("frontpage_view") or default_root_view
    return view(request)



def simple_template_render(request):
    """
    A view for absolutely simple template rendering.
    Just make sure 'template' is in the matchdict!
    """
    template_name = request.matchdict['template']
    return render_to_response(
        request, template_name, {})

def terms_of_service(request):
    if mg_globals.app_config["show_tos"] is False:
        return render_404(request)

    return render_to_response(request,
        'mediagoblin/terms_of_service.html', {})
