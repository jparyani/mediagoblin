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
import shutil
import tempfile

import six

from mediagoblin._compat import py2_unicode

# Actual workbench stuff
# ----------------------


@py2_unicode
class Workbench(object):
    """
    Represent the directory for the workbench

    WARNING: DO NOT create Workbench objects on your own,
    let the WorkbenchManager do that for you!
    """
    def __init__(self, dir):
        """
        WARNING: DO NOT create Workbench objects on your own,
        let the WorkbenchManager do that for you!
        """
        self.dir = dir

    def __str__(self):
        return six.text_type(self.dir)

    def __repr__(self):
        try:
            return str(self)
        except AttributeError:
            return 'None'

    def joinpath(self, *args):
        return os.path.join(self.dir, *args)

    def localized_file(self, storage, filepath,
                       filename_if_copying=None,
                       keep_extension_if_copying=True):
        """
        Possibly localize the file from this storage system (for read-only
        purposes, modifications should be written to a new file.).

        If the file is already local, just return the absolute filename of that
        local file.  Otherwise, copy the file locally to the workbench, and
        return the absolute path of the new file.

        If it is copying locally, we might want to require a filename like
        "source.jpg" to ensure that we won't conflict with other filenames in
        our workbench... if that's the case, make sure filename_if_copying is
        set to something like 'source.jpg'.  Relatedly, if you set
        keep_extension_if_copying, you don't have to set an extension on
        filename_if_copying yourself, it'll be set for you (assuming such an
        extension can be extacted from the filename in the filepath).

        Returns:
          localized_filename

        Examples:
          >>> wb_manager.localized_file(
          ...     '/our/workbench/subdir', local_storage,
          ...     ['path', 'to', 'foobar.jpg'])
          u'/local/storage/path/to/foobar.jpg'

          >>> wb_manager.localized_file(
          ...     '/our/workbench/subdir', remote_storage,
          ...     ['path', 'to', 'foobar.jpg'])
          '/our/workbench/subdir/foobar.jpg'

          >>> wb_manager.localized_file(
          ...     '/our/workbench/subdir', remote_storage,
          ...     ['path', 'to', 'foobar.jpg'], 'source.jpeg', False)
          '/our/workbench/subdir/foobar.jpeg'

          >>> wb_manager.localized_file(
          ...     '/our/workbench/subdir', remote_storage,
          ...     ['path', 'to', 'foobar.jpg'], 'source', True)
          '/our/workbench/subdir/foobar.jpg'
        """
        if storage.local_storage:
            return storage.get_local_path(filepath)
        else:
            if filename_if_copying is None:
                dest_filename = filepath[-1]
            else:
                orig_filename, orig_ext = os.path.splitext(filepath[-1])
                if keep_extension_if_copying and orig_ext:
                    dest_filename = filename_if_copying + orig_ext
                else:
                    dest_filename = filename_if_copying

            full_dest_filename = os.path.join(
                self.dir, dest_filename)

            # copy it over
            storage.copy_locally(
                filepath, full_dest_filename)

            return full_dest_filename

    def destroy(self):
        """
        Destroy this workbench!  Deletes the directory and all its contents!

        WARNING: Does no checks for a sane value in self.dir!
        """
        # just in case
        workbench = os.path.abspath(self.dir)
        shutil.rmtree(workbench)
        del self.dir

    def __enter__(self):
        """Make Workbench a context manager so we can use `with Workbench() as bench:`"""
        return self

    def  __exit__(self, *args):
        """Clean up context manager, aka ourselves, deleting the workbench"""
        self.destroy()


class WorkbenchManager(object):
    """
    A system for generating and destroying workbenches.

    Workbenches are actually just subdirectories of a (local) temporary
    storage space for during the processing stage. The preferred way to
    create them is to use:

        with workbenchmger.create() as workbench:
            do stuff...

    This will automatically clean up all temporary directories even in
    case of an exceptions. Also check the
    @mediagoblin.decorators.get_workbench decorator for a convenient
    wrapper.
    """

    def __init__(self, base_workbench_dir):
        self.base_workbench_dir = os.path.abspath(base_workbench_dir)
        if not os.path.exists(self.base_workbench_dir):
            os.makedirs(self.base_workbench_dir)

    def create(self):
        """
        Create and return the path to a new workbench (directory).
        """
        return Workbench(tempfile.mkdtemp(dir=self.base_workbench_dir))
