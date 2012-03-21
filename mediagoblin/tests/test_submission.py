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

import urlparse
import pkg_resources
import re

from nose.tools import assert_equal, assert_true, assert_false

from mediagoblin.tests.tools import setup_fresh_app, get_test_app, \
    fixture_add_user
from mediagoblin import mg_globals
from mediagoblin.tools import template, common

GOOD_JPG = pkg_resources.resource_filename(
  'mediagoblin.tests', 'test_submission/good.jpg')
GOOD_PNG = pkg_resources.resource_filename(
  'mediagoblin.tests', 'test_submission/good.png')
EVIL_FILE = pkg_resources.resource_filename(
  'mediagoblin.tests', 'test_submission/evil')
EVIL_JPG = pkg_resources.resource_filename(
  'mediagoblin.tests', 'test_submission/evil.jpg')
EVIL_PNG = pkg_resources.resource_filename(
  'mediagoblin.tests', 'test_submission/evil.png')

GOOD_TAG_STRING = 'yin,yang'
BAD_TAG_STRING = 'rage,' + 'f' * 26 + 'u' * 26

FORM_CONTEXT = ['mediagoblin/submit/start.html', 'submit_form']
REQUEST_CONTEXT = ['mediagoblin/user_pages/user.html', 'request']

class TestSubmission:
    def setUp(self):
        self.test_app = get_test_app()

        # TODO: Possibly abstract into a decorator like:
        # @as_authenticated_user('chris')
        test_user = fixture_add_user()

        self.test_user = test_user

        self.login()

    def login(self):
        self.test_app.post(
            '/auth/login/', {
                'username': u'chris',
                'password': 'toast'})

    def logout(self):
        self.test_app.get('/auth/logout/')

    def do_post(self, data, *context_keys, **kwargs):
        url = kwargs.pop('url', '/submit/')
        do_follow = kwargs.pop('do_follow', False)
        template.clear_test_template_context()
        response = self.test_app.post(url, data, **kwargs)
        if do_follow:
            response.follow()
        context_data = template.TEMPLATE_TEST_CONTEXT
        for key in context_keys:
            context_data = context_data[key]
        return response, context_data
        
    def upload_data(self, filename):
        return {'upload_files': [('file', filename)]}

    def test_missing_fields(self):
        # Test blank form
        # ---------------
        response, form = self.do_post({}, *FORM_CONTEXT)
        assert form.file.errors == [u'You must provide a file.']

        # Test blank file
        # ---------------
        response, form = self.do_post({'title': 'test title'}, *FORM_CONTEXT)
        assert form.file.errors == [u'You must provide a file.']


    def test_normal_uploads(self):
        # Test JPG
        # --------
        response, context = self.do_post({'title': 'Normal upload 1'},
                                         do_follow=True,
                                         **self.upload_data(GOOD_JPG))
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/u/chris/')
        assert template.TEMPLATE_TEST_CONTEXT.has_key(
            'mediagoblin/user_pages/user.html')

        # Make sure the media view is at least reachable, logged in...
        self.test_app.get('/u/chris/m/normal-upload-1/')
        # ... and logged out too.
        self.logout()
        self.test_app.get('/u/chris/m/normal-upload-1/')
        # Log back in for the remaining tests.
        self.login()

        # Test PNG
        # --------
        response, context = self.do_post({'title': 'Normal upload 2'},
                                         do_follow=True,
                                         **self.upload_data(GOOD_PNG))
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/u/chris/')
        assert template.TEMPLATE_TEST_CONTEXT.has_key(
            'mediagoblin/user_pages/user.html')

    def check_media(self, request, find_data, count=None):
        media = request.db.MediaEntry.find(find_data)
        if count is not None:
            assert_equal(media.count(), count)
            if count == 0:
                return
        return media[0]

    def test_tags(self):
        # Good tag string
        # --------
        response, request = self.do_post({'title': 'Balanced Goblin',
                                          'tags': GOOD_TAG_STRING},
                                         *REQUEST_CONTEXT, do_follow=True,
                                         **self.upload_data(GOOD_JPG))
        media = self.check_media(request, {'title': 'Balanced Goblin'}, 1)
        assert_equal(media.tags,
                     [{'name': u'yin', 'slug': u'yin'},
                      {'name': u'yang', 'slug': u'yang'}])

        # Test tags that are too long
        # ---------------
        response, form = self.do_post({'title': 'Balanced Goblin',
                                       'tags': BAD_TAG_STRING},
                                      *FORM_CONTEXT,
                                      **self.upload_data(GOOD_JPG))
        assert form.tags.errors == [
            u'Tags must be shorter than 50 characters.  Tags that are too long'\
             ': ffffffffffffffffffffffffffuuuuuuuuuuuuuuuuuuuuuuuuuu']

    def test_delete(self):
        response, request = self.do_post({'title': 'Balanced Goblin'},
                                         *REQUEST_CONTEXT, do_follow=True,
                                         **self.upload_data(GOOD_JPG))
        media = self.check_media(request, {'title': 'Balanced Goblin'}, 1)

        # Do not confirm deletion
        # ---------------------------------------------------
        delete_url = request.urlgen(
            'mediagoblin.user_pages.media_confirm_delete',
            user=self.test_user.username, media=media._id)
        # Empty data means don't confirm
        response = self.do_post({}, do_follow=True, url=delete_url)[0]
        media = self.check_media(request, {'title': 'Balanced Goblin'}, 1)

        # Confirm deletion
        # ---------------------------------------------------
        response, request = self.do_post({'confirm': 'y'}, *REQUEST_CONTEXT,
                                         do_follow=True, url=delete_url)
        self.check_media(request, {'_id': media._id}, 0)

    def test_malicious_uploads(self):
        # Test non-suppoerted file with non-supported extension
        # -----------------------------------------------------
        response, form = self.do_post({'title': 'Malicious Upload 1'},
                                      *FORM_CONTEXT,
                                      **self.upload_data(EVIL_FILE))
        assert re.match(r'^Could not extract any file extension from ".*?"$', str(form.file.errors[0]))
        assert len(form.file.errors) == 1

        # NOTE: The following 2 tests will ultimately fail, but they
        #   *will* pass the initial form submission step.  Instead,
        #   they'll be caught as failures during the processing step.

        # Test non-supported file with .jpg extension
        # -------------------------------------------
        response, context = self.do_post({'title': 'Malicious Upload 2'},
                                         do_follow=True,
                                         **self.upload_data(EVIL_JPG))
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/u/chris/')

        entry = mg_globals.database.MediaEntry.find_one(
            {'title': 'Malicious Upload 2'})
        assert_equal(entry.state, 'failed')
        assert_equal(
            entry.fail_error,
            u'mediagoblin.processing:BadMediaFail')

        # Test non-supported file with .png extension
        # -------------------------------------------
        response, context = self.do_post({'title': 'Malicious Upload 3'},
                                         do_follow=True,
                                         **self.upload_data(EVIL_PNG))
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/u/chris/')

        entry = mg_globals.database.MediaEntry.find_one(
            {'title': 'Malicious Upload 3'})
        assert_equal(entry.state, 'failed')
        assert_equal(
            entry.fail_error,
            u'mediagoblin.processing:BadMediaFail')
