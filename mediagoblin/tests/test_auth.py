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

import urlparse

from nose.tools import assert_equal

from mediagoblin.auth import lib as auth_lib
from mediagoblin.tests.tools import setup_fresh_app
from mediagoblin import mg_globals
from mediagoblin import util


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
    assert util.TEMPLATE_TEST_CONTEXT.has_key(
        'mediagoblin/auth/register.html')

    # Try to register without providing anything, should error
    # --------------------------------------------------------

    util.clear_test_template_context()
    test_app.post(
        '/auth/register/', {})
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
    form = context['register_form']
    assert form.username.errors == [u'This field is required.']
    assert form.password.errors == [u'This field is required.']
    assert form.confirm_password.errors == [u'This field is required.']
    assert form.email.errors == [u'This field is required.']

    # Try to register with fields that are known to be invalid
    # --------------------------------------------------------

    ## too short
    util.clear_test_template_context()
    test_app.post(
        '/auth/register/', {
            'username': 'l',
            'password': 'o',
            'confirm_password': 'o',
            'email': 'l'})
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
    form = context['register_form']

    assert form.username.errors == [
        u'Field must be between 3 and 30 characters long.']
    assert form.password.errors == [
        u'Field must be between 6 and 30 characters long.']

    ## bad form
    util.clear_test_template_context()
    test_app.post(
        '/auth/register/', {
            'username': '@_@',
            'email': 'lollerskates'})
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
    form = context['register_form']

    assert form.username.errors == [
        u'Invalid input.']
    assert form.email.errors == [
        u'Invalid email address.']

    ## mismatching passwords
    util.clear_test_template_context()
    test_app.post(
        '/auth/register/', {
            'password': 'herpderp',
            'confirm_password': 'derpherp'})
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/register.html']
    form = context['register_form']

    assert form.password.errors == [
        u'Passwords must match.']

    ## At this point there should be no users in the database ;)
    assert not mg_globals.database.User.find().count()

    # Successful register
    # -------------------
    util.clear_test_template_context()
    response = test_app.post(
        '/auth/register/', {
            'username': 'happygirl',
            'password': 'iamsohappy',
            'confirm_password': 'iamsohappy',
            'email': 'happygrrl@example.org'})
    response.follow()

    ## Did we redirect to the proper page?  Use the right template?
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/u/happygirl/')
    assert util.TEMPLATE_TEST_CONTEXT.has_key(
        'mediagoblin/user_pages/user.html')

    ## Make sure user is in place
    new_user = mg_globals.database.User.find_one(
        {'username': 'happygirl'})
    assert new_user
    assert new_user['status'] == u'needs_email_verification'
    assert new_user['email_verified'] == False

    ## Make sure user is logged in
    request = util.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/user_pages/user.html']['request']
    assert request.session['user_id'] == unicode(new_user['_id'])

    ## Make sure we get email confirmation, and try verifying
    assert len(util.EMAIL_TEST_INBOX) == 1
    message = util.EMAIL_TEST_INBOX.pop()
    assert message['To'] == 'happygrrl@example.org'
    email_context = util.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/auth/verification_email.txt']
    assert email_context['verification_url'] in message.get_payload(decode=True)

    path = urlparse.urlsplit(email_context['verification_url'])[2]
    get_params = urlparse.urlsplit(email_context['verification_url'])[3]
    assert path == u'/auth/verify_email/'
    parsed_get_params = urlparse.parse_qs(get_params)

    ### user should have these same parameters
    assert parsed_get_params['userid'] == [
        unicode(new_user['_id'])]
    assert parsed_get_params['token'] == [
        new_user['verification_key']]

    ## Try verifying with bs verification key, shouldn't work
    util.clear_test_template_context()
    response = test_app.get(
        "/auth/verify_email/?userid=%s&token=total_bs" % unicode(
            new_user['_id']))
    response.follow()
    context = util.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/user_pages/user.html']
    # assert context['verification_successful'] == True
    # TODO: Would be good to test messages here when we can do so...
    new_user = mg_globals.database.User.find_one(
        {'username': 'happygirl'})
    assert new_user
    assert new_user['status'] == u'needs_email_verification'
    assert new_user['email_verified'] == False

    ## Verify the email activation works
    util.clear_test_template_context()
    response = test_app.get("%s?%s" % (path, get_params))
    response.follow()
    context = util.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/user_pages/user.html']
    # assert context['verification_successful'] == True
    # TODO: Would be good to test messages here when we can do so...
    new_user = mg_globals.database.User.find_one(
        {'username': 'happygirl'})
    assert new_user
    assert new_user['status'] == u'active'
    assert new_user['email_verified'] == True

    # Uniqueness checks
    # -----------------
    ## We shouldn't be able to register with that user twice
    util.clear_test_template_context()
    response = test_app.post(
        '/auth/register/', {
            'username': 'happygirl',
            'password': 'iamsohappy2',
            'confirm_password': 'iamsohappy2',
            'email': 'happygrrl2@example.org'})

    context = util.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/auth/register.html']
    form = context['register_form']
    assert form.username.errors == [
        u'Sorry, a user with that name already exists.']

    ## TODO: Also check for double instances of an email address?


