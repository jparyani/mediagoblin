# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

user_routes = [
    Route('mediagoblin.user_pages.user_home', "/{user}/",
        controller="mediagoblin.user_pages.views:user_home"),
    Route('mediagoblin.user_pages.media_home', '/{user}/m/{media}/',
        requirements=dict(m_id="[0-9a-fA-F]{24}"),
        controller="mediagoblin.user_pages.views:media_home"),
    Route('mediagoblin.user_pages.atom_feed', '/{user}/atom/',
        controller="mediagoblin.user_pages.views:atom_feed")]
