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

from functools import wraps

from mediagoblin.plugins.oauth.models import OAuthClient
from mediagoblin.plugins.api.tools import json_response


def require_client_auth(controller):
    @wraps(controller)
    def wrapper(request, *args, **kw):
        if not request.GET.get('client_id'):
            return json_response({
                'status': 400,
                'errors': [u'No client identifier in URL']},
                _disable_cors=True)

        client = OAuthClient.query.filter(
                OAuthClient.identifier == request.GET.get('client_id')).first()

        if not client:
            return json_response({
                'status': 400,
                'errors': [u'No such client identifier']},
                _disable_cors=True)

        return controller(request, client)

    return wrapper
