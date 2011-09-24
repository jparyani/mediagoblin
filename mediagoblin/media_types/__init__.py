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

import os
import sys

class FileTypeNotSupported(Exception):
    pass

class InvalidFileType(Exception):
    pass

MEDIA_TYPES = [
        'mediagoblin.media_types.image',
        'mediagoblin.media_types.video']


def get_media_types():
    for media_type in MEDIA_TYPES:
        yield media_type


def get_media_managers():
    for media_type in get_media_types():
        '''
        FIXME
        __import__ returns the lowest-level module. If the plugin is located
        outside the conventional plugin module tree, it will not be loaded
        properly because of the [...]ugin.media_types.

        We need this if we want to support a separate site-specific plugin
        folder.
        '''
        try:
            __import__(media_type)
        except ImportError as e:
            raise Exception('ERROR: Could not import {0}: {1}'.format(media_type, e))
            
        yield media_type, sys.modules[media_type].MEDIA_MANAGER


def get_media_manager(_media_type = None):
    for media_type, manager in get_media_managers():
        if media_type in _media_type:
            return manager


def get_media_type_and_manager(filename):
    for media_type, manager in get_media_managers():
        if filename.find('.') > 0:
            ext = os.path.splitext(filename)[1].lower()
        else:
            raise InvalidFileType(
                'Could not find any file extension in "{0}"'.format(
                    filename))

        if ext[1:] in manager['accepted_extensions']:
            return media_type, manager
