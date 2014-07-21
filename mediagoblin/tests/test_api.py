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
import datetime

import mock
import pytz
import pytest

from webtest import AppError
from werkzeug.datastructures import FileStorage

from .resources import GOOD_JPG
from mediagoblin import mg_globals
from mediagoblin.media_types import sniff_media
from mediagoblin.db.models import User, MediaEntry
from mediagoblin.submit.lib import new_upload_entry
from mediagoblin.tests.tools import fixture_add_user
from mediagoblin.federation.task import collect_garbage
from mediagoblin.moderation.tools import take_away_privileges

class TestAPI(object):
    """ Test mediagoblin's pump.io complient APIs """

    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app
        self.db = mg_globals.database

        self.user = fixture_add_user(privileges=[u'active', u'uploader'])

    def _activity_to_feed(self, test_app, activity, headers=None):
        """ Posts an activity to the user's feed """
        if headers:
            headers.setdefault("Content-Type", "application/json")
        else:
            headers = {"Content-Type": "application/json"}

        with mock.patch("mediagoblin.decorators.oauth_required",
                        new_callable=self.mocked_oauth_required):
            response = test_app.post(
                "/api/user/{0}/feed".format(self.user.username),
                json.dumps(activity),
                headers=headers
            )

        return response, json.loads(response.body)

    def _upload_image(self, test_app, image):
        """ Uploads and image to MediaGoblin via pump.io API """
        data = open(image, "rb").read()
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(data))
        }


        with mock.patch("mediagoblin.decorators.oauth_required",
                        new_callable=self.mocked_oauth_required):
            response = test_app.post(
                "/api/user/{0}/uploads".format(self.user.username),
                data,
                headers=headers
            )
            image = json.loads(response.body)

        return response, image

    def _post_image_to_feed(self, test_app, image):
        """ Posts an already uploaded image to feed """
        activity = {
            "verb": "post",
            "object": image,
        }

        return self._activity_to_feed(test_app, activity)


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
        response, image = self._upload_image(test_app, GOOD_JPG)

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

        # Check that we got the response we're expecting
        response, _ = self._post_image_to_feed(test_app, image)
        assert response.status_code == 200

    def test_upload_image_with_filename(self, test_app):
        """ Tests that you can upload an image with filename and description """
        response, data = self._upload_image(test_app, GOOD_JPG)
        response, data = self._post_image_to_feed(test_app, data)

        image = data["object"]

        # Now we need to add a title and description
        title = "My image ^_^"
        description = "This is my super awesome image :D"
        license = "CC-BY-SA"

        image["displayName"] = title
        image["content"] = description
        image["license"] = license

        activity = {"verb": "update", "object": image}

        with mock.patch("mediagoblin.decorators.oauth_required",
                        new_callable=self.mocked_oauth_required):
            response = test_app.post(
                "/api/user/{0}/feed".format(self.user.username),
                json.dumps(activity),
                headers={"Content-Type": "application/json"}
            )

        image = json.loads(response.body)["object"]

        # Check everything has been set on the media correctly
        media = MediaEntry.query.filter_by(id=image["id"]).first()
        assert media.title == title
        assert media.description == description
        assert media.license == license

        # Check we're being given back everything we should on an update
        assert image["id"] == media.id
        assert image["displayName"] == title
        assert image["content"] == description
        assert image["license"] == license


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

        with mock.patch("mediagoblin.decorators.oauth_required",
                        new_callable=self.mocked_oauth_required):
            with pytest.raises(AppError) as excinfo:
                test_app.post(
                    "/api/user/{0}/uploads".format(self.user.username),
                    data,
                    headers=headers
                )

            # Assert that we've got a 403
            assert "403 FORBIDDEN" in excinfo.value.message

    def test_object_endpoint(self, test_app):
        """ Tests that object can be looked up at endpoint """
        # Post an image
        response, data = self._upload_image(test_app, GOOD_JPG)
        response, data = self._post_image_to_feed(test_app, data)

        # Now lookup image to check that endpoint works.
        image = data["object"]

        assert "links" in image
        assert "self" in image["links"]

        # Get URI and strip testing host off
        object_uri = image["links"]["self"]["href"]
        object_uri = object_uri.replace("http://localhost:80", "")

        with mock.patch("mediagoblin.decorators.oauth_required",
                        new_callable=self.mocked_oauth_required):
            request = test_app.get(object_uri)

        image = json.loads(request.body)
        entry = MediaEntry.query.filter_by(id=image["id"]).first()

        assert request.status_code == 200
        assert entry.id == image["id"]

        assert "image" in image
        assert "fullImage" in image
        assert "pump_io" in image
        assert "links" in image

    def test_post_comment(self, test_app):
        """ Tests that I can post an comment media """
        # Upload some media to comment on
        response, data = self._upload_image(test_app, GOOD_JPG)
        response, data = self._post_image_to_feed(test_app, data)

        content = "Hai this is a comment on this lovely picture ^_^"

        activity = {
            "verb": "post",
            "object": {
                "objectType": "comment",
                "content": content,
                "inReplyTo": data["object"],
            }
        }

        response, comment_data = self._activity_to_feed(test_app, activity)
        assert response.status_code == 200

        # Find the objects in the database
        media = MediaEntry.query.filter_by(id=data["object"]["id"]).first()
        comment = media.get_comments()[0]

        # Tests that it matches in the database
        assert comment.author == self.user.id
        assert comment.content == content

        # Test that the response is what we should be given
        assert comment.id == comment_data["object"]["id"]
        assert comment.content == comment_data["object"]["content"]

    def test_profile(self, test_app):
        """ Tests profile endpoint """
        uri = "/api/user/{0}/profile".format(self.user.username)
        with mock.patch("mediagoblin.decorators.oauth_required",
                        new_callable=self.mocked_oauth_required):
            response = test_app.get(uri)
            profile = json.loads(response.body)

            assert response.status_code == 200

            assert profile["preferredUsername"] == self.user.username
            assert profile["objectType"] == "person"

            assert "links" in profile

    def test_garbage_collection_task(self, test_app):
        """ Test old media entry are removed by GC task """
        # Create a media entry that's unprocessed and over an hour old.
        entry_id = 72
        now = datetime.datetime.now(pytz.UTC)
        file_data = FileStorage(
            stream=open(GOOD_JPG, "rb"),
            filename="mah_test.jpg",
            content_type="image/jpeg"
        )

        # Find media manager
        media_type, media_manager = sniff_media(file_data, "mah_test.jpg")
        entry = new_upload_entry(self.user)
        entry.id = entry_id
        entry.title = "Mah Image"
        entry.slug = "slugy-slug-slug"
        entry.media_type = 'image'
        entry.uploaded = now - datetime.timedelta(days=2)
        entry.save()

        # Validate the model exists
        assert MediaEntry.query.filter_by(id=entry_id).first() is not None

        # Call the garbage collection task
        collect_garbage()

        # Now validate the image has been deleted
        assert MediaEntry.query.filter_by(id=entry_id).first() is None
