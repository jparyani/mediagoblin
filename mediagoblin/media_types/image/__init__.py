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

from mediagoblin.media_types import MediaManagerBase
from mediagoblin.media_types.image.processing import process_image, \
    sniff_handler


class ImageMediaManager(MediaManagerBase):
    human_readable = "Image"
    processor = staticmethod(process_image)
    sniff_handler = staticmethod(sniff_handler)
    display_template = "mediagoblin/media_displays/image.html"
    default_thumb = "images/media_thumbs/image.png"
    accepted_extensions = ["jpg", "jpeg", "png", "gif", "tiff"]
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


MEDIA_MANAGER = ImageMediaManager
