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

pytest.importorskip("requests")

from mediagoblin import mg_globals
from mediagoblin.db.base import Session
from mediagoblin.db.models import Privilege
from mediagoblin.tests.tools import get_app
from mediagoblin.tools import template


# App with plugin enabled
@pytest.fixture()
def persona_plugin_app(request):
    return get_app(
        request,
        mgoblin_config=pkg_resources.resource_filename(
            'mediagoblin.tests.auth_configs',
            'persona_appconfig.ini'))


class TestPersonaPlugin(object):
    def test_authentication_views(self, persona_plugin_app):
        res = persona_plugin_app.get('/auth/login/')

        assert urlparse.urlsplit(res.location)[2] == '/'

        res = persona_plugin_app.get('/auth/register/')

        assert urlparse.urlsplit(res.location)[2] == '/'

        res = persona_plugin_app.get('/auth/persona/login/')

        assert urlparse.urlsplit(res.location)[2] == '/auth/login/'

        res = persona_plugin_app.get('/auth/persona/register/')

        assert urlparse.urlsplit(res.location)[2] == '/auth/login/'

        @mock.patch('mediagoblin.plugins.persona.views._get_response', mock.Mock(return_value=u'test@example.com'))
        def _test_registration():
            # No register users
            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/auth/persona/login/', {})

            assert 'mediagoblin/auth/register.html' in template.TEMPLATE_TEST_CONTEXT
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
            register_form = context['register_form']

            assert register_form.email.data == u'test@example.com'
            assert register_form.persona_email.data == u'test@example.com'

            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/auth/persona/register/', {})

            assert 'mediagoblin/auth/register.html' in template.TEMPLATE_TEST_CONTEXT
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
            register_form = context['register_form']

            assert register_form.username.errors == [u'This field is required.']
            assert register_form.email.errors == [u'This field is required.']
            assert register_form.persona_email.errors == [u'This field is required.']

            # Successful register
            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/auth/persona/register/',
                {'username': 'chris',
                 'email': 'chris@example.com',
                 'persona_email': 'test@example.com'})
            res.follow()

            assert urlparse.urlsplit(res.location)[2] == '/u/chris/'
            assert 'mediagoblin/user_pages/user_nonactive.html' in template.TEMPLATE_TEST_CONTEXT

            # Try to register same Persona email address
            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/auth/persona/register/',
                {'username': 'chris1',
                 'email': 'chris1@example.com',
                 'persona_email': 'test@example.com'})

            assert 'mediagoblin/auth/register.html' in template.TEMPLATE_TEST_CONTEXT
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
            register_form = context['register_form']

            assert register_form.persona_email.errors == [u'Sorry, an account is already registered to that Persona email.']

            # Logout
            persona_plugin_app.get('/auth/logout/')

            # Get user and detach from session
            test_user = mg_globals.database.User.query.filter_by(
                username=u'chris').first()
            active_privilege = Privilege.query.filter(
                Privilege.privilege_name==u'active').first()
            test_user.all_privileges.append(active_privilege)
            test_user.save()
            test_user = mg_globals.database.User.query.filter_by(
                username=u'chris').first()
            Session.expunge(test_user)

            # Add another user for _test_edit_persona
            persona_plugin_app.post(
                '/auth/persona/register/',
                {'username': 'chris1',
                 'email': 'chris1@example.com',
                 'persona_email': 'test1@example.com'})

            # Log back in
            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/auth/persona/login/')
            res.follow()

            assert urlparse.urlsplit(res.location)[2] == '/'
            assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT

            # Make sure user is in the session
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/root.html']
            session = context['request'].session
            assert session['user_id'] == unicode(test_user.id)

        _test_registration()

        @mock.patch('mediagoblin.plugins.persona.views._get_response', mock.Mock(return_value=u'new@example.com'))
        def _test_edit_persona():
            # Try and delete only Persona email address
            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/edit/persona/',
                {'email': 'test@example.com'})

            assert 'mediagoblin/plugins/persona/edit.html' in template.TEMPLATE_TEST_CONTEXT
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/persona/edit.html']
            form = context['form']

            assert form.email.errors == [u"You can't delete your only Persona email address unless you have a password set."]

            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/edit/persona/', {})

            assert 'mediagoblin/plugins/persona/edit.html' in template.TEMPLATE_TEST_CONTEXT
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/persona/edit.html']
            form = context['form']

            assert form.email.errors == [u'This field is required.']

            # Try and delete Persona not owned by the user
            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/edit/persona/',
                {'email': 'test1@example.com'})

            assert 'mediagoblin/plugins/persona/edit.html' in template.TEMPLATE_TEST_CONTEXT
            context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/plugins/persona/edit.html']
            form = context['form']

            assert form.email.errors == [u'That Persona email address is not registered to this account.']

            res = persona_plugin_app.get('/edit/persona/add/')

            assert urlparse.urlsplit(res.location)[2] == '/edit/persona/'

            # Add Persona email address
            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/edit/persona/add/')
            res.follow()

            assert urlparse.urlsplit(res.location)[2] == '/edit/account/'

            # Delete a Persona
            res = persona_plugin_app.post(
                '/edit/persona/',
                {'email': 'test@example.com'})
            res.follow()

            assert urlparse.urlsplit(res.location)[2] == '/edit/account/'

        _test_edit_persona()

        @mock.patch('mediagoblin.plugins.persona.views._get_response', mock.Mock(return_value=u'test1@example.com'))
        def _test_add_existing():
            template.clear_test_template_context()
            res = persona_plugin_app.post(
                '/edit/persona/add/')
            res.follow()

            assert urlparse.urlsplit(res.location)[2] == '/edit/persona/'

        _test_add_existing()
