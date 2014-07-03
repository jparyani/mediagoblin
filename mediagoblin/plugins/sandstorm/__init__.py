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
import os

from mediagoblin.tools import pluginapi

PLUGIN_DIR = os.path.dirname(__file__)


def setup_plugin():
    # config = pluginapi.get_config('mediagoblin.plugins.sandstorm')

    routes = [
        ('mediagoblin.plugins.ldap.register',
         '/auth/ldap/register/',
         'mediagoblin.plugins.ldap.views:register'),
        ('mediagoblin.plugins.sandstorm.login',
         '/auth/sandstorm/login/',
         'mediagoblin.plugins.sandstorm.views:login')]

    pluginapi.register_routes(routes)


def no_pass_redirect():
    return 'sandstorm'


def auth():
    return True

hooks = {
    'setup': setup_plugin,
    'authentication': auth,
    'auth_no_pass_redirect': no_pass_redirect
}
