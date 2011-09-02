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


from routes.route import Route

tag_routes = [
    # Route('mediagoblin.listings.tags_home', "/",
    #    controller="mediagoblin.listings.views:tags_home"),
    Route('mediagoblin.listings.tags_listing', "/{tag}/",
        controller="mediagoblin.listings.views:tag_listing"),
    Route('mediagoblin.listings.tag_atom_feed', "/{tag}/atom/",
        controller="mediagoblin.listings.views:tag_atom_feed"),
    ]
    
