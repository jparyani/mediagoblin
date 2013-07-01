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

from mediagoblin.auth.tools import create_basic_user
from mediagoblin.plugins.ldap.tools import LDAP
from mediagoblin.plugins.ldap import forms
from mediagoblin.tools import pluginapi


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.plugins.ldap')

    routes = [
        ('mediagoblin.plugins.ldap.register',
         '/auth/ldap/register/',
         'mediagoblin.plugins.ldap.views:register')]
    pluginapi.register_routes(routes)


def check_login_simple(username, password, request):
    l = LDAP(request)
    return l.login(username, password)


def create_user(register_form):
    user = create_basic_user(register_form)
    return user


def get_login_form(request):
    return forms.LoginForm(request.form)


def auth():
    return True


def append_to_global_context(context):
    context['pass_auth'] = True
    return context

hooks = {
    'setup': setup_plugin,
    'authentication': auth,
    'auth_check_login_simple': check_login_simple,
    'auth_create_user': create_user,
    'template_global_context': append_to_global_context,
    'auth_get_login_form': get_login_form,
}
