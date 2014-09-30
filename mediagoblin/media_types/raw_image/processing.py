# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2014 MediaGoblin contributors.  See AUTHORS.
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

import os
import logging

# This needs to handle the case where it's missing
import pyexiv2

from mediagoblin.media_types.image.processing import (
    InitialProcessor, Resizer)
from mediagoblin.processing import (
    FilenameBuilder, ProcessingManager)


_log = logging.getLogger(__name__)

MEDIA_TYPE = 'mediagoblin.media_types.raw_image'
ACCEPTED_EXTENSIONS = ['nef', 'cr2']


# The entire function have to be copied

def sniff_handler(media_file, filename):
    _log.info('Sniffing {0}'.format(MEDIA_TYPE))
    name, ext = os.path.splitext(filename)
    clean_ext = ext[1:].lower()  # Strip the . from ext and make lowercase

    if clean_ext in ACCEPTED_EXTENSIONS:
        _log.info('Found file extension in supported filetypes')
        return MEDIA_TYPE
    else:
        _log.debug('Media present, extension not found in {0}'.format(
                ACCEPTED_EXTENSIONS))

    return None


class InitialRawProcessor(InitialProcessor):
    def common_setup(self):
        """
        Pull out a full-size JPEG-preview
        """
        super(InitialRawProcessor, self).common_setup()

        self._original_raw = self.process_filename

        # Read EXIF data
        md = pyexiv2.ImageMetadata(self._original_raw)
        md.read()
        self.process_filename = os.path.join(self.conversions_subdir,
            self.entry.queued_media_file[-1])

        # Extract the biggest preview and write it as our working image
        md.previews[-1].write_to_file(
            self.process_filename.encode('utf-8'))
        self.process_filename += '.jpg'
        _log.debug(u'Wrote new file from {0} to preview (jpg) {1}'.format(
            self._original_raw, self.process_filename))

        # Override the namebuilder with our new jpg-based name
        self.name_builder = FilenameBuilder(self.process_filename)


class RawImageProcessingManager(ProcessingManager):
    def __init__(self):
        super(RawImageProcessingManager, self).__init__()
        self.add_processor(InitialRawProcessor)
        self.add_processor(Resizer)
