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
import re
import urlparse
import uuid

from werkzeug.utils import secure_filename

from mediagoblin import util

########
# Errors
########

class Error(Exception): pass
class InvalidFilepath(Error): pass
class NoWebServing(Error): pass

class NotImplementedError(Error): pass


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


class BasicFileStorage(StorageInterface):
    """
    Basic local filesystem implementation of storage API
    """

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


###########
# Utilities
###########

def clean_listy_filepath(listy_filepath):
    """
    Take a listy filepath (like ['dir1', 'dir2', 'filename.jpg']) and
    clean out any nastiness from it.

    For example:
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


def storage_system_from_paste_config(paste_config, storage_prefix):
    """
    Utility for setting up a storage system from the paste app config.

    Note that a special argument may be passed in to the paste_config
    which is "${storage_prefix}_storage_class" which will provide an
    import path to a storage system.  This defaults to
    "mediagoblin.storage:BasicFileStorage" if otherwise undefined.

    Arguments:
     - paste_config: dictionary of config parameters
     - storage_prefix: the storage system we're setting up / will be
       getting keys/arguments from.  For example 'publicstore' will
       grab all arguments that are like 'publicstore_FOO'.

    Returns:
      An instantiated storage system.

    Example:
      storage_system_from_paste_config(
        {'publicstore_base_url': '/media/',
         'publicstore_base_dir': '/var/whatever/media/'},
        'publicstore')

       Will return:
         BasicFileStorage(
           base_url='/media/',
           base_dir='/var/whatever/media')
    """
    prefix_re = re.compile('^%s_(.+)$' % re.escape(storage_prefix))

    config_params = dict(
        [(prefix_re.match(key).groups()[0], value)
         for key, value in paste_config.iteritems()
         if prefix_re.match(key)])

    if config_params.has_key('storage_class'):
        storage_class = config_params['storage_class']
        config_params.pop('storage_class')
    else:
        storage_class = "mediagoblin.storage:BasicFileStorage"

    storage_class = util.import_component(storage_class)
    return storage_class(**config_params)
