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

import tempfile


class WorkbenchOutsideScope(Exception):
    """
    Raised when a workbench is outside a WorkbenchManager scope.
    """
    pass


# TODO: This doesn't seem like it'd work with Windows
DEFAULT_WORKBENCH_DIR = u'/tmp/workbench/'


class WorkbenchManager(object):
    """
    A system for generating and destroying workbenches.

    Workbenches are actually just subdirectories of a temporary storage space
    for during the processing stage.
    """

    def __init__(self, base_workbench_dir):
        self.base_workbench_dir = base_workbench_dir
        
    def create_workbench(self):
        """
        Create and return the path to a new workbench (directory).
        """
        pass

    def destroy_workbench(self, workbench):
        """
        Destroy this workbench!  Deletes the directory and all its contents!

        Makes sure the workbench actually belongs to this manager though.
        """
        pass

    def possibly_localize_file(self, workbench, storage, filepath):
        """
        Possibly localize the file from this storage system (for read-only
        purposes, modifications should be written to a new file.).

        If the file is already local, just return the absolute filename of that
        local file.  Otherwise, copy the file locally to the workbench, and
        return the absolute path of the new file.

        Also returns whether or not it copied the file locally.

        Returns:
          (localized_filename, copied_locally)
          The first of these bieng the absolute filename as described above as a
          unicode string, the second being a boolean stating whether or not we
          had to copy the file locally.
        """
        pass
