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
import pkg_resources
import pytest

from mediagoblin.plugins.basic_auth import lib as auth_lib
from mediagoblin import mg_globals
from mediagoblin.tools import template, mail
from mediagoblin.tests.tools import get_app, fixture_add_user
from mediagoblin.tools.testing import _activate_testing

_activate_testing()


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


@pytest.fixture()
def context_modified_app(request):
    return get_app(
        request,
        mgoblin_config=pkg_resources.resource_filename(
            'mediagoblin.tests', 'basic_auth_appconfig.ini'))


def test_fp_view(context_modified_app):
    ### Oops, forgot the password
    # -------------------
    ## Register a user
    fixture_add_user(active_user=True)

    template.clear_test_template_context()
    response = context_modified_app.post(
        '/auth/forgot_password/',
        {'username': u'chris'})
    response.follow()

    ## Did we redirect to the proper page?  Use the right template?
    assert urlparse.urlsplit(response.location)[2] == '/auth/login/'
    assert 'mediagoblin/auth/login.html' in template.TEMPLATE_TEST_CONTEXT

    ## Make sure link to change password is sent by email
    assert len(mail.EMAIL_TEST_INBOX) == 1
    message = mail.EMAIL_TEST_INBOX.pop()
    assert message['To'] == 'chris@example.com'
    email_context = template.TEMPLATE_TEST_CONTEXT[
        'mediagoblin/auth/fp_verification_email.txt']
    #TODO - change the name of verification_url to something
    # forgot-password-ish
    assert email_context['verification_url'] in \
        message.get_payload(decode=True)

    path = urlparse.urlsplit(email_context['verification_url'])[2]
    get_params = urlparse.urlsplit(email_context['verification_url'])[3]
    assert path == u'/auth/forgot_password/verify/'
    parsed_get_params = urlparse.parse_qs(get_params)

    # user should have matching parameters
    new_user = mg_globals.database.User.find_one({'username': u'chris'})
    assert parsed_get_params['userid'] == [unicode(new_user.id)]
    assert parsed_get_params['token'] == [new_user.fp_verification_key]

    ### The forgotten password token should be set to expire in ~ 10 days
    # A few ticks have expired so there are only 9 full days left...
    assert (new_user.fp_token_expire - datetime.datetime.now()).days == 9

    ## Try using a bs password-changing verification key, shouldn't work
    template.clear_test_template_context()
    response = context_modified_app.get(
        "/auth/forgot_password/verify/?userid=%s&token=total_bs" % unicode(
            new_user.id), status=404)
    assert response.status.split()[0] == u'404'  # status="404 NOT FOUND"

    ## Try using an expired token to change password, shouldn't work
    template.clear_test_template_context()
    new_user = mg_globals.database.User.find_one({'username': u'chris'})
    real_token_expiration = new_user.fp_token_expire
    new_user.fp_token_expire = datetime.datetime.now()
    new_user.save()
    response = context_modified_app.get("%s?%s" % (path, get_params),
                                        status=404)
    assert response.status.split()[0] == u'404'  # status="404 NOT FOUND"
    new_user.fp_token_expire = real_token_expiration
    new_user.save()

    ## Verify step 1 of password-change works -- can see form to
    ## change password
    template.clear_test_template_context()
    response = context_modified_app.get("%s?%s" % (path, get_params))
    assert 'mediagoblin/plugins/basic_auth/change_fp.html' \
            in template.TEMPLATE_TEST_CONTEXT

    ## Verify step 2.1 of password-change works -- report success to user
    template.clear_test_template_context()
    response = context_modified_app.post(
        '/auth/forgot_password/verify/', {
            'userid': parsed_get_params['userid'],
            'password': 'iamveryveryhappy',
            'token': parsed_get_params['token']})
    response.follow()
    assert 'mediagoblin/auth/login.html' in template.TEMPLATE_TEST_CONTEXT

    ## Verify step 2.2 of password-change works -- login w/ new password
    ## success
    template.clear_test_template_context()
    response = context_modified_app.post(
        '/auth/login/', {
            'username': u'chris',
            'password': 'iamveryveryhappy'})

    # User should be redirected
    response.follow()
    assert urlparse.urlsplit(response.location)[2] == '/'
    assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT
