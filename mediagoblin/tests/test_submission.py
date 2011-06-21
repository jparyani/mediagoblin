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
from mediagoblin.tests.tools import setup_fresh_app
from mediagoblin import mg_globals
from mediagoblin import util

#TEST_JPG = ''

# TODO:
# - Define test files as globals
#   - supported mime types
#   - unsupported mime type with supported extension
# - Remove any imports that aren't neccessary
# - Get setup fixture working

class TestSubmission:
    def setUp(self):
        test_user = mg_globals.database.User()
        test_user['username'] = u'chris'
        test_user['email'] = u'chris@example.com'
        test_user['pw_hash'] = auth_lib.bcrypt_gen_password_hash('toast')
        test_user.save()

    @setup_fresh_app
    def test_something(test_app, self):
        pass
