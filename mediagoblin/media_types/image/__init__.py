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

from mediagoblin.media_types.image.processing import process_image, \
    sniff_handler


MEDIA_MANAGER = {
    "human_readable": "Image",
    "processor": process_image, # alternately a string,
                                # 'mediagoblin.media_types.image.processing'?
    "sniff_handler": sniff_handler,
    "display_template": "mediagoblin/media_displays/image.html",
    "default_thumb": "images/media_thumbs/image.png",
    "accepted_extensions": ["jpg", "jpeg", "png", "gif", "tiff"],

    # Used by the media_entry.get_display_media method
    "media_fetch_order": [u'medium', u'original', u'thumb'],
}