@setup_fresh_app
def test_authentication_views(test_app):
    """
    Test logging in and logging out
    """
    # Make a new user
    test_user = mg_globals.database.User()
    test_user['username'] = u'chris'
    test_user['email'] = u'chris@example.com'
    test_user['pw_hash'] = auth_lib.bcrypt_gen_password_hash('toast')
    test_user.save()

    # Get login
    # ---------
    test_app.get('/auth/login/')
    assert util.TEMPLATE_TEST_CONTEXT.has_key(
        'mediagoblin/auth/login.html')

    # Failed login - blank form
    # -------------------------
    util.clear_test_template_context()
    response = test_app.post('/auth/login/')
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    form = context['login_form']
    assert form.username.errors == [u'This field is required.']
    assert form.password.errors == [u'This field is required.']

    # Failed login - blank user
    # -------------------------
    util.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'password': u'toast'})
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    form = context['login_form']
    assert form.username.errors == [u'This field is required.']

    # Failed login - blank password
    # -----------------------------
    util.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'chris'})
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    form = context['login_form']
    assert form.password.errors == [u'This field is required.']

    # Failed login - bad user
    # -----------------------
    util.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'steve',
            'password': 'toast'})
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    assert context['login_failed']

    # Failed login - bad password
    # ---------------------------
    util.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'chris',
            'password': 'jam'})
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/auth/login.html']
    assert context['login_failed']

    # Successful login
    # ----------------
    util.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'chris',
            'password': 'toast'})

    # User should be redirected
    response.follow()
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/')
    assert util.TEMPLATE_TEST_CONTEXT.has_key(
        'mediagoblin/root.html')

    # Make sure user is in the session
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/root.html']
    session = context['request'].session
    assert session['user_id'] == unicode(test_user['_id'])

    # Successful logout
    # -----------------
    util.clear_test_template_context()
    response = test_app.get('/auth/logout/')

    # Should be redirected to index page
    response.follow()
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/')
    assert util.TEMPLATE_TEST_CONTEXT.has_key(
        'mediagoblin/root.html')

    # Make sure the user is not in the session
    context = util.TEMPLATE_TEST_CONTEXT['mediagoblin/root.html']
    session = context['request'].session
    assert session.has_key('user_id') == False

    # User is redirected to custom URL if POST['next'] is set
    # -------------------------------------------------------
    util.clear_test_template_context()
    response = test_app.post(
        '/auth/login/', {
            'username': u'chris',
            'password': 'toast',
            'next' : '/u/chris/'})
    assert_equal(
        urlparse.urlsplit(response.location)[2],
        '/u/chris/')

