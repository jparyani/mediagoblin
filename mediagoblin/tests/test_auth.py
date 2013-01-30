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
import datetime

from nose.tools import assert_equal

from mediagoblin import mg_globals
from mediagoblin.auth import lib as auth_lib
from mediagoblin.db.models import User
from mediagoblin.tests.tools import setup_fresh_app, get_app, fixture_add_user
from mediagoblin.tools import template, mail


########################
# Test bcrypt auth funcs
########################

def test_bcrypt_check_password():
    # Check known 'lollerskates' password against check function
    assert auth_lib.bcrypt_check_password(
        'lollerskates',
        '$2a$12$PXU03zfrVCujBhVeICTwtOaHTUs5FFwsscvSSTJkqx/2RQ0Lhy/nO')

    assert not auth_lib.bcrypt_check_password(
        'notthepassword',
        '$2a$12$PXU03zfrVCujBhVeICTwtOaHTUs5FFwsscvSSTJkqx/2RQ0Lhy/nO')

    # Same thing, but with extra fake salt.
    assert not auth_lib.bcrypt_check_password(
        'notthepassword',
        '$2a$12$ELVlnw3z1FMu6CEGs/L8XO8vl0BuWSlUHgh0rUrry9DUXGMUNWwl6',
        '3><7R45417')


def test_bcrypt_gen_password_hash():
    pw = 'youwillneverguessthis'

    # Normal password hash generation, and check on that hash
    hashed_pw = auth_lib.bcrypt_gen_password_hash(pw)
    assert auth_lib.bcrypt_check_password(
        pw, hashed_pw)
    assert not auth_lib.bcrypt_check_password(
        'notthepassword', hashed_pw)

    # Same thing, extra salt.
    hashed_pw = auth_lib.bcrypt_gen_password_hash(pw, '3><7R45417')
    assert auth_lib.bcrypt_check_password(
        pw, hashed_pw, '3><7R45417')
    assert not auth_lib.bcrypt_check_password(
        'notthepassword', hashed_pw, '3><7R45417')


