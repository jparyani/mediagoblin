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

from mediagoblin.media_types import MediaManagerBase
from mediagoblin.media_types.stl.processing import StlProcessingManager, \
    sniff_handler


MEDIA_TYPE = 'mediagoblin.media_types.stl'
ACCEPTED_EXTENSIONS = ["obj", "stl"]


class STLMediaManager(MediaManagerBase):
    human_readable = "stereo lithographics"
    display_template = "mediagoblin/media_displays/stl.html"
    default_thumb = "images/media_thumbs/video.jpg"


def get_media_type_and_manager(ext):
    if ext in ACCEPTED_EXTENSIONS:
        return MEDIA_TYPE, STLMediaManager

hooks = {
    'get_media_type_and_manager': get_media_type_and_manager,
    'sniff_handler': sniff_handler,
    ('media_manager', MEDIA_TYPE): lambda: STLMediaManager,
    ('reprocess_manager', MEDIA_TYPE): lambda: StlProcessingManager,
}
