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
from pkg_resources import resource_filename

from mediagoblin.plugins.metadata_display.lib import add_rdfa_to_readable_to_media_home
from mediagoblin.tools import pluginapi
from mediagoblin.tools.staticdirect import PluginStatic

PLUGIN_DIR = os.path.dirname(__file__)

def setup_plugin():
    # Register the template path.
    pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))

    pluginapi.register_template_hooks(
        {"media_sideinfo": "mediagoblin/plugins/metadata_display/metadata_table.html",
         "head": "mediagoblin/plugins/metadata_display/bits/metadata_extra_head.html"})


hooks = {
    'setup': setup_plugin,
    'static_setup': lambda: PluginStatic(
        'metadata_display',
        resource_filename('mediagoblin.plugins.metadata_display', 'static')
     ),
    'media_home_context':add_rdfa_to_readable_to_media_home
    }
