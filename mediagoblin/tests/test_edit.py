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

from mediagoblin import mg_globals
from mediagoblin.tests.tools import setup_fresh_app, fixture_add_user
from mediagoblin.tools import template
from mediagoblin.auth.lib import bcrypt_check_password


@setup_fresh_app
def test_change_password(test_app):
    """Test changing password correctly and incorrectly"""
    # set up new user
    test_user = fixture_add_user()

    test_app.post(
        '/auth/login/', {
            'username': u'chris',
            'password': 'toast'})

    # test that the password can be changed
    # template.clear_test_template_context()
    test_app.post(
        '/edit/profile/', {
            'bio': u'',
            'url': u'',
            'old_password': 'toast',
            'new_password': '123456',
            'confirm_password': '123456'})

    # test_user has to be fetched again in order to have the current values
    test_user = mg_globals.database.User.one({'username': 'chris'})

    assert bcrypt_check_password('123456', test_user['pw_hash'])

    # test that the password cannot be changed if the given old_password
    # is wrong
    # template.clear_test_template_context()
    test_app.post(
        '/edit/profile/', {
            'bio': u'',
            'url': u'',
            'old_password': 'toast',
            'new_password': '098765',
            'confirm_password': '098765'})

    test_user = mg_globals.database.User.one({'username': 'chris'})

    assert not bcrypt_check_password('098765', test_user['pw_hash'])


@setup_fresh_app
def change_bio_url(test_app):
    """Test changing bio and URL"""
    # set up new user
    test_user = fixture_add_user()

    # test changing the bio and the URL properly
    test_app.post(
        '/edit/profile/', {
            'bio': u'I love toast!',
            'url': u'http://dustycloud.org/'})

    test_user = mg_globals.database.User.one({'username': 'chris'})

    assert test_user['bio'] == u'I love toast!'
    assert test_user['url'] == u'http://dustycloud.org/'

    # test changing the bio and the URL inproperly
    too_long_bio = 150 * 'T' + 150 * 'o' + 150 * 'a' + 150 * 's' + 150* 't'

    test_app.post(
        '/edit/profile/', {
            # more than 500 characters
            'bio': too_long_bio,
            'url': 'this-is-no-url'})

    test_user = mg_globals.database.User.one({'username': 'chris'})

    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/edit/edit_profile.html']
    form = context['edit_profile_form']

    assert form.bio.errors == [u'Field must be between 0 and 500 characters long.']
    assert form.url.errors == [u'Improperly formed URL']

    # test changing the url inproperly
