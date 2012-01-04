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

edit_routes = [
    # Media editing view handled in user_pages/routing.py
    Route('mediagoblin.edit.profile', '/profile/',
        controller="mediagoblin.edit.views:edit_profile"),
    Route('mediagoblin.edit.account', '/account/',
        controller="mediagoblin.edit.views:edit_account")
    ]
