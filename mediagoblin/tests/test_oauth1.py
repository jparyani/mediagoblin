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

import cgi

import pytest
from urlparse import parse_qs, urlparse

from oauthlib.oauth1 import Client

from mediagoblin import mg_globals
from mediagoblin.tools import template, pluginapi
from mediagoblin.tests.tools import fixture_add_user


class TestOAuth(object):

    MIME_FORM = "application/x-www-form-urlencoded"
    MIME_JSON = "application/json"

    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app

        self.db = mg_globals.database

        self.pman = pluginapi.PluginManager()

        self.user_password = "AUserPassword123"
        self.user = fixture_add_user("OAuthy", self.user_password)

        self.login()

    def login(self):
        self.test_app.post(
            "/auth/login/", {
                "username": self.user.username,
                "password": self.user_password})

    def register_client(self, **kwargs):
        """ Regiters a client with the API """
        
        kwargs["type"] = "client_associate"        
        kwargs["application_type"] = kwargs.get("application_type", "native")
        return self.test_app.post("/api/client/register", kwargs)

    def test_client_client_register_limited_info(self):
        """ Tests that a client can be registered with limited information """
        response = self.register_client()
        client_info = response.json

        client = self.db.Client.query.filter_by(id=client_info["client_id"]).first()
        
        assert response.status_int == 200
        assert client is not None

    def test_client_register_full_info(self):
        """ Provides every piece of information possible to register client """
        query = {
                "application_name": "Testificate MD",
                "application_type": "web",
                "contacts": "someone@someplace.com tuteo@tsengeo.lu",
                "logo_url": "http://ayrel.com/utral.png",
                "redirect_uris": "http://navi-kosman.lu http://gmg-yawne-oeru.lu",
                }

        response = self.register_client(**query)
        client_info = response.json

        client = self.db.Client.query.filter_by(id=client_info["client_id"]).first()
        
        assert client is not None
        assert client.secret == client_info["client_secret"]
        assert client.application_type == query["application_type"]
        assert client.redirect_uri == query["redirect_uris"].split()
        assert client.logo_url == query["logo_url"]
        assert client.contacts == query["contacts"].split()


    def test_client_update(self):
        """ Tests that you can update a client """
        # first we need to register a client
        response = self.register_client()

        client_info = response.json
        client = self.db.Client.query.filter_by(id=client_info["client_id"]).first()

        # Now update
        update_query = {
                "type": "client_update",
                "application_name": "neytiri",
                "contacts": "someone@someplace.com abc@cba.com",
                "logo_url": "http://place.com/picture.png",
                "application_type": "web",
                "redirect_uris": "http://blah.gmg/whatever https://inboxen.org/",
                }

        update_response = self.register_client(**update_query)

        assert update_response.status_int == 200
        client_info = update_response.json
        client = self.db.Client.query.filter_by(id=client_info["client_id"]).first()

        assert client.secret == client_info["client_secret"]
        assert client.application_type == update_query["application_type"]
        assert client.application_name == update_query["application_name"]
        assert client.contacts == update_query["contacts"].split()
        assert client.logo_url == update_query["logo_url"]
        assert client.redirect_uri == update_query["redirect_uris"].split()

    def to_authorize_headers(self, data):
        headers = ""
        for key, value in data.items():
            headers += '{0}="{1}",'.format(key, value)
        return {"Authorization": "OAuth " + headers[:-1]}

    def test_request_token(self):
        """ Test a request for a request token """
        response = self.register_client()

        client_id = response.json["client_id"]

        endpoint = "/oauth/request_token"
        request_query = {
                "oauth_consumer_key": client_id,
                "oauth_nonce": "abcdefghij",
                "oauth_timestamp": 123456789.0,
                "oauth_callback": "https://some.url/callback",
                }

        headers = self.to_authorize_headers(request_query)

        headers["Content-Type"] = self.MIME_FORM

        response = self.test_app.post(endpoint, headers=headers)
        response = cgi.parse_qs(response.body)

        # each element is a list, reduce it to a string
        for key, value in response.items():
            response[key] = value[0]

        request_token = self.db.RequestToken.query.filter_by(
                token=response["oauth_token"]
                ).first()

        client = self.db.Client.query.filter_by(id=client_id).first()

        assert request_token is not None
        assert request_token.secret == response["oauth_token_secret"]
        assert request_token.client == client.id
        assert request_token.used == False
        assert request_token.callback == request_query["oauth_callback"]
        
