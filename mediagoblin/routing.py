# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

from routes import Mapper

from mediagoblin.auth.routing import auth_routes
from mediagoblin.submit.routing import submit_routes
from mediagoblin.user_pages.routing import user_routes
from mediagoblin.edit.routing import edit_routes
from mediagoblin.listings.routing import tag_routes


def get_mapper():
    mapping = Mapper()
    mapping.minimization = False

    mapping.connect(
        "index", "/",
        controller="mediagoblin.views:root_view")

    mapping.extend(auth_routes, '/auth')
    mapping.extend(submit_routes, '/submit')
    mapping.extend(user_routes, '/u')
    mapping.extend(edit_routes, '/edit')
    mapping.extend(tag_routes, '/tag')

    return mapping
