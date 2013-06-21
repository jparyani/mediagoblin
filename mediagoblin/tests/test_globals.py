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

import pytest

from mediagoblin import mg_globals


class TestGlobals(object):
    def setup(self):
        self.old_database = mg_globals.database

    def teardown(self):
        mg_globals.database = self.old_database

    def test_setup_globals(self):
        mg_globals.setup_globals(
            database='my favorite database!',
            public_store='my favorite public_store!',
            queue_store='my favorite queue_store!')

        assert mg_globals.database == 'my favorite database!'
        assert mg_globals.public_store == 'my favorite public_store!'
        assert mg_globals.queue_store == 'my favorite queue_store!'

        pytest.raises(
            AssertionError,
            mg_globals.setup_globals,
            no_such_global_foo="Dummy")
