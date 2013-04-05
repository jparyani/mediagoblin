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

from mediagoblin.tests.tools import fixture_add_collection, fixture_add_user
from mediagoblin.db.models import Collection, User
from nose.tools import assert_equal


def test_user_deletes_collection(test_app):
    # Setup db.
    user = fixture_add_user()
    coll = fixture_add_collection(user=user)
    # Reload into session:
    user = User.query.get(user.id)

    cnt1 = Collection.query.count()
    user.delete()
    cnt2 = Collection.query.count()

    assert_equal(cnt1, cnt2 + 1)
