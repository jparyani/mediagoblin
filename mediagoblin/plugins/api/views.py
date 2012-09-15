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
from webob import exc, Response

from mediagoblin.plugins.api.tools import api_auth, get_entry_serializable, \
        json_response


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

    entries = entries.filter_by(state=u'processed')

    entries_serializable = []

    for entry in entries:
        entries_serializable.append(get_entry_serializable(entry))

    return json_response(entries_serializable)
