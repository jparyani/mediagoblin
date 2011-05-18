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

import mongokit
from paste.deploy.converters import asint
from mediagoblin.db import models


def connect_database_from_config(app_config):
    """Connect to the main database, take config from app_config"""
    port = app_config.get('db_port')
    if port:
        port = asint(port)
    connection = mongokit.Connection(
        app_config.get('db_host'), port)
    return connection

def setup_connection_and_db_from_config(app_config):
    connection = connect_database_from_config(app_config)
    database_path = app_config.get('db_name', 'mediagoblin')
    db = connection[database_path]
    models.register_models(connection)
    # Could configure indexes here on db
    return (connection, db)
