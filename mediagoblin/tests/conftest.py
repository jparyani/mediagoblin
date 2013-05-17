# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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

from mediagoblin.tests import tools
from mediagoblin.tools.testing import _activate_testing


@pytest.fixture()
def test_app(request):
    """
    py.test fixture to pass sandboxed mediagoblin applications into tests that
    want them.

    You could make a local version of this method for your own tests
    to override the paste and config files being used by passing them
    in differently to get_app.
    """
    return tools.get_app(request)


@pytest.fixture()
def pt_fixture_enable_testing():
    """
    py.test fixture to enable testing mode in tools.
    """
    _activate_testing()
