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

import pytest
from urlparse import parse_qs, urlparse

from mediagoblin import mg_globals
from mediagoblin.tools import template, pluginapi
from mediagoblin.tests.tools import fixture_add_user


_log = logging.getLogger(__name__)


class TestOAuth(object):
    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app

        self.db = mg_globals.database

        self.pman = pluginapi.PluginManager()

        self.user_password = u'4cc355_70k3N'
        self.user = fixture_add_user(u'joauth', self.user_password)

        self.login()

    def login(self):
        self.test_app.post(
            '/auth/login/', {
                'username': self.user.username,
                'password': self.user_password})

    def register_client(self, name, client_type, description=None,
                        redirect_uri=''):
        return self.test_app.post(
                '/oauth-2/client/register', {
                    'name': name,
                    'description': description,
                    'type': client_type,
                    'redirect_uri': redirect_uri})

    def get_context(self, template_name):
        return template.TEMPLATE_TEST_CONTEXT[template_name]

    def test_1_public_client_registration_without_redirect_uri(self):
        ''' Test 'public' OAuth client registration without any redirect uri '''
        response = self.register_client(
            u'OMGOMGOMG', 'public', 'OMGOMG Apache License v2')

        ctx = self.get_context('oauth/client/register.html')

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == u'OMGOMGOMG').first()

        assert response.status_int == 200

        # Should display an error
        assert len(ctx['form'].redirect_uri.errors)

        # Should not pass through
        assert not client

    def test_2_successful_public_client_registration(self):
        ''' Successfully register a public client '''
        uri = 'http://foo.example'
        self.register_client(
            u'OMGOMG', 'public', 'OMG!', uri)

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == u'OMGOMG').first()

        # redirect_uri should be set
        assert client.redirect_uri == uri

        # Client should have been registered
        assert client

    def test_3_successful_confidential_client_reg(self):
        ''' Register a confidential OAuth client '''
        response = self.register_client(
            u'GMOGMO', 'confidential', 'NO GMO!')

        assert response.status_int == 302

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.name == u'GMOGMO').first()

        # Client should have been registered
        assert client

        return client

    def test_4_authorize_confidential_client(self):
        ''' Authorize a confidential client as a logged in user '''
        client = self.test_3_successful_confidential_client_reg()

        client_identifier = client.identifier

        redirect_uri = 'https://foo.example'
        response = self.test_app.get('/oauth-2/authorize', {
                'client_id': client.identifier,
                'scope': 'all',
                'redirect_uri': redirect_uri})

        # User-agent should NOT be redirected
        assert response.status_int == 200

        ctx = self.get_context('oauth/authorize.html')

        form = ctx['form']

        # Short for client authorization post reponse
        capr = self.test_app.post(
                '/oauth-2/client/authorize', {
                    'client_id': form.client_id.data,
                    'allow': 'Allow',
                    'next': form.next.data})

        assert capr.status_int == 302

        authorization_response = capr.follow()

        assert authorization_response.location.startswith(redirect_uri)

        return authorization_response, client_identifier

    def get_code_from_redirect_uri(self, uri):
        ''' Get the value of ?code= from an URI '''
        return parse_qs(urlparse(uri).query)['code'][0]

    def test_token_endpoint_successful_confidential_request(self):
        ''' Successful request against token endpoint '''
        code_redirect, client_id = self.test_4_authorize_confidential_client()

        code = self.get_code_from_redirect_uri(code_redirect.location)

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.identifier == unicode(client_id)).first()

        token_res = self.test_app.get('/oauth-2/access_token?client_id={0}&\
code={1}&client_secret={2}'.format(client_id, code, client.secret))

        assert token_res.status_int == 200

        token_data = json.loads(token_res.body)

        assert not 'error' in token_data
        assert 'access_token' in token_data
        assert 'token_type' in token_data
        assert 'expires_in' in token_data
        assert type(token_data['expires_in']) == int
        assert token_data['expires_in'] > 0

        # There should be a refresh token provided in the token data
        assert len(token_data['refresh_token'])

        return client_id, token_data

    def test_token_endpont_missing_id_confidential_request(self):
        ''' Unsuccessful request against token endpoint, missing client_id '''
        code_redirect, client_id = self.test_4_authorize_confidential_client()

        code = self.get_code_from_redirect_uri(code_redirect.location)

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.identifier == unicode(client_id)).first()

        token_res = self.test_app.get('/oauth-2/access_token?\
code={0}&client_secret={1}'.format(code, client.secret))

        assert token_res.status_int == 200

        token_data = json.loads(token_res.body)

        assert 'error' in token_data
        assert not 'access_token' in token_data
        assert token_data['error'] == 'invalid_request'
        assert len(token_data['error_description'])

    def test_refresh_token(self):
        ''' Try to get a new access token using the refresh token '''
        # Get an access token and a refresh token
        client_id, token_data =\
            self.test_token_endpoint_successful_confidential_request()

        client = self.db.OAuthClient.query.filter(
            self.db.OAuthClient.identifier == client_id).first()

        token_res = self.test_app.get('/oauth-2/access_token',
                     {'refresh_token': token_data['refresh_token'],
                      'client_id': client_id,
                      'client_secret': client.secret
                      })

        assert token_res.status_int == 200

        new_token_data = json.loads(token_res.body)

        assert not 'error' in new_token_data
        assert 'access_token' in new_token_data
        assert 'token_type' in new_token_data
        assert 'expires_in' in new_token_data
        assert type(new_token_data['expires_in']) == int
        assert new_token_data['expires_in'] > 0
