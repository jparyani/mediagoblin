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

from mediagoblin import mg_globals

from mediagoblin.tests.tools import (
    MEDIAGOBLIN_TEST_DB_NAME, suicide_if_bad_celery_environ)


def setup_package():
    suicide_if_bad_celery_environ()


def teardown_package():
    if ((mg_globals.db_connection
         and mg_globals.database.name == MEDIAGOBLIN_TEST_DB_NAME)):
            print "Killing db ..."
            mg_globals.db_connection.drop_database(MEDIAGOBLIN_TEST_DB_NAME)
            print "... done"
