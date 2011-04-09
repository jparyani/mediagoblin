# GNU Mediagoblin -- federated, autonomous media hosting
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


from werkzeug.utils import secure_filename


class Error(Exception): pass
class InvalidFilepath(Error): pass

class NotImplementedError(Error): pass


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


class StorageInterface(object):
    """
    Interface for the storage API.

    This interface doesn't actually provide behavior, but it defines
    what kind of storage patterns subclasses should provide.

    It is important to note that the storage API idea of a "filepath"
    is actually like ['dir1', 'dir2', 'file.jpg'], so keep that in
    mind while reading method documentation.
    """
    # def __init__(self, *args, **kwargs):
    #     pass

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

    def get_file(self, filepath):
        # Subclasses should override this method.
        self.__raise_not_implemented()

    def delete_file(self, filepath):
        # Subclasses should override this method.
        self.__raise_not_implemented()

    def get_unique_filename(self, filepath):
        """
        If a filename at filepath already exists, generate a new name.

        Eg, if the filename doesn't exist:
        >>> storage_handler.get_unique_filename(['dir1', 'dir2', 'fname.jpg'])
        [u'dir1', u'dir2', u'fname.jpg']
        
        But if a file does exist, let's get one back with at uuid tacked on:
        >>> storage_handler.get_unique_filename(['dir1', 'dir2', 'fname.jpg'])
        [u'dir1', u'dir2', u'd02c3571-dd62-4479-9d62-9e3012dada29-fname.jpg']
        """
        if self.file_exists(filepath):
            return filepath[:-1] + ["%s-%s" % (uuid.uuid4(), filepath[-1])]
        else:
            return filepath
