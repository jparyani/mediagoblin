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
from mediagoblin.tools.pluginapi import Plugin, get_config


_log = logging.getLogger(__name__)


class SamplePlugin(Plugin):
    """
    This is a sample plugin class. It automatically registers itself
    with mediagoblin when this module is imported.

    The setup_plugin method prints configuration for this plugin if
    it exists.
    """
    def __init__(self):
        self._setup_plugin_called = 0

    def setup_plugin(self):
        _log.info('Sample plugin set up!')
        config = get_config('mediagoblin.plugins.sampleplugin')
        if config:
            _log.info('%r' % config)
        else:
            _log.info('There is no configuration set.')
        self._setup_plugin_called += 1
