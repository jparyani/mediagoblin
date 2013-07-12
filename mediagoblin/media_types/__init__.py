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

import os
import logging
import tempfile

from mediagoblin.tools.pluginapi import hook_handle
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

_log = logging.getLogger(__name__)

class FileTypeNotSupported(Exception):
    pass

class InvalidFileType(Exception):
    pass


class MediaManagerBase(object):
    "Base class for all media managers"

    # Please override in actual media managers
    media_fetch_order = None

    @staticmethod
    def sniff_handler(*args, **kwargs):
        return False

    def __init__(self, entry):
        self.entry = entry

    def __getitem__(self, i):
        return getattr(self, i)

    def __contains__(self, i):
        return hasattr(self, i)


def sniff_media(media):
    '''
    Iterate through the enabled media types and find those suited
    for a certain file.
    '''

    try:
        return get_media_type_and_manager(media.filename)
    except FileTypeNotSupported:
        _log.info('No media handler found by file extension. Doing it the expensive way...')
        # Create a temporary file for sniffers suchs as GStreamer-based
        # Audio video
        media_file = tempfile.NamedTemporaryFile()
        media_file.write(media.stream.read())
        media.stream.seek(0)

        media_type = hook_handle('sniff_handler', media_file, media=media)
        if media_type:
            _log.info('{0} accepts the file'.format(media_type))
            return media_type, hook_handle(('media_manager', media_type))
        else:
            _log.debug('{0} did not accept the file'.format(media_type))

    raise FileTypeNotSupported(
        # TODO: Provide information on which file types are supported
        _(u'Sorry, I don\'t support that file type :('))


def get_media_type_and_manager(filename):
    '''
    Try to find the media type based on the file name, extension
    specifically. This is used as a speedup, the sniffing functionality
    then falls back on more in-depth bitsniffing of the source file.
    '''
    if filename.find('.') > 0:
        # Get the file extension
        ext = os.path.splitext(filename)[1].lower()

        # Omit the dot from the extension and match it against
        # the media manager
        if hook_handle('get_media_type_and_manager', ext[1:]):
            return hook_handle('get_media_type_and_manager', ext[1:])
    else:
        _log.info('File {0} has no file extension, let\'s hope the sniffers get it.'.format(
            filename))

    raise FileTypeNotSupported(
        _(u'Sorry, I don\'t support that file type :('))
