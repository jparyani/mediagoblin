# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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
import shutil
import urlparse
import uuid
import cloudfiles
import mimetypes
import tempfile

from werkzeug.utils import secure_filename

from mediagoblin import util

########
# Errors
########


class Error(Exception):
    pass


class InvalidFilepath(Error):
    pass


class NoWebServing(Error):
    pass


class NotImplementedError(Error):
    pass


###############################################
# Storage interface & basic file implementation
###############################################

class StorageInterface(object):
    """
    Interface for the storage API.

    This interface doesn't actually provide behavior, but it defines
    what kind of storage patterns subclasses should provide.

    It is important to note that the storage API idea of a "filepath"
    is actually like ['dir1', 'dir2', 'file.jpg'], so keep that in
    mind while reading method documentation.

    You should set up your __init__ method with whatever keyword
    arguments are appropriate to your storage system, but you should
    also passively accept all extraneous keyword arguments like:

      def __init__(self, **kwargs):
          pass

    See BasicFileStorage as a simple implementation of the
    StorageInterface.
    """

    # Whether this file store is on the local filesystem.
    local_storage = False

    def __raise_not_implemented(self):
        """
        Raise a warning about some component not implemented by a
        subclass of this interface.
        """
        raise NotImplementedError(
            "This feature not implemented in this storage API implementation.")

    def file_exists(self, filepath):
        """
        Return a boolean asserting whether or not file at filepath
        exists in our storage system.

        Returns:
         True / False depending on whether file exists or not.
        """
        # Subclasses should override this method.
        self.__raise_not_implemented()

    def get_file(self, filepath, mode='r'):
        """
        Return a file-like object for reading/writing from this filepath.

        Should create directories, buckets, whatever, as necessary.
        """
        # Subclasses should override this method.
        self.__raise_not_implemented()

    def delete_file(self, filepath):
        """
        Delete or dereference the file at filepath.

        This might need to delete directories, buckets, whatever, for
        cleanliness.  (Be sure to avoid race conditions on that though)
        """
        # Subclasses should override this method.
        self.__raise_not_implemented()

    def file_url(self, filepath):
        """
        Get the URL for this file.  This assumes our storage has been
        mounted with some kind of URL which makes this possible.
        """
        # Subclasses should override this method.
        self.__raise_not_implemented()

    def get_unique_filepath(self, filepath):
        """
        If a filename at filepath already exists, generate a new name.

        Eg, if the filename doesn't exist:
        >>> storage_handler.get_unique_filename(['dir1', 'dir2', 'fname.jpg'])
        [u'dir1', u'dir2', u'fname.jpg']

        But if a file does exist, let's get one back with at uuid tacked on:
        >>> storage_handler.get_unique_filename(['dir1', 'dir2', 'fname.jpg'])
        [u'dir1', u'dir2', u'd02c3571-dd62-4479-9d62-9e3012dada29-fname.jpg']
        """
        # Make sure we have a clean filepath to start with, since
        # we'll be possibly tacking on stuff to the filename.
        filepath = clean_listy_filepath(filepath)

        if self.file_exists(filepath):
            return filepath[:-1] + ["%s-%s" % (uuid.uuid4(), filepath[-1])]
        else:
            return filepath

    def get_local_path(self, filepath):
        """
        If this is a local_storage implementation, give us a link to
        the local filesystem reference to this file.

        >>> storage_handler.get_local_path(['foo', 'bar', 'baz.jpg'])
        u'/path/to/mounting/foo/bar/baz.jpg'
        """
        # Subclasses should override this method, if applicable.
        self.__raise_not_implemented()

    def copy_locally(self, filepath, dest_path):
        """
        Copy this file locally.

        A basic working method for this is provided that should
        function both for local_storage systems and remote storge
        systems, but if more efficient systems for copying locally
        apply to your system, override this method with something more
        appropriate.
        """
        if self.local_storage:
            shutil.copy(
                self.get_local_path(filepath), dest_path)
        else:
            with self.get_file(filepath, 'rb') as source_file:
                with file(dest_path, 'wb') as dest_file:
                    dest_file.write(source_file.read())


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


