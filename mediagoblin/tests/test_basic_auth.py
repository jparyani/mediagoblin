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
from mediagoblin.plugins.basic_auth import tools as auth_tools
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
