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

from mediagoblin.tests.tools import get_test_app

from mediagoblin import mg_globals


def test_get_test_app_wipes_db():
    """
    Make sure we get a fresh database on every wipe :)
    """
    get_test_app()
    assert mg_globals.database.User.find().count() == 0

    new_user = mg_globals.database.User()
    new_user['username'] = u'lolcat'
    new_user['email'] = u'lol@cats.example.org'
    new_user['pw_hash'] = u'pretend_this_is_a_hash'
    new_user.save()
    assert mg_globals.database.User.find().count() == 1

    get_test_app()

    assert mg_globals.database.User.find().count() == 0
