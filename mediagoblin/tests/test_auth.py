
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

from mediagoblin import mg_globals
from mediagoblin.db.models import User
from mediagoblin.tests.tools import get_app, fixture_add_user
from mediagoblin.tools import template, mail
from mediagoblin.auth import tools as auth_tools


def test_register_views(test_app):
    """
    Massive test function that all our registration-related views all work.
    """
    # Test doing a simple GET on the page
    # -----------------------------------

    test_app.get('/auth/register/')
    # Make sure it rendered with the appropriate template
    assert 'mediagoblin/auth/register.html' in template.TEMPLATE_TEST_CONTEXT

    # Try to register without providing anything, should error
    # --------------------------------------------------------

    template.clear_test_template_context()
    test_app.post(
        '/auth/register/', {})
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
    form = context['register_form']
    assert form.username.errors == [u'This field is required.']
    assert form.password.errors == [u'This field is required.']
    assert form.email.errors == [u'This field is required.']

    # Try to register with fields that are known to be invalid
    # --------------------------------------------------------

    ## too short
    template.clear_test_template_context()
    test_app.post(
        '/auth/register/', {
            'username': 'l',
            'password': 'o',
            'email': 'l'})
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
    form = context['register_form']

    assert form.username.errors == [u'Field must be between 3 and 30 characters long.']
    assert form.password.errors == [u'Field must be between 5 and 1024 characters long.']

    ## bad form
    template.clear_test_template_context()
    test_app.post(
        '/auth/register/', {
            'username': '@_@',
            'email': 'lollerskates'})
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
    form = context['register_form']

    assert form.username.errors == [u'This field does not take email addresses.']
    assert form.email.errors == [u'This field requires an email address.']

    ## At this point there should be no users in the database ;)
    assert User.query.count() == 0

    # Successful register
    # -------------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/register/', {
            'username': u'angrygirl',
            'password': 'iamsoangry',
            'email': 'angrygrrl@example.org'})
    response.follow()

    ## Did we redirect to the proper page?  Use the right template?
    assert urlparse.urlsplit(response.location)[2] == '/u/angrygirl/'
    assert 'mediagoblin/user_pages/user_nonactive.html' in template.TEMPLATE_TEST_CONTEXT

    ## Make sure user is in place
    new_user = mg_globals.database.User.query.filter_by(
        username=u'angrygirl').first()
    assert new_user

    ## Make sure that the proper privileges are granted on registration

    assert new_user.has_privilege(u'commenter')
    assert new_user.has_privilege(u'uploader')
    assert new_user.has_privilege(u'reporter')
    assert not new_user.has_privilege(u'active')
    ## Make sure user is logged in
    request = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/user_pages/user_nonactive.html']['request']
    assert request.session['user_id'] == unicode(new_user.id)

    ## Make sure we get email confirmation, and try verifying
    assert len(mail.EMAIL_TEST_INBOX) == 1
    message = mail.EMAIL_TEST_INBOX.pop()
    assert message['To'] == 'angrygrrl@example.org'
    email_context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/auth/verification_email.txt']
    assert email_context['verification_url'] in message.get_payload(decode=True)

    path = urlparse.urlsplit(email_context['verification_url'])[2]
    get_params = urlparse.urlsplit(email_context['verification_url'])[3]
    assert path == u'/auth/verify_email/'
    parsed_get_params = urlparse.parse_qs(get_params)

    ## Try verifying with bs verification key, shouldn't work
    template.clear_test_template_context()
    response = test_app.get(
        "/auth/verify_email/?token=total_bs")
    response.follow()

    # Correct redirect?
    assert urlparse.urlsplit(response.location)[2] == '/'

    # assert context['verification_successful'] == True
    # TODO: Would be good to test messages here when we can do so...
    new_user = mg_globals.database.User.query.filter_by(
        username=u'angrygirl').first()
    assert new_user

    ## Verify the email activation works
    template.clear_test_template_context()
    response = test_app.get("%s?%s" % (path, get_params))
    response.follow()
    context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/user_pages/user.html']
    # assert context['verification_successful'] == True
    # TODO: Would be good to test messages here when we can do so...
    new_user = mg_globals.database.User.query.filter_by(
        username=u'angrygirl').first()
    assert new_user

    # Uniqueness checks
    # -----------------
    ## We shouldn't be able to register with that user twice
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/register/', {
            'username': u'angrygirl',
            'password': 'iamsoangry2',
            'email': 'angrygrrl2@example.org'})

    context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/auth/register.html']
    form = context['register_form']
    assert form.username.errors == [
        u'Sorry, a user with that name already exists.']

    ## TODO: Also check for double instances of an email address?

    ### Oops, forgot the password
    # -------------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/forgot_password/',
        {'username': u'angrygirl'})
    response.follow()

    ## Did we redirect to the proper page?  Use the right template?
    assert urlparse.urlsplit(response.location)[2] == '/auth/login/'
    assert 'mediagoblin/auth/login.html' in template.TEMPLATE_TEST_CONTEXT

    ## Make sure link to change password is sent by email
    assert len(mail.EMAIL_TEST_INBOX) == 1
    message = mail.EMAIL_TEST_INBOX.pop()
    assert message['To'] == 'angrygrrl@example.org'
    email_context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/plugins/basic_auth/fp_verification_email.txt']
    #TODO - change the name of verification_url to something forgot-password-ish
    assert email_context['verification_url'] in message.get_payload(decode=True)

    path = urlparse.urlsplit(email_context['verification_url'])[2]
    get_params = urlparse.urlsplit(email_context['verification_url'])[3]
    parsed_get_params = urlparse.parse_qs(get_params)
    assert path == u'/auth/forgot_password/verify/'

    ## Try using a bs password-changing verification key, shouldn't work
    template.clear_test_template_context()
    response = test_app.get(
        "/auth/forgot_password/verify/?token=total_bs")
    response.follow()

    # Correct redirect?
    assert urlparse.urlsplit(response.location)[2] == '/'

    ## Verify step 1 of password-change works -- can see form to change password
    template.clear_test_template_context()
    response = test_app.get("%s?%s" % (path, get_params))
    assert 'mediagoblin/plugins/basic_auth/change_fp.html' in \
            template.TEMPLATE_TEST_CONTEXT

    ## Verify step 2.1 of password-change works -- report success to user
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/forgot_password/verify/', {
            'password': 'iamveryveryangry',
            'token': parsed_get_params['token']})
    response.follow()
    assert 'mediagoblin/auth/login.html' in template.TEMPLATE_TEST_CONTEXT

    ## Verify step 2.2 of password-change works -- login w/ new password success
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'angrygirl',
            'password': 'iamveryveryangry'})

    # User should be redirected
    response.follow()
    assert urlparse.urlsplit(response.location)[2] == '/'
    assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT


