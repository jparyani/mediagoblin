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

import urllib

import pytest
import mock

from oauthlib.oauth1 import Client

from mediagoblin import mg_globals
from mediagoblin.tests.tools import fixture_add_user
from .resources import GOOD_JPG

class TestAPI(object):

    def setup(self):
        self.db = mg_globals.database
        self.user = fixture_add_user()

    def test_profile_endpoint(self, test_app):
        """ Test that you can successfully get the profile of a user """
        @mock.patch("mediagoblin.decorators.oauth_required")
        def _real_test(*args, **kwargs):
            profile = test_app.get(
                "/api/user/{0}/profile".format(self.user.username)
            ).json

            assert profile["preferredUsername"] == self.user.username
            assert profile["objectType"] == "person"

        _real_test()

    def test_upload_file(self, test_app):
        """ Test that i can upload a file """
        context = {
            "title": "Rel",
            "description": "ayRel sunu oeru",
            "qqfile": "my_picture.jpg",
        }
        encoded_context = urllib.urlencode(context)
        response = test_app.post(
            "/api/user/{0}/uploads?{1}".format(
                self.user.username,
                encoded_context[1:]
            )
        )

        picture = self.db.MediaEntry.query.filter_by(title=context["title"])
        picture = picture.first()

        assert response.status_int == 200
        assert picture
        raise Exception(str(dir(picture)))
        assert picture.description == context["description"]


