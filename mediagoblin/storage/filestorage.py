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

from mediagoblin.storage import (
    StorageInterface,
    clean_listy_filepath,
    NoWebServing)

import os
import shutil
import urlparse


class BasicFileStorage(StorageInterface):
    """
    Basic local filesystem implementation of storage API
    """

    local_storage = True

    def __init__(self, base_dir, base_url=None, **kwargs):
        """
        Keyword arguments:
        - base_dir: Base directory things will be served out of.  MUST
          be an absolute path.
        - base_url: URL files will be served from
        """
        self.base_dir = base_dir
        self.base_url = base_url

    def _resolve_filepath(self, filepath):
        """
        Transform the given filepath into a local filesystem filepath.
        """
        return os.path.join(
            self.base_dir, *clean_listy_filepath(filepath))

    def file_exists(self, filepath):
        return os.path.exists(self._resolve_filepath(filepath))

    def get_file(self, filepath, mode='r'):
        # Make directories if necessary
        if len(filepath) > 1:
            directory = self._resolve_filepath(filepath[:-1])
            if not os.path.exists(directory):
                os.makedirs(directory)

        # Grab and return the file in the mode specified
        return open(self._resolve_filepath(filepath), mode)

    def delete_file(self, filepath):
        # TODO: Also delete unused directories if empty (safely, with
        # checks to avoid race conditions).
        os.remove(self._resolve_filepath(filepath))

    def file_url(self, filepath):
        if not self.base_url:
            raise NoWebServing(
                "base_url not set, cannot provide file urls")

        return urlparse.urljoin(
            self.base_url,
            '/'.join(clean_listy_filepath(filepath)))

    def get_local_path(self, filepath):
        return self._resolve_filepath(filepath)

    def copy_local_to_storage(self, filename, filepath):
        """
        Copy this file from locally to the storage system.
        """
        # Make directories if necessary
        if len(filepath) > 1:
            directory = self._resolve_filepath(filepath[:-1])
            if not os.path.exists(directory):
                os.makedirs(directory)
        # This uses chunked copying of 16kb buffers (Py2.7):
        shutil.copy(filename, self.get_local_path(filepath))
