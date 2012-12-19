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

import shutil
import uuid

from werkzeug.utils import secure_filename

from mediagoblin.tools import common

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
            # Note: this will copy in small chunks
            shutil.copy(self.get_local_path(filepath), dest_path)
        else:
            with self.get_file(filepath, 'rb') as source_file:
                with file(dest_path, 'wb') as dest_file:
                    # Copy from remote storage in 4M chunks
                    shutil.copyfileobj(source_file, dest_file, length=4*1048576)

    def copy_local_to_storage(self, filename, filepath):
        """
        Copy this file from locally to the storage system.

        This is kind of the opposite of copy_locally.  It's likely you
        could override this method with something more appropriate to
        your storage system.
        """
        with self.get_file(filepath, 'wb') as dest_file:
            with file(filename, 'rb') as source_file:
                # Copy to storage system in 4M chunks
                shutil.copyfileobj(source_file, dest_file, length=4*1048576)


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
        storage_class = 'mediagoblin.storage.filestorage:BasicFileStorage'

    storage_class = common.import_component(storage_class)
    return storage_class(**config_params)

import filestorage
