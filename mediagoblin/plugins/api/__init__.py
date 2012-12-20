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
import logging

from mediagoblin.tools import pluginapi

_log = logging.getLogger(__name__)

PLUGIN_DIR = os.path.dirname(__file__)

config = pluginapi.get_config(__name__)

def setup_plugin():
    _log.info('Setting up API...')

    _log.debug('API config: {0}'.format(config))

    routes = [
        ('mediagoblin.plugins.api.test',
            '/api/test',
            'mediagoblin.plugins.api.views:api_test'),
        ('mediagoblin.plugins.api.entries',
            '/api/entries',
            'mediagoblin.plugins.api.views:get_entries'),
        ('mediagoblin.plugins.api.post_entry',
            '/api/submit',
            'mediagoblin.plugins.api.views:post_entry')]

    pluginapi.register_routes(routes)

hooks = {
    'setup': setup_plugin}
