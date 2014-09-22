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

import pkg_resources
import pytest
import six
try:
    import mock
except ImportError:
    import unittest.mock as mock

import six.moves.urllib.parse as urlparse

from mediagoblin import mg_globals
from mediagoblin.db.base import Session
from mediagoblin.tests.tools import get_app
from mediagoblin.tools import template

pytest.importorskip("ldap")


@pytest.fixture()
def ldap_plugin_app(request):
    return get_app(
        request,
        mgoblin_config=pkg_resources.resource_filename(
            'mediagoblin.tests.auth_configs',
            'ldap_appconfig.ini'))


def return_value():
    return u'chris', u'chris@example.com'


def test_ldap_plugin(ldap_plugin_app):
    res = ldap_plugin_app.get('/auth/login/')

    assert urlparse.urlsplit(res.location)[2] == '/auth/ldap/login/'

    res = ldap_plugin_app.get('/auth/register/')

    assert urlparse.urlsplit(res.location)[2] == '/auth/ldap/register/'

    res = ldap_plugin_app.get('/auth/ldap/register/')

    assert urlparse.urlsplit(res.location)[2] == '/auth/ldap/login/'

    template.clear_test_template_context()
    res = ldap_plugin_app.post(
        '/auth/ldap/login/', {})

    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    form = context['login_form']
    assert form.username.errors == [u'This field is required.']
    assert form.password.errors == [u'This field is required.']

    @mock.patch('mediagoblin.plugins.ldap.tools.LDAP.login',
                mock.Mock(return_value=return_value()))
    def _test_authentication():
        template.clear_test_template_context()
        res = ldap_plugin_app.post(
            '/auth/ldap/login/',
            {'username': u'chris',
             'password': u'toast'})

        context = template.TEMPLATE_TEST_CONTEXT[
            'mediagoblin/auth/register.html']
        register_form = context['register_form']

        assert register_form.username.data == u'chris'
        assert register_form.email.data == u'chris@example.com'

        template.clear_test_template_context()
        res = ldap_plugin_app.post(
            '/auth/ldap/register/',
            {'username': u'chris',
             'email': u'chris@example.com'})
        res.follow()

        assert urlparse.urlsplit(res.location)[2] == '/u/chris/'
        assert 'mediagoblin/user_pages/user_nonactive.html' in \
            template.TEMPLATE_TEST_CONTEXT

        # Try to register with same email and username
        template.clear_test_template_context()
        res = ldap_plugin_app.post(
            '/auth/ldap/register/',
            {'username': u'chris',
             'email': u'chris@example.com'})

        context = template.TEMPLATE_TEST_CONTEXT[
            'mediagoblin/auth/register.html']
        register_form = context['register_form']

        assert register_form.email.errors == [
            u'Sorry, a user with that email address already exists.']
        assert register_form.username.errors == [
            u'Sorry, a user with that name already exists.']

        # Log out
        ldap_plugin_app.get('/auth/logout/')

        # Get user and detach from session
        test_user = mg_globals.database.User.query.filter_by(
            username=u'chris').first()
        Session.expunge(test_user)

        # Log back in
        template.clear_test_template_context()
        res = ldap_plugin_app.post(
            '/auth/ldap/login/',
            {'username': u'chris',
             'password': u'toast'})
        res.follow()

        assert urlparse.urlsplit(res.location)[2] == '/'
        assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT

        # Make sure user is in the session
        context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/root.html']
        session = context['request'].session
        assert session['user_id'] == six.text_type(test_user.id)

    _test_authentication()
