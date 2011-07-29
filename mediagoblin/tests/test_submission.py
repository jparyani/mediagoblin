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
import pkg_resources

from nose.tools import assert_equal

from mediagoblin.auth import lib as auth_lib
from mediagoblin.tests.tools import setup_fresh_app, get_test_app
from mediagoblin import mg_globals
from mediagoblin import util

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
        # Test JPG
        # --------
        util.clear_test_template_context()
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
        assert util.TEMPLATE_TEST_CONTEXT.has_key(
            'mediagoblin/user_pages/user.html')

        # Test PNG
        # --------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Normal upload 2'
                }, upload_files=[(
                    'file', GOOD_PNG)])

        response.follow()
        assert_equal(
            urlparse.urlsplit(response.location)[2],
            '/u/chris/')
        assert util.TEMPLATE_TEST_CONTEXT.has_key(
            'mediagoblin/user_pages/user.html')


    def test_tags(self):
        # Good tag string
        # --------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Balanced Goblin',
                'tags': GOOD_TAG_STRING
                }, upload_files=[(
                    'file', GOOD_JPG)])

        # New media entry with correct tags should be created
        response.follow()
        context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/user_pages/user.html']
        request = context['request']
        media = request.db.MediaEntry.find({'title': 'Balanced Goblin'})[0]
        assert_equal(media['tags'],
                     [{'name': u'yin', 'slug': u'yin'},
                                            {'name': u'yang', 'slug': u'yang'}])

        # Test tags that are too long
        # ---------------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Balanced Goblin',
                'tags': BAD_TAG_STRING
                }, upload_files=[(
                    'file', GOOD_JPG)])

        # Too long error should be raised
        context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.tags.errors == [
            u'Tags must be shorter than 50 characters.  Tags that are too long'\
             ': ffffffffffffffffffffffffffuuuuuuuuuuuuuuuuuuuuuuuuuu']


    def test_malicious_uploads(self):
        # Test non-suppoerted file with non-supported extension
        # -----------------------------------------------------
        util.clear_test_template_context()
        response = self.test_app.post(
            '/submit/', {
                'title': 'Malicious Upload 2'
                }, upload_files=[(
                    'file', EVIL_FILE)])

        context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        form = context['submit_form']
        assert form.file.errors == ['The file doesn\'t seem to be an image!']

        # NOTE: The following 2 tests will fail. These can be uncommented
        #       after http://bugs.foocorp.net/issues/324 is resolved and
        #       bad files are handled properly.

        # Test non-supported file with .jpg extension
        # -------------------------------------------
        #util.clear_test_template_context()
        #response = self.test_app.post(
        #    '/submit/', {
        #        'title': 'Malicious Upload 2'
        #        }, upload_files=[(
        #            'file', EVIL_JPG)])

        #context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        #form = context['submit_form']
        #assert form.file.errors == ['The file doesn\'t seem to be an image!']

        # Test non-supported file with .png extension
        # -------------------------------------------
        #util.clear_test_template_context()
        #response = self.test_app.post(
        #    '/submit/', {
        #        'title': 'Malicious Upload 3'
        #        }, upload_files=[(
        #            'file', EVIL_PNG)])

        #context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/submit/start.html']
        #form = context['submit_form']
        #assert form.file.errors == ['The file doesn\'t seem to be an image!']

