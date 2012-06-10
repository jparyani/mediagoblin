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

import logging
import os

from mediagoblin.tools import pluginapi


PLUGIN_DIR = os.path.dirname(__file__)


_log = logging.getLogger(__name__)


class FlatpagesPlugin(pluginapi.Plugin):
    """
    This is the flatpages plugin class. See the README for how to use
    flatpages.
    """
    def __init__(self):
        self._setup_plugin_called = 0

    def setup_plugin(self):
        self.config = pluginapi.get_config('mediagoblin.plugins.flatpagesfile')

        _log.info('Setting up flatpages....')
        pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))
