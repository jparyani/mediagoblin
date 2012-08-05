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

'''
Make it so that ``import cloudfiles`` does not pick THIS file, but the
python-cloudfiles one.

http://docs.python.org/whatsnew/2.5.html#pep-328-absolute-and-relative-imports
'''
from __future__ import absolute_import

from mediagoblin.storage import StorageInterface, clean_listy_filepath

import cloudfiles
import mimetypes
import logging

_log = logging.getLogger(__name__)


class CloudFilesStorage(StorageInterface):
    '''
    OpenStack/Rackspace Cloud's Swift/CloudFiles support
    '''

    local_storage = False

    def __init__(self, **kwargs):
        self.param_container = kwargs.get('cloudfiles_container')
        self.param_user = kwargs.get('cloudfiles_user')
        self.param_api_key = kwargs.get('cloudfiles_api_key')
        self.param_host = kwargs.get('cloudfiles_host')
        self.param_use_servicenet = kwargs.get('cloudfiles_use_servicenet')

        # the Mime Type webm doesn't exists, let's add it
        mimetypes.add_type("video/webm", "webm")

        if not self.param_host:
            _log.info('No CloudFiles host URL specified, '
                  'defaulting to Rackspace US')

        self.connection = cloudfiles.get_connection(
            username=self.param_user,
            api_key=self.param_api_key,
            servicenet=True if self.param_use_servicenet == 'true' or \
                self.param_use_servicenet == True else False)

        _log.debug('Connected to {0} (auth: {1})'.format(
            self.connection.connection.host,
            self.connection.auth.host))

        if not self.param_container == \
                self.connection.get_container(self.param_container):
            self.container = self.connection.create_container(
                self.param_container)
            self.container.make_public(
                ttl=60 * 60 * 2)
        else:
            self.container = self.connection.get_container(
                self.param_container)

        _log.debug('Container: {0}'.format(
            self.container.name))

        self.container_uri = self.container.public_uri()

    def _resolve_filepath(self, filepath):
        return '/'.join(
            clean_listy_filepath(filepath))

    def file_exists(self, filepath):
        try:
            self.container.get_object(self._resolve_filepath(filepath))
            return True
        except cloudfiles.errors.NoSuchObject:
            return False

    def get_file(self, filepath, *args, **kwargs):
        """
        - Doesn't care about the "mode" argument.
        """
        try:
            obj = self.container.get_object(
                self._resolve_filepath(filepath))
        except cloudfiles.errors.NoSuchObject:
            obj = self.container.create_object(
                self._resolve_filepath(filepath))

            # Detect the mimetype ourselves, since some extensions (webm)
            # may not be universally accepted as video/webm
            mimetype = mimetypes.guess_type(
                filepath[-1])

            if mimetype:
                # Set the mimetype on the CloudFiles object
                obj.content_type = mimetype[0]
                obj.metadata = {'mime-type': mimetype[0]}

        return CloudFilesStorageObjectWrapper(obj, *args, **kwargs)

    def delete_file(self, filepath):
        # TODO: Also delete unused directories if empty (safely, with
        # checks to avoid race conditions).
        try:
            self.container.delete_object(
                self._resolve_filepath(filepath))
        except cloudfiles.container.ResponseError:
            pass
        finally:
            pass

    def file_url(self, filepath):
        return '/'.join([
                self.container_uri,
                self._resolve_filepath(filepath)])


class CloudFilesStorageObjectWrapper():
    """
    Wrapper for python-cloudfiles's cloudfiles.storage_object.Object
    used to circumvent the mystic `medium.jpg` corruption issue, where
    we had both python-cloudfiles and PIL doing buffering on both
    ends and causing breakage.

    This wrapper currently meets mediagoblin's needs for a public_store
    file-like object.
    """
    def __init__(self, storage_object, *args, **kwargs):
        self.storage_object = storage_object

    def read(self, *args, **kwargs):
        _log.debug('Reading {0}'.format(
            self.storage_object.name))
        return self.storage_object.read(*args, **kwargs)

    def write(self, data, *args, **kwargs):
        """
        write data to the cloudfiles storage object

        The original motivation for this wrapper is to ensure
        that buffered writing to a cloudfiles storage object does not overwrite
        any preexisting data.

        Currently this method does not support any write modes except "append".
        However if we should need it it would be easy implement.
        """
        if self.storage_object.size and type(data) == str:
            _log.debug('{0} is > 0 in size, appending data'.format(
                self.storage_object.name))
            data = self.read() + data

        _log.debug('Writing {0}'.format(
            self.storage_object.name))
        self.storage_object.write(data, *args, **kwargs)

    def close(self):
        """
        Not implemented.
        """
        pass

    def __enter__(self):
        """
        Context Manager API implementation
        http://docs.python.org/library/stdtypes.html#context-manager-types
        """
        return self

    def __exit__(self, *exc_info):
        """
        Context Manger API implementation
        see self.__enter__()
        """
        self.close()
