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

import six
from werkzeug.routing import Map, Rule
from mediagoblin.tools.common import import_component


_log = logging.getLogger(__name__)

url_map = Map()


class MGRoute(Rule):
    def __init__(self, endpoint, url, controller):
        Rule.__init__(self, url, endpoint=endpoint)
        self.gmg_controller = controller

    def empty(self):
        new_rule = Rule.empty(self)
        new_rule.gmg_controller = self.gmg_controller
        return new_rule


def endpoint_to_controller(rule):
    endpoint = rule.endpoint
    view_func = rule.gmg_controller

    _log.debug('endpoint: {0} view_func: {1}'.format(endpoint, view_func))

    # import the endpoint, or if it's already a callable, call that
    if isinstance(view_func, six.string_types):
        view_func = import_component(view_func)
        rule.gmg_controller = view_func

    return view_func


def add_route(endpoint, url, controller):
    """
    Add a route to the url mapping
    """
    url_map.add(MGRoute(endpoint, url, controller))


def mount(mountpoint, routes):
    """
    Mount a bunch of routes to this mountpoint
    """
    for endpoint, url, controller in routes:
        url = "%s/%s" % (mountpoint.rstrip('/'), url.lstrip('/'))
        add_route(endpoint, url, controller)
