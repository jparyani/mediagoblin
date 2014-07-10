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
import json

import pytest
import mock

from webtest import AppError

from mediagoblin import mg_globals
from .resources import GOOD_JPG
from mediagoblin.db.models import User
from mediagoblin.tests.tools import fixture_add_user
from mediagoblin.moderation.tools import take_away_privileges
from .resources import GOOD_JPG, GOOD_PNG, EVIL_FILE, EVIL_JPG, EVIL_PNG, \
    BIG_BLUE

class TestAPI(object):

    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app
        self.db = mg_globals.database
        self.user = fixture_add_user(privileges=[u'active', u'uploader'])

    def mocked_oauth_required(self, *args, **kwargs):
        """ Mocks mediagoblin.decorator.oauth_required to always validate """

        def fake_controller(controller, request, *args, **kwargs):
            request.user = User.query.filter_by(id=self.user.id).first()
            return controller(request, *args, **kwargs)

        def oauth_required(c):
            return lambda *args, **kwargs: fake_controller(c, *args, **kwargs)

        return oauth_required

    def test_can_post_image(self, test_app):
        """ Tests that an image can be posted to the API """
        # First request we need to do is to upload the image
        data = open(GOOD_JPG, "rb").read()
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(data))
        }


        with mock.patch("mediagoblin.decorators.oauth_required", new_callable=self.mocked_oauth_required):
            response = test_app.post(
                "/api/user/{0}/uploads".format(self.user.username),
                data,
                headers=headers
            )
            image = json.loads(response.body)


            # I should have got certain things back
            assert response.status_code == 200

            assert "id" in image
            assert "fullImage" in image
            assert "url" in image["fullImage"]
            assert "url" in image
            assert "author" in image
            assert "published" in image
            assert "updated" in image
            assert image["objectType"] == "image"

            # Now post this to the feed
            activity = {
                "verb": "post",
                "object": image,
            }
            response = test_app.post(
                "/api/user/{0}/feed".format(self.user.username),
                activity
            )

            # Check that we got the response we're expecting
            assert response.status_code == 200

    def test_only_uploaders_post_image(self, test_app):
        """ Test that only uploaders can upload images """
        # Remove uploader permissions from user
        take_away_privileges(self.user.username, u"uploader")

        # Now try and upload a image
        data = open(GOOD_JPG, "rb").read()
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(data)),
        }

        with mock.patch("mediagoblin.decorators.oauth_required", new_callable=self.mocked_oauth_required):
            with pytest.raises(AppError) as excinfo:
                response = test_app.post(
                    "/api/user/{0}/uploads".format(self.user.username),
                    data,
                    headers=headers
                )

            # Assert that we've got a 403
            assert "403 FORBIDDEN" in excinfo.value.message