class CloudFilesStorage(StorageInterface):
    class StorageObjectWrapper():
        """
        Wrapper for python-cloudfiles's cloudfiles.storage_object.Object
        used to circumvent the mystic `medium.jpg` corruption issue, where
        we had both python-cloudfiles and PIL doing buffering on both
        ends and that breaking things.

        This wrapper currently meets mediagoblin's needs for a public_store
        file-like object.
        """
        def __init__(self, storage_object):
            self.storage_object = storage_object

        def read(self, *args, **kwargs):
            return self.storage_object.read(*args, **kwargs)

        def write(self, data, *args, **kwargs):
            if self.storage_object.size and type(data) == str:
                data = self.read() + data

            self.storage_object.write(data, *args, **kwargs)


    def __init__(self, **kwargs):
        self.param_container = kwargs.get('cloudfiles_container')
        self.param_user = kwargs.get('cloudfiles_user')
        self.param_api_key = kwargs.get('cloudfiles_api_key')
        self.param_host = kwargs.get('cloudfiles_host')
        self.param_use_servicenet = kwargs.get('cloudfiles_use_servicenet')

        if not self.param_host:
            print('No CloudFiles host URL specified, '
                  'defaulting to Rackspace US')

        self.connection = cloudfiles.get_connection(
            username=self.param_user,
            api_key=self.param_api_key,
            servicenet=True if self.param_use_servicenet == 'true' or \
                self.param_use_servicenet == True else False)

        if not self.param_container == \
                self.connection.get_container(self.param_container):
            self.container = self.connection.create_container(
                self.param_container)
            self.container.make_public(
                ttl=60 * 60 * 2)
        else:
            self.container = self.connection.get_container(
                self.param_container)

        self.container_uri = self.container.public_uri()

    def _resolve_filepath(self, filepath):
        return '/'.join(
            clean_listy_filepath(filepath))

    def file_exists(self, filepath):
        try:
            object = self.container.get_object(
                self._resolve_filepath(filepath))
            return True
        except cloudfiles.errors.NoSuchObject:
            return False

    def get_file(self, filepath, *args):
        """
        - Doesn't care about the "mode" argument
        """
        try:
            obj = self.container.get_object(
                self._resolve_filepath(filepath))
        except cloudfiles.errors.NoSuchObject:
            obj = self.container.create_object(
                self._resolve_filepath(filepath))

            mimetype = mimetypes.guess_type(
                filepath[-1])

            if mimetype:
                obj.content_type = mimetype[0]

        return self.StorageObjectWrapper(obj)

    def delete_file(self, filepath):
        # TODO: Also delete unused directories if empty (safely, with
        # checks to avoid race conditions).
        self.container.delete_object(
            self._resolve_filepath(filepath))

    def file_url(self, filepath):
        return '/'.join([
                self.container_uri,
                self._resolve_filepath(filepath)])


