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

try:
    import mock
except ImportError:
    import unittest.mock as mock
import pytest

from webtest import AppError

from .resources import GOOD_JPG
from mediagoblin import mg_globals
from mediagoblin.db.models import User, MediaEntry, MediaComment
from mediagoblin.tools.routing import extract_url_arguments
from mediagoblin.tests.tools import fixture_add_user
from mediagoblin.moderation.tools import take_away_privileges

class TestAPI(object):
    """ Test mediagoblin's pump.io complient APIs """

    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app
        self.db = mg_globals.database

        self.user = fixture_add_user(privileges=[u'active', u'uploader', u'commenter'])
        self.other_user = fixture_add_user(
            username="otheruser",
            privileges=[u'active', u'uploader', u'commenter']
        )
        self.active_user = self.user

    def _activity_to_feed(self, test_app, activity, headers=None):
        """ Posts an activity to the user's feed """
        if headers:
            headers.setdefault("Content-Type", "application/json")
        else:
            headers = {"Content-Type": "application/json"}

        with self.mock_oauth():
            response = test_app.post(
                "/api/user/{0}/feed".format(self.active_user.username),
                json.dumps(activity),
                headers=headers
            )

        return response, json.loads(response.body.decode())

    def _upload_image(self, test_app, image):
        """ Uploads and image to MediaGoblin via pump.io API """
        data = open(image, "rb").read()
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(data))
        }


        with self.mock_oauth():
            response = test_app.post(
                "/api/user/{0}/uploads".format(self.active_user.username),
                data,
                headers=headers
            )
            image = json.loads(response.body.decode())

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
            request.user = User.query.filter_by(id=self.active_user.id).first()
            return controller(request, *args, **kwargs)

        def oauth_required(c):
            return lambda *args, **kwargs: fake_controller(c, *args, **kwargs)

        return oauth_required

    def mock_oauth(self):
        """ Returns a mock.patch for the oauth_required decorator """
        return mock.patch(
            target="mediagoblin.decorators.oauth_required",
            new_callable=self.mocked_oauth_required
        )

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

    def test_unable_to_upload_as_someone_else(self, test_app):
        """ Test that can't upload as someoen else """
        data = open(GOOD_JPG, "rb").read()
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(data))
        }

        with self.mock_oauth():
            # Will be self.user trying to upload as self.other_user
            with pytest.raises(AppError) as excinfo:
                test_app.post(
                    "/api/user/{0}/uploads".format(self.other_user.username),
                    data,
                    headers=headers
                )

            assert "403 FORBIDDEN" in excinfo.value.args[0]

    def test_unable_to_post_feed_as_someone_else(self, test_app):
        """ Tests that can't post an image to someone else's feed """
        response, data = self._upload_image(test_app, GOOD_JPG)

        activity = {
            "verb": "post",
            "object": data
        }

        headers = {
            "Content-Type": "application/json",
        }

        with self.mock_oauth():
            with pytest.raises(AppError) as excinfo:
                test_app.post(
                    "/api/user/{0}/feed".format(self.other_user.username),
                    json.dumps(activity),
                    headers=headers
                )

            assert "403 FORBIDDEN" in excinfo.value.args[0]

    def test_only_able_to_update_own_image(self, test_app):
        """ Test's that the uploader is the only person who can update an image """
        response, data = self._upload_image(test_app, GOOD_JPG)
        response, data = self._post_image_to_feed(test_app, data)

        activity = {
            "verb": "update",
            "object": data["object"],
        }

        headers = {
            "Content-Type": "application/json",
        }

        # Lets change the image uploader to be self.other_user, this is easier
        # than uploading the image as someone else as the way self.mocked_oauth_required
        # and self._upload_image.
        id = int(data["object"]["id"].split("/")[-1])
        media = MediaEntry.query.filter_by(id=id).first()
        media.uploader = self.other_user.id
        media.save()

        # Now lets try and edit the image as self.user, this should produce a 403 error.
        with self.mock_oauth():
            with pytest.raises(AppError) as excinfo:
                test_app.post(
                    "/api/user/{0}/feed".format(self.user.username),
                    json.dumps(activity),
                    headers=headers
                )

            assert "403 FORBIDDEN" in excinfo.value.args[0]

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

        with self.mock_oauth():
            response = test_app.post(
                "/api/user/{0}/feed".format(self.user.username),
                json.dumps(activity),
                headers={"Content-Type": "application/json"}
            )

        image = json.loads(response.body.decode())["object"]

        # Check everything has been set on the media correctly
        id = int(image["id"].split("/")[-1])
        media = MediaEntry.query.filter_by(id=id).first()
        assert media.title == title
        assert media.description == description
        assert media.license == license

        # Check we're being given back everything we should on an update
        assert int(image["id"].split("/")[-1]) == media.id
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

        with self.mock_oauth():
            with pytest.raises(AppError) as excinfo:
                test_app.post(
                    "/api/user/{0}/uploads".format(self.user.username),
                    data,
                    headers=headers
                )

            # Assert that we've got a 403
            assert "403 FORBIDDEN" in excinfo.value.args[0]

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

        with self.mock_oauth():
            request = test_app.get(object_uri)

        image = json.loads(request.body.decode())
        entry_id = int(image["id"].split("/")[-1])
        entry = MediaEntry.query.filter_by(id=entry_id).first()

        assert request.status_code == 200

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
        media_id = int(data["object"]["id"].split("/")[-1])
        media = MediaEntry.query.filter_by(id=media_id).first()
        comment = media.get_comments()[0]

        # Tests that it matches in the database
        assert comment.author == self.user.id
        assert comment.content == content

        # Test that the response is what we should be given
        assert comment.content == comment_data["object"]["content"]

    def test_unable_to_post_comment_as_someone_else(self, test_app):
        """ Tests that you're unable to post a comment as someone else. """
        # Upload some media to comment on
        response, data = self._upload_image(test_app, GOOD_JPG)
        response, data = self._post_image_to_feed(test_app, data)

        activity = {
            "verb": "post",
            "object": {
                "objectType": "comment",
                "content": "comment commenty comment ^_^",
                "inReplyTo": data["object"],
            }
        }

        headers = {
            "Content-Type": "application/json",
        }

        with self.mock_oauth():
            with pytest.raises(AppError) as excinfo:
                test_app.post(
                    "/api/user/{0}/feed".format(self.other_user.username),
                    json.dumps(activity),
                    headers=headers
                )

            assert "403 FORBIDDEN" in excinfo.value.args[0]

    def test_unable_to_update_someone_elses_comment(self, test_app):
        """ Test that you're able to update someoen elses comment. """
        # Upload some media to comment on
        response, data = self._upload_image(test_app, GOOD_JPG)
        response, data = self._post_image_to_feed(test_app, data)

        activity = {
            "verb": "post",
            "object": {
                "objectType": "comment",
                "content": "comment commenty comment ^_^",
                "inReplyTo": data["object"],
            }
        }

        headers = {
            "Content-Type": "application/json",
        }

        # Post the comment.
        response, comment_data = self._activity_to_feed(test_app, activity)

        # change who uploaded the comment as it's easier than changing
        comment_id = int(comment_data["object"]["id"].split("/")[-1])
        comment = MediaComment.query.filter_by(id=comment_id).first()
        comment.author = self.other_user.id
        comment.save()

        # Update the comment as someone else.
        comment_data["object"]["content"] = "Yep"
        activity = {
            "verb": "update",
            "object": comment_data["object"]
        }

        with self.mock_oauth():
            with pytest.raises(AppError) as excinfo:
                test_app.post(
                    "/api/user/{0}/feed".format(self.user.username),
                    json.dumps(activity),
                    headers=headers
                )

            assert "403 FORBIDDEN" in excinfo.value.args[0]

    def test_profile(self, test_app):
        """ Tests profile endpoint """
        uri = "/api/user/{0}/profile".format(self.user.username)
        with self.mock_oauth():
            response = test_app.get(uri)
            profile = json.loads(response.body.decode())

            assert response.status_code == 200

            assert profile["preferredUsername"] == self.user.username
            assert profile["objectType"] == "person"

            assert "links" in profile

    def test_user(self, test_app):
        """ Test the user endpoint """
        uri = "/api/user/{0}/".format(self.user.username)
        with self.mock_oauth():
            response = test_app.get(uri)
            user = json.loads(response.body.decode())

            assert response.status_code == 200

            assert user["nickname"] == self.user.username
            assert user["updated"] == self.user.created.isoformat()
            assert user["published"] == self.user.created.isoformat()

            # Test profile exists but self.test_profile will test the value
            assert "profile" in response

    def test_whoami_without_login(self, test_app):
        """ Test that whoami endpoint returns error when not logged in """
        with pytest.raises(AppError) as excinfo:
            response = test_app.get("/api/whoami")

        assert "401 UNAUTHORIZED" in excinfo.value.args[0]

    def test_read_feed(self, test_app):
        """ Test able to read objects from the feed """
        response, data = self._upload_image(test_app, GOOD_JPG)
        response, data = self._post_image_to_feed(test_app, data)

        uri = "/api/user/{0}/feed".format(self.active_user.username)
        with self.mock_oauth():
            response = test_app.get(uri)
            feed = json.loads(response.body.decode())

            assert response.status_code == 200

            # Check it has the attributes it should
            assert "displayName" in feed
            assert "objectTypes" in feed
            assert "url" in feed
            assert "links" in feed
            assert "author" in feed
            assert "items" in feed

            # Check that image i uploaded is there
            assert feed["items"][0]["verb"] == "post"
            assert feed["items"][0]["actor"]

    def test_cant_post_to_someone_elses_feed(self, test_app):
        """ Test that can't post to someone elses feed """
        response, data = self._upload_image(test_app, GOOD_JPG)
        self.active_user = self.other_user

        with self.mock_oauth():
            with pytest.raises(AppError) as excinfo:
                self._post_image_to_feed(test_app, data)

            assert "403 FORBIDDEN" in excinfo.value.args[0]

    def test_object_endpoint_requestable(self, test_app):
        """ Test that object endpoint can be requested """
        response, data = self._upload_image(test_app, GOOD_JPG)
        response, data = self._post_image_to_feed(test_app, data)
        object_id = data["object"]["id"]

        with self.mock_oauth():
            response = test_app.get(data["object"]["links"]["self"]["href"])
            data = json.loads(response.body.decode())

            assert response.status_code == 200

            assert object_id == data["id"]
            assert "url" in data
            assert "links" in data
            assert data["objectType"] == "image"
