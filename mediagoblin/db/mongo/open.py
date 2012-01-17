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

import pymongo
import mongokit
from paste.deploy.converters import asint
from mediagoblin.db.mongo import models
from mediagoblin.db.mongo.util import MigrationManager


def connect_database_from_config(app_config, use_pymongo=False):
    """
    Connect to the main database, take config from app_config

    Optionally use pymongo instead of mongokit for the connection.
    """
    port = app_config.get('db_port')
    if port:
        port = asint(port)

    if use_pymongo:
        connection = pymongo.Connection(
            app_config.get('db_host'), port)
    else:
        connection = mongokit.Connection(
            app_config.get('db_host'), port)
    return connection


def setup_connection_and_db_from_config(app_config, use_pymongo=False):
    """
    Setup connection and database from config.

    Optionally use pymongo instead of mongokit.
    """
    connection = connect_database_from_config(app_config, use_pymongo)
    database_path = app_config['db_name']
    db = connection[database_path]

    if not use_pymongo:
        models.register_models(connection)

    return (connection, db)


def check_db_migrations_current(db):
    # This MUST be imported so as to set up the appropriate migrations!
    from mediagoblin.db.mongo import migrations

    # Init the migration number if necessary
    migration_manager = MigrationManager(db)
    migration_manager.install_migration_version_if_missing()

    # Tiny hack to warn user if our migration is out of date
    if not migration_manager.database_at_latest_migration():
        db_migration_num = migration_manager.database_current_migration()
        latest_migration_num = migration_manager.latest_migration()
        if db_migration_num < latest_migration_num:
            print (
                "*WARNING:* Your migrations are out of date, "
                "maybe run ./bin/gmg migrate?")
        elif db_migration_num > latest_migration_num:
            print (
                "*WARNING:* Your migrations are out of date... "
                "in fact they appear to be from the future?!")
