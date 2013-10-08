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

from mediagoblin.db.models import User
from mediagoblin.plugins.basic_auth import tools as auth_tools
from mediagoblin.tests.tools import fixture_add_user
from mediagoblin.tools import template
from mediagoblin.tools.testing import _activate_testing

_activate_testing()


########################
# Test bcrypt auth funcs
########################


def test_bcrypt_check_password():
    # Check known 'lollerskates' password against check function
    assert auth_tools.bcrypt_check_password(
        'lollerskates',
        '$2a$12$PXU03zfrVCujBhVeICTwtOaHTUs5FFwsscvSSTJkqx/2RQ0Lhy/nO')

    assert not auth_tools.bcrypt_check_password(
        'notthepassword',
        '$2a$12$PXU03zfrVCujBhVeICTwtOaHTUs5FFwsscvSSTJkqx/2RQ0Lhy/nO')

    # Same thing, but with extra fake salt.
    assert not auth_tools.bcrypt_check_password(
        'notthepassword',
        '$2a$12$ELVlnw3z1FMu6CEGs/L8XO8vl0BuWSlUHgh0rUrry9DUXGMUNWwl6',
        '3><7R45417')


def test_bcrypt_gen_password_hash():
    pw = 'youwillneverguessthis'

    # Normal password hash generation, and check on that hash
    hashed_pw = auth_tools.bcrypt_gen_password_hash(pw)
    assert auth_tools.bcrypt_check_password(
        pw, hashed_pw)
    assert not auth_tools.bcrypt_check_password(
        'notthepassword', hashed_pw)

    # Same thing, extra salt.
    hashed_pw = auth_tools.bcrypt_gen_password_hash(pw, '3><7R45417')
    assert auth_tools.bcrypt_check_password(
        pw, hashed_pw, '3><7R45417')
    assert not auth_tools.bcrypt_check_password(
        'notthepassword', hashed_pw, '3><7R45417')


def test_change_password(test_app):
        """Test changing password correctly and incorrectly"""
        test_user = fixture_add_user(
            password=u'toast',
            privileges=[u'active'])

        test_app.post(
            '/auth/login/', {
                'username': u'chris',
                'password': u'toast'})

        # test that the password can be changed
        res = test_app.post(
            '/edit/password/', {
                'old_password': 'toast',
                'new_password': '123456',
                })
        res.follow()

        # Did we redirect to the correct page?
        assert urlparse.urlsplit(res.location)[2] == '/edit/account/'

        # test_user has to be fetched again in order to have the current values
        test_user = User.query.filter_by(username=u'chris').first()
        assert auth_tools.bcrypt_check_password('123456', test_user.pw_hash)

        # test that the password cannot be changed if the given
        # old_password is wrong
        template.clear_test_template_context()
        test_app.post(
            '/edit/password/', {
                'old_password': 'toast',
                'new_password': '098765',
                })

        test_user = User.query.filter_by(username=u'chris').first()
        assert not auth_tools.bcrypt_check_password('098765', test_user.pw_hash)
