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


from mediagoblin.auth import lib as auth_lib

from mediagoblin.tests.tools import get_test_app

from mediagoblin import globals as mgoblin_globals
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


def test_register_views():
    util.clear_test_template_context()
    test_app = get_test_app()

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
    assert not mgoblin_globals.database.User.find().count()

    # Successful register
    # -------------------
    ## Did we redirect to the proper page?  Use the right template?
    ## Make sure user is in place
    ## Make sure we get email confirmation
    ## Try logging in
    
    # Uniqueness checks
    # -----------------
    ## We shouldn't be able to register with that user twice

    ## Also check for double instances of an email address
