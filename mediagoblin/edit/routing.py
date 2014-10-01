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

from mediagoblin.tools.routing import add_route

add_route('mediagoblin.edit.profile', '/u/<string:user>/edit/',
    'mediagoblin.edit.views:edit_profile')
add_route('mediagoblin.edit.legacy_edit_profile', '/edit/profile/',
    'mediagoblin.edit.views:legacy_edit_profile')
add_route('mediagoblin.edit.account', '/edit/account/',
    'mediagoblin.edit.views:edit_account')
add_route('mediagoblin.edit.delete_account', '/edit/account/delete/',
    'mediagoblin.edit.views:delete_account')
add_route('mediagoblin.edit.verify_email', '/edit/verify_email/',
    'mediagoblin.edit.views:verify_email')
add_route('mediagoblin.edit.email', '/edit/email/',
    'mediagoblin.edit.views:change_email')
add_route('mediagoblin.edit.deauthorize_applications', '/edit/deauthorize/',
    'mediagoblin.edit.views:deauthorize_applications')
