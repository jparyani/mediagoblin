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
import tempfile


from mediagoblin.tools import workbench
from mediagoblin.mg_globals import setup_globals
from mediagoblin.decorators import get_workbench
from mediagoblin.tests.test_storage import get_tmp_filestorage, cleanup_storage


class TestWorkbench(object):
    def setup(self):
        self.workbench_base = tempfile.mkdtemp(prefix='gmg_workbench_testing')
        self.workbench_manager = workbench.WorkbenchManager(
            self.workbench_base)

    def teardown(self):
        # If the workbench is empty, this should work.
        os.rmdir(self.workbench_base)

    def test_create_workbench(self):
        workbench = self.workbench_manager.create()
        assert os.path.isdir(workbench.dir)
        assert workbench.dir.startswith(self.workbench_manager.base_workbench_dir)
        workbench.destroy()

    def test_joinpath(self):
        this_workbench = self.workbench_manager.create()
        tmpname = this_workbench.joinpath('temp.txt')
        assert tmpname == os.path.join(this_workbench.dir, 'temp.txt')
        this_workbench.destroy()

    def test_destroy_workbench(self):
        # kill a workbench
        this_workbench = self.workbench_manager.create()
        tmpfile_name = this_workbench.joinpath('temp.txt')
        tmpfile = open(tmpfile_name, 'w')
        with tmpfile:
            tmpfile.write('lollerskates')

        assert os.path.exists(tmpfile_name)

        wb_dir = this_workbench.dir
        this_workbench.destroy()
        assert not os.path.exists(tmpfile_name)
        assert not os.path.exists(wb_dir)

    def test_localized_file(self):
        tmpdir, this_storage = get_tmp_filestorage()
        this_workbench = self.workbench_manager.create()

        # Write a brand new file
        filepath = ['dir1', 'dir2', 'ourfile.txt']

        with this_storage.get_file(filepath, 'w') as our_file:
            our_file.write('Our file')

        # with a local file storage
        filename = this_workbench.localized_file(this_storage, filepath)
        assert filename == os.path.join(
            tmpdir, 'dir1/dir2/ourfile.txt')
        this_storage.delete_file(filepath)
        cleanup_storage(this_storage, tmpdir, ['dir1', 'dir2'])

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

        this_storage.delete_file(filepath)
        cleanup_storage(this_storage, tmpdir, ['dir1', 'dir2'])
        this_workbench.destroy()

    def test_workbench_decorator(self):
        """Test @get_workbench decorator and automatic cleanup"""
        # The decorator needs mg_globals.workbench_manager
        setup_globals(workbench_manager=self.workbench_manager)

        @get_workbench
        def create_it(workbench=None):
            # workbench dir exists?
            assert os.path.isdir(workbench.dir)
            return workbench.dir

        benchdir = create_it()
        # workbench dir has been cleaned up automatically?
        assert not os.path.isdir(benchdir)
