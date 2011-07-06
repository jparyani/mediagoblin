# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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
from os import getcwd

from nose.tools import assert_equal

from mediagoblin.auth import lib as auth_lib
from mediagoblin.tests.tools import setup_fresh_app, get_test_app
from mediagoblin import mg_globals
from mediagoblin import util

IMAGE_ROOT = getcwd() + '/mediagoblin/tests/test_submission/'
GOOD_JPG = 'good.jpg'
GOOD_PNG = 'good.png'
EVIL_FILE = 'evil'
EVIL_JPG = 'evil.jpg'
EVIL_PNG = 'evil.png'


# TODO:
# - Define test files as globals
#   - supported mime types
#   - unsupported mime type with supported extension
# - Remove any imports that aren't neccessary

class TestSubmission:
    def setUp(self):
        self.test_app = get_test_app()

        # TODO: Possibly abstract into a decorator like:
        # @as_authenticated_user('chris')
        test_user = mg_globals.database.User()
        test_user['username'] = u'chris'
        test_user['email'] = u'chris@example.com'
        test_user['email_verified'] = True
        test_user['status'] = u'active'
        test_user['pw_hash'] = auth_lib.bcrypt_gen_password_hash('toast')
        test_user.save()

        self.test_app.post(
            '/auth/login/', {
                'username': u'chris',
                'password': 'toast'})

    def test_missing_fields(self):
        # Test blank form
        # ---------------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {})
        context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.file.errors == [u'You must provide a file.']

        # Test blank file
        # ---------------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'test title'})
        context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.file.errors == [u'You must provide a file.']


    def test_normal_uploads(self):
        # FYI:
        # upload_files is for file uploads. It should be a list of
        # [(fieldname, filename, file_content)]. You can also use
        # just [(fieldname, filename)] and the file content will be
        # read from disk.

        # Test JPG
        # --------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Normal upload 1'
                }, upload_files=[(
                    'file', IMAGE_ROOT + GOOD_JPG)])

        # User should be redirected
        response.follow()
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/submit/success/')
        assert util.TEMPLATE_TEST_CONTEXT.has_key(
            'mediagoblin/submit/success.html')

        # Test PNG
        # --------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Normal upload 2'
                }, upload_files=[(
                    'file', IMAGE_ROOT + GOOD_PNG)])

        response.follow()
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/submit/success/')
        assert util.TEMPLATE_TEST_CONTEXT.has_key(
            'mediagoblin/submit/success.html')

        # TODO: Test additional supported formats


    def test_malicious_uploads(self):
        # Test non-suppoerted file with non-supported extension
        # -----------------------------------------------------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Malicious Upload 2'
                }, upload_files=[(
                    'file', IMAGE_ROOT + EVIL_FILE)])

        context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.file.errors == ['The file doesn\'t seem to be an image!']

        # Test non-supported file with .jpg extension
        # -------------------------------------------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Malicious Upload 2'
                }, upload_files=[(
                    'file', IMAGE_ROOT + EVIL_JPG)])

        context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.file.errors == ['The file doesn\'t seem to be an image!']

        # Test non-supported file with .png extension
        # -------------------------------------------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Malicious Upload 3'
                }, upload_files=[(
                    'file', IMAGE_ROOT + EVIL_PNG)])

        context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.file.errors == ['The file doesn\'t seem to be an image!']

