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
import mediagoblin.plugins.openid.forms as auth_forms


def get_register_form(request):
    # This function will check to see if persona plugin is enabled. If so,
    # this function will call hook_transform? and return a modified form
    # containing both openid & persona info.
    return auth_forms.RegistrationForm(request.form)


def get_login_form(request):
    # See register_form comment above
    return auth_forms.LoginForm(request.form)
