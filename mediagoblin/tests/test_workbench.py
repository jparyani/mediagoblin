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
import tempfile

from mediagoblin.process_media import workbench


class TestWorkbench(object):
    def setUp(self):
        self.workbench_manager = workbench.WorkbenchManager(
            os.path.join(tempfile.gettempdir(), u'mgoblin_workbench_testing'))

    def test_create_workbench(self):
        workbench = self.workbench_manager.create_workbench()
        assert os.path.isdir(workbench)
        assert workbench.startswith(self.workbench_manager.base_workbench_dir)

    def test_destroy_workbench(self):
        # kill a workbench
        workbench = self.workbench_manager.create_workbench()
        tmpfile = file(os.path.join(workbench, 'temp.txt'), 'w')
        with tmpfile:
            tmpfile.write('lollerskates')

        assert os.path.exists(os.path.join(workbench, 'temp.txt'))

        self.workbench_manager.destroy_workbench(workbench)
        assert not os.path.exists(os.path.join(workbench, 'temp.txt'))
        assert not os.path.exists(workbench)
