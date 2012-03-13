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

    pcache = pluginapi.PluginCache()

    # Go through and import all the modules that are subsections of
    # the [plugins] section.
    for plugin_module, config in plugin_section.items():
        _log.info("Importing plugin module: %s" % plugin_module)
        # If this throws errors, that's ok--it'll halt mediagoblin
        # startup.
        __import__(plugin_module)

    # Note: One side-effect of importing things is that anything that
    # subclassed pluginapi.Plugin is registered.

    # Go through all the plugin classes, instantiate them, and call
    # setup_plugin so they can figure things out.
    for plugin_class in pcache.plugin_classes:
        name = plugin_class.__module__ + "." + plugin_class.__name__
        _log.info("Loading plugin: %s" % name)
        plugin_obj = plugin_class()
        plugin_obj.setup_plugin()
        pcache.register_plugin_object(plugin_obj)
