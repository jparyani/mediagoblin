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

add_route('mediagoblin.user_pages.user_home',
          '/u/<string:user>/', 'mediagoblin.user_pages.views:user_home')

add_route('mediagoblin.user_pages.media_home',
          '/u/<string:user>/m/<string:media>/',
          'mediagoblin.user_pages.views:media_home')

add_route('mediagoblin.user_pages.media_confirm_delete',
          '/u/<string:user>/m/<int:media_id>/confirm-delete/',
          'mediagoblin.user_pages.views:media_confirm_delete')

# Submission handling of new comments. TODO: only allow for POST methods
add_route('mediagoblin.user_pages.media_post_comment',
          '/u/<string:user>/m/<int:media_id>/comment/add/',
          'mediagoblin.user_pages.views:media_post_comment')

add_route('mediagoblin.user_pages.media_preview_comment',
          '/ajax/comment/preview/',
          'mediagoblin.user_pages.views:media_preview_comment')

add_route('mediagoblin.user_pages.user_gallery',
          '/u/<string:user>/gallery/',
          'mediagoblin.user_pages.views:user_gallery')

add_route('mediagoblin.user_pages.media_home.view_comment',
          '/u/<string:user>/m/<string:media>/c/<int:comment>/',
          'mediagoblin.user_pages.views:media_home')

# User's tags gallery
add_route('mediagoblin.user_pages.user_tag_gallery',
          '/u/<string:user>/tag/<string:tag>/',
          'mediagoblin.user_pages.views:user_gallery')

add_route('mediagoblin.user_pages.atom_feed',
          '/u/<string:user>/atom/',
          'mediagoblin.user_pages.views:atom_feed')

add_route('mediagoblin.user_pages.media_collect',
          '/u/<string:user>/m/<int:media_id>/collect/',
          'mediagoblin.user_pages.views:media_collect')

add_route('mediagoblin.user_pages.collection_list',
          '/u/<string:user>/collections/',
          'mediagoblin.user_pages.views:collection_list')

add_route('mediagoblin.user_pages.user_collection',
          '/u/<string:user>/collection/<string:collection>/',
          'mediagoblin.user_pages.views:user_collection')

add_route('mediagoblin.edit.edit_collection',
          '/u/<string:user>/c/<string:collection>/edit/',
          'mediagoblin.edit.views:edit_collection')

add_route('mediagoblin.user_pages.collection_confirm_delete',
          '/u/<string:user>/c/<string:collection>/confirm-delete/',
          'mediagoblin.user_pages.views:collection_confirm_delete')

add_route('mediagoblin.user_pages.collection_item_confirm_remove',
          '/u/<string:user>/collection/<string:collection>/<string:collection_item>/confirm_remove/',
          'mediagoblin.user_pages.views:collection_item_confirm_remove')

add_route('mediagoblin.user_pages.collection_atom_feed',
          '/u/<string:user>/collection/<string:collection>/atom/',
          'mediagoblin.user_pages.views:collection_atom_feed')

add_route('mediagoblin.user_pages.processing_panel',
          '/u/<string:user>/panel/',
          'mediagoblin.user_pages.views:processing_panel')

# Stray edit routes
add_route('mediagoblin.edit.edit_media',
          '/u/<string:user>/m/<int:media_id>/edit/',
          'mediagoblin.edit.views:edit_media')

add_route('mediagoblin.edit.attachments',
          '/u/<string:user>/m/<int:media_id>/attachments/',
          'mediagoblin.edit.views:edit_attachments')
