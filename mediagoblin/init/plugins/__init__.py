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
import sys

from mediagoblin import mg_globals
from mediagoblin.tools import pluginapi


_log = logging.getLogger(__name__)


def setup_plugins():
    """This loads, configures and registers plugins

    See plugin documentation for more details.
    """

    global_config = mg_globals.global_config
    plugin_section = global_config.get('plugins', {})

    if not plugin_section:
        _log.info("No plugins to load")
        return

    pman = pluginapi.PluginManager()

    # Go through and import all the modules that are subsections of
    # the [plugins] section and read in the hooks.
    for plugin_module, config in plugin_section.items():
        # Skip any modules that start with -. This makes it easier for
        # someone to tweak their configuration so as to not load a
        # plugin without having to remove swaths of plugin
        # configuration.
        if plugin_module.startswith('-'):
            continue

        _log.info("Importing plugin module: %s" % plugin_module)
        pman.register_plugin(plugin_module)
        # If this throws errors, that's ok--it'll halt mediagoblin
        # startup.
        __import__(plugin_module)
        plugin = sys.modules[plugin_module]
        if hasattr(plugin, 'hooks'):
            pman.register_hooks(plugin.hooks)

    # Execute anything registered to the setup hook.
    pluginapi.callable_runall('setup')
