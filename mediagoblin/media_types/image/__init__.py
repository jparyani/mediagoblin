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
import datetime
import logging

from mediagoblin.media_types import MediaManagerBase
from mediagoblin.media_types.image.processing import sniff_handler, \
        ImageProcessingManager

_log = logging.getLogger(__name__)


ACCEPTED_EXTENSIONS = ["jpe", "jpg", "jpeg", "png", "gif", "tiff"]
MEDIA_TYPE = 'mediagoblin.media_types.image'


class ImageMediaManager(MediaManagerBase):
    human_readable = "Image"
    display_template = "mediagoblin/media_displays/image.html"
    default_thumb = "images/media_thumbs/image.png"

    media_fetch_order = [u'medium', u'original', u'thumb']

    def get_original_date(self):
        """
        Get the original date and time from the EXIF information. Returns
        either a datetime object or None (if anything goes wrong)
        """
        if not self.entry.media_data or not self.entry.media_data.exif_all:
            return None

        try:
            # Try wrapped around all since exif_all might be none,
            # EXIF DateTimeOriginal or printable might not exist
            # or strptime might not be able to parse date correctly
            exif_date = self.entry.media_data.exif_all[
                'EXIF DateTimeOriginal']['printable']
            original_date = datetime.datetime.strptime(
                exif_date,
                '%Y:%m:%d %H:%M:%S')
            return original_date
        except (KeyError, ValueError):
            return None

def get_media_type_and_manager(ext):
    if ext in ACCEPTED_EXTENSIONS:
        return MEDIA_TYPE, ImageMediaManager


hooks = {
    'get_media_type_and_manager': get_media_type_and_manager,
    'sniff_handler': sniff_handler,
    ('media_manager', MEDIA_TYPE): lambda: ImageMediaManager,
    ('reprocess_manager', MEDIA_TYPE): lambda: ImageProcessingManager,
}
