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

import logging

from mediagoblin import mg_globals
from mediagoblin.init.plugins import setup_plugins
from mediagoblin.tools import template, pluginapi
from mediagoblin.tests.tools import get_test_app, fixture_add_user
from mediagoblin.tests.test_pluginapi import with_cleanup, build_config


_log = logging.getLogger(__name__)


class TestOAuth(object):
    def setUp(self):
        self.app = get_test_app()
        self.db = mg_globals.database

        self.pman = pluginapi.PluginManager()

        self.user_password = '4cc355_70k3N'
        self.user = fixture_add_user('joauth', self.user_password)

        self.login()

    def login(self):
        self.app.post(
                '/auth/login/', {
                    'username': self.user.username,
                    'password': self.user_password})

    def register_client(self, name, client_type, description=None,
            redirect_uri=''):
        return self.app.post(
                '/oauth/client/register', {
                    'name': name,
                    'description': description,
                    'type': client_type,
                    'redirect_uri': redirect_uri})

    def get_context(self, template_name):
        return template.TEMPLATE_TEST_CONTEXT[template_name]

    def test_1_public_client_registration_without_redirect_uri(self):
        ''' Test 'public' OAuth client registration without any redirect uri '''
        response = self.register_client('OMGOMGOMG', 'public',
                'OMGOMG Apache License v2')

        ctx = self.get_context('oauth/client/register.html')

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == 'OMGOMGOMG').first()

        assert response.status_int == 200

        # Should display an error
        assert ctx['form'].redirect_uri.errors

        # Should not pass through
        assert not client

    def test_2_successful_public_client_registration(self):
        ''' Successfully register a public client '''
        self.login()
        self.register_client('OMGOMG', 'public', 'OMG!',
                'http://foo.example')

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == 'OMGOMG').first()

        # Client should have been registered
        assert client

    def test_3_successful_confidential_client_reg(self):
        ''' Register a confidential OAuth client '''
        response = self.register_client('GMOGMO', 'confidential', 'NO GMO!')

        assert response.status_int == 302

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == 'GMOGMO').first()

        # Client should have been registered
        assert client

        return client

    def test_4_authorize_confidential_client(self):
        ''' Authorize a confidential client as a logged in user '''
        client = self.test_3_successful_confidential_client_reg()

        redirect_uri = 'https://foo.example'
        response = self.app.get('/oauth/authorize', {
                'client_id': client.identifier,
                'scope': 'admin',
                'redirect_uri': redirect_uri})

        # User-agent should NOT be redirected
        assert response.status_int == 200

        ctx = self.get_context('oauth/authorize.html')

        form = ctx['form']

        # Short for client authorization post reponse
        capr = self.app.post(
                '/oauth/client/authorize', {
                    'client_id': form.client_id.data,
                    'allow': 'Allow',
                    'next': form.next.data})

        assert capr.status_int == 302

        authorization_response = capr.follow()

        assert authorization_response.location.startswith(redirect_uri)

        return authorization_response