@setup_fresh_app
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

    assert_equal (form.username.errors, [u'Field must be between 3 and 30 characters long.'])
    assert_equal (form.password.errors, [u'Field must be between 5 and 1024 characters long.'])

    ## bad form
    template.clear_test_template_context()
    test_app.post(
        '/auth/register/', {
            'username': '@_@',
            'email': 'lollerskates'})
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
    form = context['register_form']

    assert_equal (form.username.errors, [u'This field does not take email addresses.'])
    assert_equal (form.email.errors, [u'This field requires an email address.'])

    ## At this point there should be no users in the database ;)
    assert_equal(User.query.count(), 0)

    # Successful register
    # -------------------
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/register/', {
            'username': u'happygirl',
            'password': 'iamsohappy',
            'email': 'happygrrl@example.org'})
    response.follow()

    ## Did we redirect to the proper page?  Use the right template?
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/u/happygirl/')
    assert 'mediagoblin/user_pages/user.html' in template.TEMPLATE_TEST_CONTEXT

    ## Make sure user is in place
    new_user = mg_globals.database.User.find_one(
        {'username': u'happygirl'})
    assert new_user
    assert new_user.status == u'needs_email_verification'
    assert new_user.email_verified == False

    ## Make sure user is logged in
    request = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/user_pages/user.html']['request']
    assert request.session['user_id'] == unicode(new_user.id)

    ## Make sure we get email confirmation, and try verifying
    assert len(mail.EMAIL_TEST_INBOX) == 1
    message = mail.EMAIL_TEST_INBOX.pop()
    assert message['To'] == 'happygrrl@example.org'
    email_context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/auth/verification_email.txt']
    assert email_context['verification_url'] in message.get_payload(decode=True)

    path = urlparse.urlsplit(email_context['verification_url'])[2]
    get_params = urlparse.urlsplit(email_context['verification_url'])[3]
    assert path == u'/auth/verify_email/'
    parsed_get_params = urlparse.parse_qs(get_params)

    ### user should have these same parameters
    assert parsed_get_params['userid'] == [
        unicode(new_user.id)]
    assert parsed_get_params['token'] == [
        new_user.verification_key]

    ## Try verifying with bs verification key, shouldn't work
    template.clear_test_template_context()
    response = test_app.get(
        "/auth/verify_email/?userid=%s&token=total_bs" % unicode(
            new_user.id))
    response.follow()
    context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/user_pages/user.html']
    # assert context['verification_successful'] == True
    # TODO: Would be good to test messages here when we can do so...
    new_user = mg_globals.database.User.find_one(
        {'username': u'happygirl'})
    assert new_user
    assert new_user.status == u'needs_email_verification'
    assert new_user.email_verified == False

    ## Verify the email activation works
    template.clear_test_template_context()
    response = test_app.get("%s?%s" % (path, get_params))
    response.follow()
    context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/user_pages/user.html']
    # assert context['verification_successful'] == True
    # TODO: Would be good to test messages here when we can do so...
    new_user = mg_globals.database.User.find_one(
        {'username': u'happygirl'})
    assert new_user
    assert new_user.status == u'active'
    assert new_user.email_verified == True

    # Uniqueness checks
    # -----------------
    ## We shouldn't be able to register with that user twice
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/register/', {
            'username': u'happygirl',
            'password': 'iamsohappy2',
            'email': 'happygrrl2@example.org'})

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
        {'username': u'happygirl'})
    response.follow()

    ## Did we redirect to the proper page?  Use the right template?
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/auth/login/')
    assert 'mediagoblin/auth/login.html' in template.TEMPLATE_TEST_CONTEXT

    ## Make sure link to change password is sent by email
    assert len(mail.EMAIL_TEST_INBOX) == 1
    message = mail.EMAIL_TEST_INBOX.pop()
    assert message['To'] == 'happygrrl@example.org'
    email_context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/auth/fp_verification_email.txt']
    #TODO - change the name of verification_url to something forgot-password-ish
    assert email_context['verification_url'] in message.get_payload(decode=True)

    path = urlparse.urlsplit(email_context['verification_url'])[2]
    get_params = urlparse.urlsplit(email_context['verification_url'])[3]
    assert path == u'/auth/forgot_password/verify/'
    parsed_get_params = urlparse.parse_qs(get_params)

    # user should have matching parameters
    new_user = mg_globals.database.User.find_one({'username': u'happygirl'})
    assert parsed_get_params['userid'] == [unicode(new_user.id)]
    assert parsed_get_params['token'] == [new_user.fp_verification_key]

    ### The forgotten password token should be set to expire in ~ 10 days
    # A few ticks have expired so there are only 9 full days left...
    assert (new_user.fp_token_expire - datetime.datetime.now()).days == 9

    ## Try using a bs password-changing verification key, shouldn't work
    template.clear_test_template_context()
    response = test_app.get(
        "/auth/forgot_password/verify/?userid=%s&token=total_bs" % unicode(
            new_user.id), status=404)
    assert_equal(response.status.split()[0], u'404') # status="404 NOT FOUND"

    ## Try using an expired token to change password, shouldn't work
    template.clear_test_template_context()
    new_user = mg_globals.database.User.find_one({'username': u'happygirl'})
    real_token_expiration = new_user.fp_token_expire
    new_user.fp_token_expire = datetime.datetime.now()
    new_user.save()
    response = test_app.get("%s?%s" % (path, get_params), status=404)
    assert_equal(response.status.split()[0], u'404') # status="404 NOT FOUND"
    new_user.fp_token_expire = real_token_expiration
    new_user.save()

    ## Verify step 1 of password-change works -- can see form to change password
    template.clear_test_template_context()
    response = test_app.get("%s?%s" % (path, get_params))
    assert 'mediagoblin/auth/change_fp.html' in template.TEMPLATE_TEST_CONTEXT

    ## Verify step 2.1 of password-change works -- report success to user
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/forgot_password/verify/', {
            'userid': parsed_get_params['userid'],
            'password': 'iamveryveryhappy',
            'token': parsed_get_params['token']})
    response.follow()
    assert 'mediagoblin/auth/login.html' in template.TEMPLATE_TEST_CONTEXT

    ## Verify step 2.2 of password-change works -- login w/ new password success
    template.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'happygirl',
            'password': 'iamveryveryhappy'})

    # User should be redirected
    response.follow()
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/')
    assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT


def test_authentication_views():
    """
    Test logging in and logging out
    """
    test_app = get_app(dump_old_app=False)
    # Make a new user
    test_user = fixture_add_user(active_user=False)

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
    assert form.password.errors == [u'This field is required.']

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
    context = template.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    form = context['login_form']
    assert form.password.errors == [u'This field is required.']

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
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/')
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
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/')
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
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/u/chris/')
