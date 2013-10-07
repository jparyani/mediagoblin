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
import pytest
import mock

openid_consumer = pytest.importorskip(
    "openid.consumer.consumer")

from mediagoblin import mg_globals
from mediagoblin.db.base import Session
from mediagoblin.db.models import User
from mediagoblin.plugins.openid.models import OpenIDUserURL
from mediagoblin.tests.tools import get_app, fixture_add_user
from mediagoblin.tools import template


# App with plugin enabled
@pytest.fixture()
def openid_plugin_app(request):
    return get_app(
        request,
        mgoblin_config=pkg_resources.resource_filename(
            'mediagoblin.tests.auth_configs',
            'openid_appconfig.ini'))


class TestOpenIDPlugin(object):
    def _setup(self, openid_plugin_app, value=True, edit=False, delete=False):
        if value:
            response = openid_consumer.SuccessResponse(mock.Mock(), mock.Mock())
            if edit or delete:
                response.identity_url = u'http://add.myopenid.com'
            else:
                response.identity_url = u'http://real.myopenid.com'
            self._finish_verification = mock.Mock(return_value=response)
        else:
            self._finish_verification = mock.Mock(return_value=False)

        @mock.patch('mediagoblin.plugins.openid.views._response_email', mock.Mock(return_value=None))
        @mock.patch('mediagoblin.plugins.openid.views._response_nickname', mock.Mock(return_value=None))
        @mock.patch('mediagoblin.plugins.openid.views._finish_verification', self._finish_verification)
        def _setup_start(self, openid_plugin_app, edit, delete):
            if edit:
                self._start_verification = mock.Mock(return_value=openid_plugin_app.post(
                    '/edit/openid/finish/'))
            elif delete:
                self._start_verification = mock.Mock(return_value=openid_plugin_app.post(
                    '/edit/openid/delete/finish/'))
            else:
                self._start_verification = mock.Mock(return_value=openid_plugin_app.post(
                    '/auth/openid/login/finish/'))
        _setup_start(self, openid_plugin_app, edit, delete)

    def test_bad_login(self, openid_plugin_app):
        """ Test that attempts to login with invalid paramaters"""

        # Test GET request for auth/register page
        res = openid_plugin_app.get('/auth/register/').follow()

        # Make sure it redirected to the correct place
        assert urlparse.urlsplit(res.location)[2] == '/auth/openid/login/'

        # Test GET request for auth/login page
        res = openid_plugin_app.get('/auth/login/')
        res.follow()

        # Correct redirect?
        assert urlparse.urlsplit(res.location)[2] == '/auth/openid/login/'

        # Test GET request for auth/openid/register page
        res = openid_plugin_app.get('/auth/openid/register/')
        res.follow()

        # Correct redirect?
        assert urlparse.urlsplit(res.location)[2] == '/auth/openid/login/'

        # Test GET request for auth/openid/login/finish page
        res = openid_plugin_app.get('/auth/openid/login/finish/')
        res.follow()

        # Correct redirect?
        assert urlparse.urlsplit(res.location)[2] == '/auth/openid/login/'

        # Test GET request for auth/openid/login page
        res = openid_plugin_app.get('/auth/openid/login/')

        # Correct place?
        assert 'mediagoblin/plugins/openid/login.html' in template.TEMPLATE_TEST_CONTEXT

        # Try to login with an empty form
        template.clear_test_template_context()
        openid_plugin_app.post(
            '/auth/openid/login/', {})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/openid/login.html']
        form = context['login_form']
        assert form.openid.errors == [u'This field is required.']

        # Try to login with wrong form values
        template.clear_test_template_context()
        openid_plugin_app.post(
            '/auth/openid/login/', {
                'openid': 'not_a_url.com'})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/openid/login.html']
        form = context['login_form']
        assert form.openid.errors == [u'Please enter a valid url.']

        # Should be no users in the db
        assert User.query.count() == 0

        # Phony OpenID URl
        template.clear_test_template_context()
        openid_plugin_app.post(
            '/auth/openid/login/', {
                'openid': 'http://phoney.myopenid.com/'})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/openid/login.html']
        form = context['login_form']
        assert form.openid.errors == [u'Sorry, the OpenID server could not be found']

    def test_login(self, openid_plugin_app):
        """Tests that test login and registion with openid"""
        # Test finish_login redirects correctly when response = False
        self._setup(openid_plugin_app, False)

        @mock.patch('mediagoblin.plugins.openid.views._finish_verification', self._finish_verification)
        @mock.patch('mediagoblin.plugins.openid.views._start_verification', self._start_verification)
        def _test_non_response():
            template.clear_test_template_context()
            res = openid_plugin_app.post(
                '/auth/openid/login/', {
                    'openid': 'http://phoney.myopenid.com/'})
            res.follow()

            # Correct Place?
            assert urlparse.urlsplit(res.location)[2] == '/auth/openid/login/'
            assert 'mediagoblin/plugins/openid/login.html' in template.TEMPLATE_TEST_CONTEXT
        _test_non_response()

        # Test login with new openid
        # Need to clear_test_template_context before calling _setup
        template.clear_test_template_context()
        self._setup(openid_plugin_app)

        @mock.patch('mediagoblin.plugins.openid.views._finish_verification', self._finish_verification)
        @mock.patch('mediagoblin.plugins.openid.views._start_verification', self._start_verification)
        def _test_new_user():
            openid_plugin_app.post(
                '/auth/openid/login/', {
                    'openid': u'http://real.myopenid.com'})

            # Right place?
            assert 'mediagoblin/auth/register.html' in template.TEMPLATE_TEST_CONTEXT
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
            register_form = context['register_form']

            # Register User
            res = openid_plugin_app.post(
                '/auth/openid/register/', {
                    'openid': register_form.openid.data,
                    'username': u'chris',
                    'email': u'chris@example.com'})
            res.follow()

            # Correct place?
            assert urlparse.urlsplit(res.location)[2] == '/u/chris/'
            assert 'mediagoblin/user_pages/user_nonactive.html' in template.TEMPLATE_TEST_CONTEXT

            # No need to test if user is in logged in and verification email
            # awaits, since openid uses the register_user function which is
            # tested in test_auth

            # Logout User
            openid_plugin_app.get('/auth/logout')

            # Get user and detach from session
            test_user = mg_globals.database.User.query.filter_by(
                username=u'chris').first()
            Session.expunge(test_user)

            # Log back in
            # Could not get it to work by 'POST'ing to /auth/openid/login/
            template.clear_test_template_context()
            res = openid_plugin_app.post(
                '/auth/openid/login/finish/', {
                    'openid': u'http://real.myopenid.com'})
            res.follow()

            assert urlparse.urlsplit(res.location)[2] == '/'
            assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT

            # Make sure user is in the session
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/root.html']
            session = context['request'].session
            assert session['user_id'] == unicode(test_user.id)

        _test_new_user()

        # Test register with empty form
        template.clear_test_template_context()
        openid_plugin_app.post(
            '/auth/openid/register/', {})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
        register_form = context['register_form']

        assert register_form.openid.errors == [u'This field is required.']
        assert register_form.email.errors == [u'This field is required.']
        assert register_form.username.errors == [u'This field is required.']

        # Try to register with existing username and email
        template.clear_test_template_context()
        openid_plugin_app.post(
            '/auth/openid/register/', {
                'openid': 'http://real.myopenid.com',
                'email': 'chris@example.com',
                'username': 'chris'})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
        register_form = context['register_form']

        assert register_form.username.errors == [u'Sorry, a user with that name already exists.']
        assert register_form.email.errors == [u'Sorry, a user with that email address already exists.']
        assert register_form.openid.errors == [u'Sorry, an account is already registered to that OpenID.']

    def test_add_delete(self, openid_plugin_app):
        """Test adding and deleting openids"""
        # Add user
        test_user = fixture_add_user(password='', privileges=[u'active'])
        openid = OpenIDUserURL()
        openid.openid_url = 'http://real.myopenid.com'
        openid.user_id = test_user.id
        openid.save()

        # Log user in
        template.clear_test_template_context()
        self._setup(openid_plugin_app)

        @mock.patch('mediagoblin.plugins.openid.views._finish_verification', self._finish_verification)
        @mock.patch('mediagoblin.plugins.openid.views._start_verification', self._start_verification)
        def _login_user():
            openid_plugin_app.post(
                '/auth/openid/login/finish/', {
                    'openid': u'http://real.myopenid.com'})

        _login_user()

        # Try and delete only OpenID url
        template.clear_test_template_context()
        res = openid_plugin_app.post(
            '/edit/openid/delete/', {
                'openid': 'http://real.myopenid.com'})
        assert 'mediagoblin/plugins/openid/delete.html' in template.TEMPLATE_TEST_CONTEXT

        # Add OpenID to user
        # Empty form
        template.clear_test_template_context()
        res = openid_plugin_app.post(
            '/edit/openid/', {})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/openid/add.html']
        form = context['form']
        assert form.openid.errors == [u'This field is required.']

        # Try with a bad url
        template.clear_test_template_context()
        openid_plugin_app.post(
            '/edit/openid/', {
                'openid': u'not_a_url.com'})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/openid/add.html']
        form = context['form']
        assert form.openid.errors == [u'Please enter a valid url.']

        # Try with a url that's already registered
        template.clear_test_template_context()
        openid_plugin_app.post(
            '/edit/openid/', {
                'openid': 'http://real.myopenid.com'})
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/openid/add.html']
        form = context['form']
        assert form.openid.errors == [u'Sorry, an account is already registered to that OpenID.']

        # Test adding openid to account
        # Need to clear_test_template_context before calling _setup
        template.clear_test_template_context()
        self._setup(openid_plugin_app, edit=True)

        # Need to remove openid_url from db because it was added at setup
        openid = OpenIDUserURL.query.filter_by(
            openid_url=u'http://add.myopenid.com')
        openid.delete()

        @mock.patch('mediagoblin.plugins.openid.views._finish_verification', self._finish_verification)
        @mock.patch('mediagoblin.plugins.openid.views._start_verification', self._start_verification)
        def _test_add():
            # Successful add
            template.clear_test_template_context()
            res = openid_plugin_app.post(
                '/edit/openid/', {
                    'openid': u'http://add.myopenid.com'})
            res.follow()

            # Correct place?
            assert urlparse.urlsplit(res.location)[2] == '/edit/account/'
            assert 'mediagoblin/edit/edit_account.html' in template.TEMPLATE_TEST_CONTEXT

            # OpenID Added?
            new_openid = mg_globals.database.OpenIDUserURL.query.filter_by(
                openid_url=u'http://add.myopenid.com').first()
            assert new_openid

        _test_add()

        # Test deleting openid from account
        # Need to clear_test_template_context before calling _setup
        template.clear_test_template_context()
        self._setup(openid_plugin_app, delete=True)

        # Need to add OpenID back to user because it was deleted during
        # patch
        openid = OpenIDUserURL()
        openid.openid_url = 'http://add.myopenid.com'
        openid.user_id = test_user.id
        openid.save()

        @mock.patch('mediagoblin.plugins.openid.views._finish_verification', self._finish_verification)
        @mock.patch('mediagoblin.plugins.openid.views._start_verification', self._start_verification)
        def _test_delete(self, test_user):
            # Delete openid from user
            # Create another user to test deleting OpenID that doesn't belong to them
            new_user = fixture_add_user(username='newman')
            openid = OpenIDUserURL()
            openid.openid_url = 'http://realfake.myopenid.com/'
            openid.user_id = new_user.id
            openid.save()

            # Try and delete OpenID url that isn't the users
            template.clear_test_template_context()
            res = openid_plugin_app.post(
                '/edit/openid/delete/', {
                    'openid': 'http://realfake.myopenid.com/'})
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/openid/delete.html']
            form = context['form']
            assert form.openid.errors == [u'That OpenID is not registered to this account.']

            # Delete OpenID
            # Kind of weird to POST to delete/finish
            template.clear_test_template_context()
            res = openid_plugin_app.post(
                '/edit/openid/delete/finish/', {
                    'openid': u'http://add.myopenid.com'})
            res.follow()

            # Correct place?
            assert urlparse.urlsplit(res.location)[2] == '/edit/account/'
            assert 'mediagoblin/edit/edit_account.html' in template.TEMPLATE_TEST_CONTEXT

            # OpenID deleted?
            new_openid = mg_globals.database.OpenIDUserURL.query.filter_by(
                openid_url=u'http://add.myopenid.com').first()
            assert not new_openid

        _test_delete(self, test_user)
