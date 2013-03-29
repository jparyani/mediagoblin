# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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

import logging

from mediagoblin.tools import pluginapi
from mediagoblin.tools.session import SessionManager
from .tools import PWGSession

_log = logging.getLogger(__name__)


def setup_plugin():
    _log.info('Setting up piwigo...')

    routes = [
            ('mediagoblin.plugins.piwigo.wsphp',
             '/api/piwigo/ws.php',
             'mediagoblin.plugins.piwigo.views:ws_php'),
        ]

    pluginapi.register_routes(routes)

    PWGSession.session_manager = SessionManager("pwg_id", "plugins.piwigo")


hooks = {
    'setup': setup_plugin
}
