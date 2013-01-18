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

from mediagoblin import mg_globals
from mediagoblin.tests.tools import get_app, fixture_add_user
from mediagoblin.db.models import User


def test_get_app_wipes_db():
    """
    Make sure we get a fresh database on every wipe :)
    """
    get_app(dump_old_app=True)
    assert User.query.count() == 0

    fixture_add_user()
    assert User.query.count() == 1

    get_app(dump_old_app=False)
    assert User.query.count() == 1

    get_app(dump_old_app=True)
    assert User.query.count() == 0