def test_authentication_views(test_app):
    """
    Test logging in and logging out
    """
    # Make a new user
    test_user = fixture_add_user()


    # Get login
    # ---------
    test_app.get('/auth/login/')
    assert 'mediagoblin/auth/login.html' in template.TEMPLATE_TEST_CONTEXT

    # Failed login - blank form
    # -------------------------
    template.clear_test_template_context()
    response = test_app.post('/auth/login/')
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    form = context['login_form']
    assert form.username.errors == [u'This field is required.']

    # Failed login - blank user
    # -------------------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'password': u'toast'})
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    form = context['login_form']
    assert form.username.errors == [u'This field is required.']

    # Failed login - blank password
    # -----------------------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'chris'})
    assert 'mediagoblin/auth/login.html' in template.TEMPLATE_TEST_CONTEXT

    # Failed login - bad user
    # -----------------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'steve',
            'password': 'toast'})
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    assert context['login_failed']

    # Failed login - bad password
    # ---------------------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'chris',
            'password': 'jam_and_ham'})
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    assert context['login_failed']

    # Successful login
    # ----------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'chris',
            'password': 'toast'})

    # User should be redirected
    response.follow()
    assert urlparse.urlsplit(response.location)[2] == '/'
    assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT

    # Make sure user is in the session
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/root.html']
    session = context['request'].session
    assert session['user_id'] == unicode(test_user.id)

    # Successful logout
    # -----------------
    template.clear_test_template_context()
    response = test_app.get('/auth/logout/')

    # Should be redirected to index page
    response.follow()
    assert urlparse.urlsplit(response.location)[2] == '/'
    assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT

    # Make sure the user is not in the session
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/root.html']
    session = context['request'].session
    assert 'user_id' not in session

    # User is redirected to custom URL if POST['next'] is set
    # -------------------------------------------------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'chris',
            'password': 'toast',
            'next' : '/u/chris/'})
    assert urlparse.urlsplit(response.location)[2] == '/u/chris/'

@pytest.fixture()
def authentication_disabled_app(request):
    return get_app(
        request,
        mgoblin_config=pkg_resources.resource_filename(
            'mediagoblin.tests.auth_configs',
            'authentication_disabled_appconfig.ini'))


def test_authentication_disabled_app(authentication_disabled_app):
    # app.auth should = false
    assert mg_globals
    assert mg_globals.app.auth is False

    # Try to visit register page
    template.clear_test_template_context()
    response = authentication_disabled_app.get('/auth/register/')
    response.follow()

    # Correct redirect?
    assert urlparse.urlsplit(response.location)[2] == '/'
    assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT

    # Try to vist login page
    template.clear_test_template_context()
    response = authentication_disabled_app.get('/auth/login/')
    response.follow()

    # Correct redirect?
    assert urlparse.urlsplit(response.location)[2] == '/'
    assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT

    ## Test check_login_simple should return None
    assert auth_tools.check_login_simple('test', 'simple') is None

    # Try to visit the forgot password page
    template.clear_test_template_context()
    response = authentication_disabled_app.get('/auth/register/')
    response.follow()

    # Correct redirect?
    assert urlparse.urlsplit(response.location)[2] == '/'
    assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT
