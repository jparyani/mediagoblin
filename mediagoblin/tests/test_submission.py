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

from nose.tools import assert_equal

from mediagoblin.auth import lib as auth_lib
from mediagoblin.tests.tools import setup_fresh_app, get_test_app
from mediagoblin import mg_globals
from mediagoblin import util

IMAGE_ROOT = 'mediagoblin/tests/test_submission'
GOOD_JPG = 'good.jpg'
GOOD_PNG = 'good.png'
EVIL_JPG = ''
EVIL_PNG = ''


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
        test_user['pw_hash'] = auth_lib.bcrypt_gen_password_hash('toast')
        test_user.save()

        self.test_app.post(
            '/auth/login/', {
                'username': u'chris',
                'password': 'toast'})

    def test_missing_fields(self):
        # Test missing title
        # Test missing description (if it's required)
        # Test missing file
        pass

    def test_normal_uploads(self):
        # FYI:
        # upload_files is for file uploads. It should be a list of
        # [(fieldname, filename, file_content)]. You can also use
        # just [(fieldname, filename)] and the file content will be
        # read from disk.

        # Test JPG
        # Test PNG
        # Test additional supported formats

        #resp = self.test_app.get('/')
        #print resp
        pass

    def test_malicious_uploads(self):
        # Test non-supported file with .jpg extension
        # Test non-supported file with .png extension
        pass

