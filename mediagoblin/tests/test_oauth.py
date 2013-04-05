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
import logging

from urlparse import parse_qs, urlparse

from mediagoblin import mg_globals
from mediagoblin.tools import template, pluginapi
from mediagoblin.tests.tools import fixture_add_user


_log = logging.getLogger(__name__)


class TestOAuth(object):
    def _setup(self, test_app):
        self.db = mg_globals.database

        self.pman = pluginapi.PluginManager()

        self.user_password = u'4cc355_70k3N'
        self.user = fixture_add_user(u'joauth', self.user_password)

        self.login(test_app)

    def login(self, test_app):
        test_app.post(
                '/auth/login/', {
                    'username': self.user.username,
                    'password': self.user_password})

    def register_client(self, test_app, name, client_type, description=None,
            redirect_uri=''):
        return test_app.post(
                '/oauth/client/register', {
                    'name': name,
                    'description': description,
                    'type': client_type,
                    'redirect_uri': redirect_uri})

    def get_context(self, template_name):
        return template.TEMPLATE_TEST_CONTEXT[template_name]

    def test_1_public_client_registration_without_redirect_uri(self, test_app):
        ''' Test 'public' OAuth client registration without any redirect uri '''
        self._setup(test_app)

        response = self.register_client(test_app, u'OMGOMGOMG', 'public',
                'OMGOMG Apache License v2')

        ctx = self.get_context('oauth/client/register.html')

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == u'OMGOMGOMG').first()

        assert response.status_int == 200

        # Should display an error
        assert ctx['form'].redirect_uri.errors

        # Should not pass through
        assert not client

    def test_2_successful_public_client_registration(self, test_app):
        ''' Successfully register a public client '''
        self._setup(test_app)
        self.register_client(test_app, u'OMGOMG', 'public', 'OMG!',
                'http://foo.example')

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == u'OMGOMG').first()

        # Client should have been registered
        assert client

    def test_3_successful_confidential_client_reg(self, test_app):
        ''' Register a confidential OAuth client '''
        self._setup(test_app)

        response = self.register_client(
            test_app, u'GMOGMO', 'confidential', 'NO GMO!')

        assert response.status_int == 302

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == u'GMOGMO').first()

        # Client should have been registered
        assert client

        return client

    def test_4_authorize_confidential_client(self, test_app):
        ''' Authorize a confidential client as a logged in user '''
        self._setup(test_app)

        client = self.test_3_successful_confidential_client_reg(test_app)

        client_identifier = client.identifier

        redirect_uri = 'https://foo.example'
        response = test_app.get('/oauth/authorize', {
                'client_id': client.identifier,
                'scope': 'admin',
                'redirect_uri': redirect_uri})

        # User-agent should NOT be redirected
        assert response.status_int == 200

        ctx = self.get_context('oauth/authorize.html')

        form = ctx['form']

        # Short for client authorization post reponse
        capr = test_app.post(
                '/oauth/client/authorize', {
                    'client_id': form.client_id.data,
                    'allow': 'Allow',
                    'next': form.next.data})

        assert capr.status_int == 302

        authorization_response = capr.follow()

        assert authorization_response.location.startswith(redirect_uri)

        return authorization_response, client_identifier

    def get_code_from_redirect_uri(self, uri):
        return parse_qs(urlparse(uri).query)['code'][0]

    def test_token_endpoint_successful_confidential_request(self, test_app):
        ''' Successful request against token endpoint '''
        self._setup(test_app)

        code_redirect, client_id = self.test_4_authorize_confidential_client(
            test_app)

        code = self.get_code_from_redirect_uri(code_redirect.location)

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.identifier == unicode(client_id)).first()

        token_res = test_app.get('/oauth/access_token?client_id={0}&\
code={1}&client_secret={2}'.format(client_id, code, client.secret))

        assert token_res.status_int == 200

        token_data = json.loads(token_res.body)

        assert not 'error' in token_data
        assert 'access_token' in token_data
        assert 'token_type' in token_data
        assert 'expires_in' in token_data
        assert type(token_data['expires_in']) == int
        assert token_data['expires_in'] > 0

    def test_token_endpont_missing_id_confidential_request(self, test_app):
        ''' Unsuccessful request against token endpoint, missing client_id '''
        self._setup(test_app)

        code_redirect, client_id = self.test_4_authorize_confidential_client(
            test_app)

        code = self.get_code_from_redirect_uri(code_redirect.location)

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.identifier == unicode(client_id)).first()

        token_res = test_app.get('/oauth/access_token?\
code={0}&client_secret={1}'.format(code, client.secret))

        assert token_res.status_int == 200

        token_data = json.loads(token_res.body)

        assert 'error' in token_data
        assert not 'access_token' in token_data
        assert token_data['error'] == 'invalid_request'
        assert token_data['error_description'] == 'Missing client_id in request'
