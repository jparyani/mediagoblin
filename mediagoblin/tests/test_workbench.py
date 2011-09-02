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
import tempfile

from nose.tools import assert_raises

from mediagoblin import workbench
from mediagoblin.tests.test_storage import get_tmp_filestorage


class TestWorkbench(object):
    def setUp(self):
        self.workbench_manager = workbench.WorkbenchManager(
            os.path.join(tempfile.gettempdir(), u'mgoblin_workbench_testing'))

    def test_create_workbench(self):
        workbench = self.workbench_manager.create_workbench()
        assert os.path.isdir(workbench.dir)
        assert workbench.dir.startswith(self.workbench_manager.base_workbench_dir)

    def test_joinpath(self):
        this_workbench = self.workbench_manager.create_workbench()
        tmpname = this_workbench.joinpath('temp.txt')
        assert tmpname == os.path.join(this_workbench.dir, 'temp.txt')
        this_workbench.destroy_self()

    def test_destroy_workbench(self):
        # kill a workbench
        this_workbench = self.workbench_manager.create_workbench()
        tmpfile_name = this_workbench.joinpath('temp.txt')
        tmpfile = file(tmpfile_name, 'w')
        with tmpfile:
            tmpfile.write('lollerskates')

        assert os.path.exists(tmpfile_name)

        wb_dir = this_workbench.dir
        this_workbench.destroy_self()
        assert not os.path.exists(tmpfile_name)
        assert not os.path.exists(wb_dir)

    def test_localized_file(self):
        tmpdir, this_storage = get_tmp_filestorage()
        this_workbench = self.workbench_manager.create_workbench()
        
        # Write a brand new file
        filepath = ['dir1', 'dir2', 'ourfile.txt']

        with this_storage.get_file(filepath, 'w') as our_file:
            our_file.write('Our file')

        # with a local file storage
        filename = this_workbench.localized_file(this_storage, filepath)
        assert filename == os.path.join(
            tmpdir, 'dir1/dir2/ourfile.txt')

        # with a fake remote file storage
        tmpdir, this_storage = get_tmp_filestorage(fake_remote=True)

        # ... write a brand new file, again ;)
        with this_storage.get_file(filepath, 'w') as our_file:
            our_file.write('Our file')

        filename = this_workbench.localized_file(this_storage, filepath)
        assert filename == os.path.join(
            this_workbench.dir, 'ourfile.txt')
        
        # fake remote file storage, filename_if_copying set
        filename = this_workbench.localized_file(
            this_storage, filepath, 'thisfile')
        assert filename == os.path.join(
            this_workbench.dir, 'thisfile.txt')

        # fake remote file storage, filename_if_copying set,
        # keep_extension_if_copying set to false
        filename = this_workbench.localized_file(
            this_storage, filepath, 'thisfile.text', False)
        assert filename == os.path.join(
            this_workbench.dir, 'thisfile.text')
