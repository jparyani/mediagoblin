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

from werkzeug.routing import Map, Rule

url_map = Map()

view_functions = {}

def add_route(endpoint, url, controller):
    """
    Add a route to the url mapping
    """
    #assert endpoint not in view_functions.keys(), 'Trying to overwrite a rule'

    view_functions.update({endpoint: controller})

    url_map.add(Rule(url, endpoint=endpoint))

def mount(mountpoint, routes):
    """
    Mount a bunch of routes to this mountpoint
    """
    for endpoint, url, controller in routes:
        url = "%s/%s" % (mountpoint.rstrip('/'), url.lstrip('/'))
        add_route(endpoint, url, controller)

add_route('index', '/', 'mediagoblin.views:root_view')

import mediagoblin.submit.routing
import mediagoblin.user_pages.routing
import mediagoblin.edit.routing
import mediagoblin.webfinger.routing
import mediagoblin.listings.routing

from mediagoblin.auth.routing import auth_routes
mount('/auth', auth_routes)