class MountStorage(StorageInterface):
    """
    Experimental "Mount" virtual Storage Interface
    
    This isn't an interface to some real storage, instead it's a
    redirecting interface, that redirects requests to other
    "StorageInterface"s.

    For example, say you have the paths:

     1. ['user_data', 'cwebber', 'avatar.jpg']
     2. ['user_data', 'elrond', 'avatar.jpg']
     3. ['media_entries', '34352f304c3f4d0ad8ad0f043522b6f2', 'thumb.jpg']

    You could mount media_entries under CloudFileStorage and user_data
    under BasicFileStorage.  Then 1 would be passed to
    BasicFileStorage under the path ['cwebber', 'avatar.jpg'] and 3
    would be passed to CloudFileStorage under
    ['34352f304c3f4d0ad8ad0f043522b6f2', 'thumb.jpg'].

    In other words, this is kind of like mounting /home/ and /etc/
    under different filesystems on your operating system... but with
    mediagoblin filestorages :)
    
    To set this up, you currently need to call the mount() method with
    the target path and a backend, that shall be available under that
    target path.  You have to mount things in a sensible order,
    especially you can't mount ["a", "b"] before ["a"].
    """
    def __init__(self, **kwargs):
        self.mounttab = {}

    def mount(self, dirpath, backend):
        """
        Mount a new backend under dirpath
        """
        new_ent = clean_listy_filepath(dirpath)

        print "Mounting:", repr(new_ent)
        already, rem_1, table, rem_2 = self._resolve_to_backend(new_ent, True)
        print "===", repr(already), repr(rem_1), repr(rem_2), len(table)

        assert (len(rem_2) > 0) or (None not in table), \
            "That path is already mounted"
        assert (len(rem_2) > 0) or (len(table)==0), \
            "A longer path is already mounted here"

        for part in rem_2:
            table[part] = {}
            table = table[part]
        table[None] = backend

    def _resolve_to_backend(self, filepath, extra_info = False):
        """
        extra_info = True is for internal use!

        Normally, returns the backend and the filepath inside that backend.

        With extra_info = True it returns the last directory node and the
        remaining filepath from there in addition.
        """
        table = self.mounttab
        filepath = filepath[:]
        res_fp = None
        while True:
            new_be = table.get(None)
            if (new_be is not None) or res_fp is None:
                res_be = new_be
                res_fp = filepath[:]
                res_extra = (table, filepath[:])
                # print "... New res: %r, %r, %r" % (res_be, res_fp, res_extra)
            if len(filepath) == 0:
                break
            query = filepath.pop(0)
            entry = table.get(query)
            if entry is not None:
                table = entry
                res_extra = (table, filepath[:])
            else:
                break
        if extra_info:
            return (res_be, res_fp) + res_extra
        else:
            return (res_be, res_fp)

    def resolve_to_backend(self, filepath):
        backend, filepath = self._resolve_to_backend(filepath)
        if backend is None:
            raise Error("Path not mounted")
        return backend, filepath

    def __repr__(self, table = None, indent = []):
        res = []
        if table is None:
            res.append("MountStorage<")
            table = self.mounttab
        v = table.get(None)
        if v:
            res.append("  " * len(indent) + repr(indent) + ": " + repr(v))
        for k, v in table.iteritems():
            if k == None:
                continue
            res.append("  " * len(indent) + repr(k) + ":")
            res += self.__repr__(v, indent + [k])
        if table is self.mounttab:
            res.append(">")
            return "\n".join(res)
        else:
            return res

    def file_exists(self, filepath):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.file_exists(filepath)

    def get_file(self, filepath, mode='r'):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.get_file(filepath, mode)

    def delete_file(self, filepath):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.delete_file(filepath)

    def file_url(self, filepath):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.file_url(filepath)

    def get_local_path(self, filepath):
        backend, filepath = self.resolve_to_backend(filepath)
        return backend.get_local_path(filepath)

    def copy_locally(self, filepath, dest_path):
        """
        Need to override copy_locally, because the local_storage
        attribute is not correct.
        """
        backend, filepath = self.resolve_to_backend(filepath)
        backend.copy_locally(filepath, dest_path)


###########
# Utilities
###########

def clean_listy_filepath(listy_filepath):
    """
    Take a listy filepath (like ['dir1', 'dir2', 'filename.jpg']) and
    clean out any nastiness from it.


    >>> clean_listy_filepath([u'/dir1/', u'foo/../nasty', u'linooks.jpg'])
    [u'dir1', u'foo_.._nasty', u'linooks.jpg']

    Args:
    - listy_filepath: a list of filepath components, mediagoblin
      storage API style.

    Returns:
      A cleaned list of unicode objects.
    """
    cleaned_filepath = [
        unicode(secure_filename(filepath))
        for filepath in listy_filepath]

    if u'' in cleaned_filepath:
        raise InvalidFilepath(
            "A filename component could not be resolved into a usable name.")

    return cleaned_filepath


def storage_system_from_config(config_section):
    """
    Utility for setting up a storage system from a config section.

    Note that a special argument may be passed in to
    the config_section which is "storage_class" which will provide an
    import path to a storage system.  This defaults to
    "mediagoblin.storage:BasicFileStorage" if otherwise undefined.

    Arguments:
     - config_section: dictionary of config parameters

    Returns:
      An instantiated storage system.

    Example:
      storage_system_from_config(
        {'base_url': '/media/',
         'base_dir': '/var/whatever/media/'})

       Will return:
         BasicFileStorage(
           base_url='/media/',
           base_dir='/var/whatever/media')
    """
    # This construct is needed, because dict(config) does
    # not replace the variables in the config items.
    config_params = dict(config_section.iteritems())

    if 'storage_class' in config_params:
        storage_class = config_params['storage_class']
        config_params.pop('storage_class')
    else:
        storage_class = "mediagoblin.storage:BasicFileStorage"

    storage_class = util.import_component(storage_class)
    return storage_class(**config_params)
