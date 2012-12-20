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

import jinja2

from mediagoblin.tools import pluginapi
from mediagoblin.tools.response import render_to_response


PLUGIN_DIR = os.path.dirname(__file__)


_log = logging.getLogger(__name__)


@jinja2.contextfunction
def print_context(c):
    s = []
    for key, val in c.items():
        s.append('%s: %s' % (key, repr(val)))
    return '\n'.join(s)


def flatpage_handler_builder(template):
    """Flatpage view generator

    Given a template, generates the controller function for handling that
    route.

    """
    def _flatpage_handler_builder(request):
        return render_to_response(
            request, 'flatpagesfile/%s' % template,
            {'request': request})
    return _flatpage_handler_builder


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.plugins.flatpagesfile')

    _log.info('Setting up flatpagesfile....')

    # Register the template path.
    pluginapi.register_template_path(os.path.join(PLUGIN_DIR, 'templates'))

    pages = config.items()

    routes = []
    for name, (url, template) in pages:
        name = 'flatpagesfile.%s' % name.strip()
        controller = flatpage_handler_builder(template)
        routes.append(
            (name, url, controller))

    pluginapi.register_routes(routes)
    _log.info('Done setting up flatpagesfile!')


hooks = {
    'setup': setup_plugin
    }
