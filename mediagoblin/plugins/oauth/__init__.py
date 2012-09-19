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

import os
import logging

from routes.route import Route
from webob import exc

from mediagoblin.tools import pluginapi
from mediagoblin.tools.response import render_to_response
from mediagoblin.plugins.oauth.models import OAuthToken
from mediagoblin.plugins.api.tools import Auth

_log = logging.getLogger(__name__)

PLUGIN_DIR = os.path.dirname(__file__)


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.plugins.oauth')

    _log.info('Setting up OAuth...')
    _log.debug('OAuth config: {0}'.format(config))

    routes = [
        Route('mediagoblin.plugins.oauth.authorize', '/oauth/authorize',
            controller='mediagoblin.plugins.oauth.views:authorize'),
        Route('mediagoblin.plugins.oauth.access_token', '/oauth/access_token',
            controller='mediagoblin.plugins.oauth.views:access_token')]

    pluginapi.register_routes(routes)
    pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))


class OAuthAuth(Auth):
    def trigger(self, request):
        if 'access_token' in request.GET:
            return True

        return False

    def __call__(self, request, *args, **kw):
        access_token = request.GET.get('access_token')
        if access_token:
            token = OAuthToken.query.filter(OAuthToken.token == access_token)\
                    .first()

            if not token:
                return False

            request.user = token.user
            return True

        return False

hooks = {
    'setup': setup_plugin,
    'auth': OAuthAuth()
    }
