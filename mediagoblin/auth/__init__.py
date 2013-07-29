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
from mediagoblin.tools.pluginapi import hook_handle, hook_runall


def get_user(**kwargs):
    """ Takes a kwarg such as username and returns a user object """
    return hook_handle("auth_get_user", **kwargs)


def create_user(register_form):
    results = hook_runall("auth_create_user", register_form)
    return results[0]


def extra_validation(register_form):
    from mediagoblin.auth.tools import basic_extra_validation

    extra_validation_passes = basic_extra_validation(register_form)
    if False in hook_runall("auth_extra_validation", register_form):
        extra_validation_passes = False
    return extra_validation_passes


def gen_password_hash(raw_pass, extra_salt=None):
    return hook_handle("auth_gen_password_hash", raw_pass, extra_salt)


def check_password(raw_pass, stored_hash, extra_salt=None):
    return hook_handle("auth_check_password",
                       raw_pass, stored_hash, extra_salt)
