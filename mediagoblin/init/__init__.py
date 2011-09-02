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

import jinja2
from mediagoblin import staticdirect
from mediagoblin.init.config import (
    read_mediagoblin_config, generate_validation_report)
from mediagoblin import mg_globals
from mediagoblin.mg_globals import setup_globals
from mediagoblin.db.open import setup_connection_and_db_from_config
from mediagoblin.db.util import MigrationManager
from mediagoblin.workbench import WorkbenchManager
from mediagoblin.storage import storage_system_from_config


class Error(Exception): pass
class ImproperlyConfigured(Error): pass


def setup_global_and_app_config(config_path):
    global_config, validation_result = read_mediagoblin_config(config_path)
    app_config = global_config['mediagoblin']
    # report errors if necessary
    validation_report = generate_validation_report(
        global_config, validation_result)
    if validation_report:
        raise ImproperlyConfigured(validation_report)

    setup_globals(
        app_config=app_config,
        global_config=global_config)

    return global_config, app_config


def setup_database():
    app_config = mg_globals.app_config

    # This MUST be imported so as to set up the appropriate migrations!
    from mediagoblin.db import migrations

    # Set up the database
    connection, db = setup_connection_and_db_from_config(app_config)

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

    setup_globals(
        db_connection = connection,
        database = db)

    return connection, db


def get_jinja_loader(user_template_path=None):
    """
    Set up the Jinja template loaders, possibly allowing for user
    overridden templates.

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    if user_template_path:
        return jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(user_template_path),
             jinja2.PackageLoader('mediagoblin', 'templates')])
    else:
        return jinja2.PackageLoader('mediagoblin', 'templates')


def get_staticdirector(app_config):
    if app_config.has_key('direct_remote_path'):
        return staticdirect.RemoteStaticDirect(
            app_config['direct_remote_path'].strip())
    elif app_config.has_key('direct_remote_paths'):
        direct_remote_path_lines = app_config[
            'direct_remote_paths'].strip().splitlines()
        return staticdirect.MultiRemoteStaticDirect(
            dict([line.strip().split(' ', 1)
                  for line in direct_remote_path_lines]))
    else:
        raise ImproperlyConfigured(
            "One of direct_remote_path or "
            "direct_remote_paths must be provided")


def setup_storage():
    global_config = mg_globals.global_config

    key_short = 'publicstore'
    key_long = "storage:" + key_short
    public_store = storage_system_from_config(global_config[key_long])

    key_short = 'queuestore'
    key_long = "storage:" + key_short
    queue_store = storage_system_from_config(global_config[key_long])

    setup_globals(
        public_store = public_store,
        queue_store = queue_store)

    return public_store, queue_store


def setup_workbench():
    app_config = mg_globals.app_config

    workbench_manager = WorkbenchManager(app_config['workbench_path'])

    setup_globals(workbench_manager = workbench_manager)
