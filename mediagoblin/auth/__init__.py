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
from mediagoblin.tools.pluginapi import hook_handle


def check_login(user, password):
    return hook_handle("auth_check_login", user, password)


def get_user(*args):
    return hook_handle("auth_get_user", *args)


def create_user(*args):
    return hook_handle("auth_create_user", *args)


def extra_validation(register_form, *args):
    return hook_handle("auth_extra_validation", register_form, *args)


def get_user_metadata(user):
    return hook_handle("auth_get_user_metadata", user)


def get_login_form(request):
    return hook_handle("auth_get_login_form", request)


def get_registration_form(request):
    return hook_handle("auth_get_registration_form", request)


def gen_password_hash(raw_pass, extra_salt=None):
    return hook_handle("auth_gen_password_hash", raw_pass, extra_salt)
