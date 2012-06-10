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

from routes.route import Route

from mediagoblin.tools import pluginapi
from mediagoblin.tools.response import render_to_response


PLUGIN_DIR = os.path.dirname(__file__)


_log = logging.getLogger(__name__)


def flatpage_handler(template):
    """Flatpage view generator

    Given a template, generates the controller function for handling that
    route.

    """
    def _flatpage_handler(request, *args, **kwargs):
        return render_to_response(
            request, 'flatpagesfile/%s' % template,
            {'args': args, 'kwargs': kwargs})
    return _flatpage_handler


class FlatpagesFilePlugin(pluginapi.Plugin):
    """
    This is the flatpages plugin class. See the README for how to use
    flatpages.
    """
    def setup_plugin(self):
        self.config = pluginapi.get_config('mediagoblin.plugins.flatpagesfile')

        _log.info('Setting up flatpagesfile....')

        # Register the template path.
        pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))

        # Set up and register routes.
        pages = [(int(key.replace('page', '')), val)
                 for key, val in self.config.items()
                 if key.startswith('page')]

        pages = [mapping for index, mapping in sorted(pages)]
        routes = []
        for name, url, template in pages:
            name = 'flatpagesfile.%s' % name.strip()
            controller = flatpage_handler(template)
            routes.append(
                Route(name, url, controller=controller))

        pluginapi.register_routes(routes)
        _log.info('Done setting up flatpagesfile!')
