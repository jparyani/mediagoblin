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

from mediagoblin.tools import pluginapi
from mediagoblin.plugins.oauth.models import OAuthToken, OAuthClient, \
        OAuthUserClient
from mediagoblin.plugins.api.tools import Auth

_log = logging.getLogger(__name__)

PLUGIN_DIR = os.path.dirname(__file__)


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.plugins.oauth')

    _log.info('Setting up OAuth...')
    _log.debug('OAuth config: {0}'.format(config))

    routes = [
       ('mediagoblin.plugins.oauth.authorize',
            '/oauth/authorize',
            'mediagoblin.plugins.oauth.views:authorize'),
        ('mediagoblin.plugins.oauth.authorize_client',
            '/oauth/client/authorize',
            'mediagoblin.plugins.oauth.views:authorize_client'),
        ('mediagoblin.plugins.oauth.access_token',
            '/oauth/access_token',
            'mediagoblin.plugins.oauth.views:access_token'),
        ('mediagoblin.plugins.oauth.list_connections',
            '/oauth/client/connections',
            'mediagoblin.plugins.oauth.views:list_connections'),
        ('mediagoblin.plugins.oauth.register_client',
            '/oauth/client/register',
            'mediagoblin.plugins.oauth.views:register_client'),
        ('mediagoblin.plugins.oauth.list_clients',
            '/oauth/client/list',
            'mediagoblin.plugins.oauth.views:list_clients')]

    pluginapi.register_routes(routes)
    pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))


class OAuthAuth(Auth):
    def trigger(self, request):
        if 'access_token' in request.GET:
            return True

        return False

    def __call__(self, request, *args, **kw):
        self.errors = []
        # TODO: Add suport for client credentials authorization
        client_id = request.GET.get('client_id')  # TODO: Not used
        client_secret = request.GET.get('client_secret')  # TODO: Not used
        access_token = request.GET.get('access_token')

        _log.debug('Authorizing request {0}'.format(request.url))

        if access_token:
            token = OAuthToken.query.filter(OAuthToken.token == access_token)\
                    .first()

            if not token:
                self.errors.append('Invalid access token')
                return False

            _log.debug('Access token: {0}'.format(token))
            _log.debug('Client: {0}'.format(token.client))

            relation = OAuthUserClient.query.filter(
                    (OAuthUserClient.user == token.user)
                    & (OAuthUserClient.client == token.client)
                    & (OAuthUserClient.state == u'approved')).first()

            _log.debug('Relation: {0}'.format(relation))

            if not relation:
                self.errors.append(
                        u'Client has not been approved by the resource owner')
                return False

            request.user = token.user
            return True

        self.errors.append(u'No access_token specified')

        return False

hooks = {
    'setup': setup_plugin,
    'auth': OAuthAuth()
    }
