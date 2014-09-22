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

import logging

import six
from sqlalchemy.orm import sessionmaker

from mediagoblin.db.open import setup_connection_and_db_from_config
from mediagoblin.db.migration_tools import MigrationManager, AlembicMigrationManager
from mediagoblin.init import setup_global_and_app_config
from mediagoblin.tools.common import import_component

_log = logging.getLogger(__name__)
logging.basicConfig()
## Let's not set the level as debug by default to avoid confusing users :)
# _log.setLevel(logging.DEBUG)


def dbupdate_parse_setup(subparser):
    pass


class DatabaseData(object):
    def __init__(self, name, models, foundations, migrations):
        self.name = name
        self.models = models
        self.foundations = foundations
        self.migrations = migrations

    def make_migration_manager(self, session):
        return MigrationManager(
            self.name, self.models, self.foundations, self.migrations, session)


def gather_database_data(plugins):
    """
    Gather all database data relevant to the extensions we have
    installed so we can do migrations and table initialization.

    Returns a list of DatabaseData objects.
    """
    managed_dbdata = []

    # Add main first
    from mediagoblin.db.models import MODELS as MAIN_MODELS
    from mediagoblin.db.migrations import MIGRATIONS as MAIN_MIGRATIONS
    from mediagoblin.db.models import FOUNDATIONS as MAIN_FOUNDATIONS

    managed_dbdata.append(
        DatabaseData(
            u'__main__', MAIN_MODELS, MAIN_FOUNDATIONS, MAIN_MIGRATIONS))

    for plugin in plugins:
        try:
            models = import_component('{0}.models:MODELS'.format(plugin))
        except ImportError as exc:
            _log.debug('No models found for {0}: {1}'.format(
                plugin,
                exc))

            models = []
        except AttributeError as exc:
            _log.warning('Could not find MODELS in {0}.models, have you \
forgotten to add it? ({1})'.format(plugin, exc))
            models = []

        try:
            migrations = import_component('{0}.migrations:MIGRATIONS'.format(
                plugin))
        except ImportError as exc:
            _log.debug('No migrations found for {0}: {1}'.format(
                plugin,
                exc))

            migrations = {}
        except AttributeError as exc:
            _log.debug('Could not find MIGRATIONS in {0}.migrations, have you \
forgotten to add it? ({1})'.format(plugin, exc))
            migrations = {}

        try:
            foundations = import_component('{0}.models:FOUNDATIONS'.format(plugin))
        except ImportError as exc:
            foundations = {}
        except AttributeError as exc:
            foundations = {}

        if models:
            managed_dbdata.append(
                    DatabaseData(plugin, models, foundations, migrations))


    return managed_dbdata


def run_alembic_migrations(db, app_config, global_config):
    """Initializes a database and runs all Alembic migrations."""
    Session = sessionmaker(bind=db.engine)
    manager = AlembicMigrationManager(Session())
    manager.init_or_migrate()


def run_dbupdate(app_config, global_config):
    """
    Initialize or migrate the database as specified by the config file.

    Will also initialize or migrate all extensions (media types, and
    in the future, plugins)
    """

    # Set up the database
    db = setup_connection_and_db_from_config(app_config, migrations=True)
    # Run the migrations
    run_all_migrations(db, app_config, global_config)

    # TODO: Make this happen regardless of python 2 or 3 once ensured
    # to be "safe"!
    if six.PY3:
        run_alembic_migrations(db, app_config, global_config)


def run_all_migrations(db, app_config, global_config):
    """
    Initializes or migrates a database that already has a
    connection setup and also initializes or migrates all
    extensions based on the config files.

    It can be used to initialize an in-memory database for
    testing.
    """
    # Gather information from all media managers / projects
    dbdatas = gather_database_data(
            list(global_config.get('plugins', {}).keys()))

    Session = sessionmaker(bind=db.engine)

    # Setup media managers for all dbdata, run init/migrate and print info
    # For each component, create/migrate tables
    for dbdata in dbdatas:
        migration_manager = dbdata.make_migration_manager(Session())
        migration_manager.init_or_migrate()


def dbupdate(args):
    global_config, app_config = setup_global_and_app_config(args.conf_file)
    run_dbupdate(app_config, global_config)
