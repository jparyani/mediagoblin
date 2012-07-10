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

from mediagoblin.tools.response import render_to_response, render_404
from mediagoblin.db.util import DESCENDING
from mediagoblin.decorators import require_active_login


@require_active_login
def admin_processing_panel(request):
    '''
    Show the global processing panel for this instance
    '''
    if not request.user.is_admin:
        return render_404(request)

    processing_entries = request.db.MediaEntry.find(
        {'state': u'processing'}).sort('created', DESCENDING)

    # Get media entries which have failed to process
    failed_entries = request.db.MediaEntry.find(
        {'state': u'failed'}).sort('created', DESCENDING)

    processed_entries = request.db.MediaEntry.find(
            {'state': u'processed'}).sort('created', DESCENDING).limit(10)

    # Render to response
    return render_to_response(
        request,
        'mediagoblin/admin/panel.html',
        {'processing_entries': processing_entries,
         'failed_entries': failed_entries,
         'processed_entries': processed_entries})
