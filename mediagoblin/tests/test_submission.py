
# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

    def test_missing_fields(self):
        # Test blank form
        # ---------------
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.file.errors == [u'You must provide a file.']

        # Test blank file
        # ---------------
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'test title'})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.file.errors == [u'You must provide a file.']


    def test_normal_uploads(self):
        # Test JPG
        # --------
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Normal upload 1'
                }, upload_files=[(
                    'file', GOOD_JPG)])

        # User should be redirected
        response.follow()
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
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Normal upload 2'
                }, upload_files=[(
                    'file', GOOD_PNG)])

        response.follow()
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/u/chris/')
        assert template.TEMPLATE_TEST_CONTEXT.has_key(
            'mediagoblin/user_pages/user.html')

    def test_tags(self):
        # Good tag string
        # --------
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Balanced Goblin',
                'tags': GOOD_TAG_STRING
                }, upload_files=[(
                    'file', GOOD_JPG)])

        # New media entry with correct tags should be created
        response.follow()
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/user_pages/user.html']
        request = context['request']
        media = request.db.MediaEntry.find({'title': 'Balanced Goblin'})[0]
        assert_equal(media['tags'],
                     [{'name': u'yin', 'slug': u'yin'},
                                            {'name': u'yang', 'slug': u'yang'}])

        # Test tags that are too long
        # ---------------
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Balanced Goblin',
                'tags': BAD_TAG_STRING
                }, upload_files=[(
                    'file', GOOD_JPG)])

        # Too long error should be raised
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.tags.errors == [
            u'Tags must be shorter than 50 characters.  Tags that are too long'\
             ': ffffffffffffffffffffffffffuuuuuuuuuuuuuuuuuuuuuuuuuu']

    def test_delete(self):
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Balanced Goblin',
                }, upload_files=[(
                    'file', GOOD_JPG)])

        # Post image
        response.follow()

        request = template.TEMPLATE_TEST_CONTEXT[
            'mediagoblin/user_pages/user.html']['request']

        media = request.db.MediaEntry.find({'title': 'Balanced Goblin'})[0]

        # Does media entry exist?
        assert_true(media)

        # Do not confirm deletion
        # ---------------------------------------------------
        response = self.test_app.post(
            request.urlgen('mediagoblin.user_pages.media_confirm_delete',
                           # No work: user=media.uploader().username,
                           user=self.test_user.username,
                           media=media._id),
            # no value means no confirm
            {})

        response.follow()

        request = template.TEMPLATE_TEST_CONTEXT[
            'mediagoblin/user_pages/user.html']['request']

        media = request.db.MediaEntry.find({'title': 'Balanced Goblin'})[0]

        # Does media entry still exist?
        assert_true(media)

        # Confirm deletion
        # ---------------------------------------------------
        response = self.test_app.post(
            request.urlgen('mediagoblin.user_pages.media_confirm_delete',
                           # No work: user=media.uploader().username,
                           user=self.test_user.username,
                           media=media._id),
            {'confirm': 'y'})

        response.follow()

        request = template.TEMPLATE_TEST_CONTEXT[
            'mediagoblin/user_pages/user.html']['request']

        # Does media entry still exist?
        assert_false(
            request.db.MediaEntry.find(
                {'_id': media._id}).count())

    def test_malicious_uploads(self):
        # Test non-suppoerted file with non-supported extension
        # -----------------------------------------------------
        template.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Malicious Upload 1'
                }, upload_files=[(
                    'file', EVIL_FILE)])

        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert re.match(r'^Could not extract any file extension from ".*?"$', str(form.file.errors[0]))
        assert len(form.file.errors) == 1

        # NOTE: The following 2 tests will ultimately fail, but they
        #   *will* pass the initial form submission step.  Instead,
        #   they'll be caught as failures during the processing step.

        # Test non-supported file with .jpg extension
        # -------------------------------------------
        template.clear_test_template_context()
        response = self.test_app.post(
           '/submit/', {
               'title': 'Malicious Upload 2'
               }, upload_files=[(
                   'file', EVIL_JPG)])
        response.follow()
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/u/chris/')

        entry = mg_globals.database.MediaEntry.find_one(
            {'title': 'Malicious Upload 2'})
        assert_equal(entry.state, 'failed')
        assert_equal(
            entry['fail_error'],
            u'mediagoblin.processing:BadMediaFail')

        # Test non-supported file with .png extension
        # -------------------------------------------
        template.clear_test_template_context()
        response = self.test_app.post(
           '/submit/', {
               'title': 'Malicious Upload 3'
               }, upload_files=[(
                   'file', EVIL_PNG)])
        response.follow()
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/u/chris/')

        entry = mg_globals.database.MediaEntry.find_one(
            {'title': 'Malicious Upload 3'})
        assert_equal(entry.state, 'failed')
        assert_equal(
            entry['fail_error'],
            u'mediagoblin.processing:BadMediaFail')
