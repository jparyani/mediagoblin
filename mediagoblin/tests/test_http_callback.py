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

import pytest
from urlparse import urlparse, parse_qs

from mediagoblin import mg_globals
from mediagoblin.tools import processing
from mediagoblin.tests.tools import fixture_add_user
from mediagoblin.tests.test_submission import GOOD_PNG
from mediagoblin.tests import test_oauth2 as oauth


class TestHTTPCallback(object):
    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app

        self.db = mg_globals.database

        self.user_password = u'secret'
        self.user = fixture_add_user(u'call_back', self.user_password)

        self.login()

    def login(self):
        self.test_app.post('/auth/login/', {
            'username': self.user.username,
            'password': self.user_password})

    def get_access_token(self, client_id, client_secret, code):
        response = self.test_app.get('/oauth-2/access_token', {
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret})

        response_data = json.loads(response.body)

        return response_data['access_token']

    def test_callback(self):
        ''' Test processing HTTP callback '''
        self.oauth = oauth.TestOAuth()
        self.oauth.setup(self.test_app)

        redirect, client_id = self.oauth.test_4_authorize_confidential_client()

        code = parse_qs(urlparse(redirect.location).query)['code'][0]

        client = self.db.OAuthClient.query.filter(
                self.db.OAuthClient.identifier == unicode(client_id)).first()

        client_secret = client.secret

        access_token = self.get_access_token(client_id, client_secret, code)

        callback_url = 'https://foo.example?secrettestmediagoblinparam'

        self.test_app.post('/api/submit?client_id={0}&access_token={1}\
&client_secret={2}'.format(
                    client_id,
                    access_token,
                    client_secret), {
            'title': 'Test',
            'callback_url': callback_url},
            upload_files=[('file', GOOD_PNG)])

        assert processing.TESTS_CALLBACKS[callback_url]['state'] == u'processed'
