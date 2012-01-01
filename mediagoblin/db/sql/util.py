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


import sys

def _simple_printer(string):
    """
    Prints a string, but without an auto \n at the end.
    """
    sys.stdout.write(string)
    sys.stdout.flush()


class MigrationManager(object):
    """
    Migration handling tool.

    Takes information about a database, lets you update the database
    to the latest migrations, etc.
    """

    def __init__(self, name, models, migration_registry, database,
                 printer=_simple_printer):
        """
        Args:
         - name: identifier of this section of the database
         - database: database we're going to migrate
         - migration_registry: where we should find all migrations to
           run
        """
        self.name = name
        self.models = models
        self.database = database
        self.migration_registry = migration_registry
        self._sorted_migrations = None
        self.printer = printer

        # For convenience
        from mediagoblin.db.sql.models import MigrationData

        self.migration_model = MigrationData
        self.migration_table = MigrationData.__table__

    @property
    def sorted_migrations(self):
        """
        Sort migrations if necessary and store in self._sorted_migrations
        """
        if not self._sorted_migrations:
            self._sorted_migrations = sorted(
                self.migration_registry.items(),
                # sort on the key... the migration number
                key=lambda migration_tuple: migration_tuple[0])

        return self._sorted_migrations

    def latest_migration(self):
        """
        Return a migration number for the latest migration, or 0 if
        there are no migrations.
        """
        if self.sorted_migrations:
            return self.sorted_migrations[-1][0]
        else:
            # If no migrations have been set, we start at 0.
            return 0

    def database_current_migration(self):
        """
        Return the current migration in the database.
        """
        # TODO

    def set_current_migration(self, migration_number):
        """
        Set the migration in the database to migration_number
        """
        # TODO
        pass

    def migrations_to_run(self):
        """
        Get a list of migrations to run still, if any.
        
        Note that calling this will set your migration version to the
        latest version if it isn't installed to anything yet!
        """
        ## TODO
        # self._ensure_current_migration_record()
        #
        # db_current_migration = self.database_current_migration()
        #
        # return [
        #     (migration_number, migration_func)
        #     for migration_number, migration_func in self.sorted_migrations
        #     if migration_number > db_current_migration]
        pass

    def init_tables(self):
        ## TODO
        pass

    def create_new_migration_record(self):
        ## TODO
        pass

    def dry_run(self):
        """
        Print out a dry run of what we would have upgraded.
        """
        if self.database_current_migration() is None:
            self.printer(
                    u'~> Woulda initialized: %s\n' % self.name_for_printing())
            return u'inited'

        migrations_to_run = self.migrations_to_run()
        if migrations_to_run:
            self.printer(
                u'~> Woulda updated %s:\n' % self.name_for_printing())

            for migration_number, migration_func in migrations_to_run():
                self.printer(
                    u'   + Would update %s, "%s"\n' % (
                        migration_number, migration_func.func_name))

            return u'migrated'
        
    def name_for_printing(self):
        if self.name == u'__main__':
            return u"main mediagoblin tables"
        else:
            # TODO: Use the friendlier media manager "human readable" name
            return u'media type "%s"' % self.name

    def init_or_migrate(self, printer=_simple_printer):
        """
        Initialize the database or migrate if appropriate.

        Returns information about whether or not we initialized
        ('inited'), migrated ('migrated'), or did nothing (None)
        """
        # Find out what migration number, if any, this database data is at,
        # and what the latest is.
        migration_number = self.database_current_migration()

        # Is this our first time?  Is there even a table entry for
        # this identifier?
        # If so:
        #  - create all tables
        #  - create record in migrations registry
        #  - print / inform the user
        #  - return 'inited'
        if migration_number is None:
            self.printer(u"-> Initializing %s... " % self.name_for_printing())

            self.init_tables()
            # auto-set at latest migration number
            self.create_new_migration_record()  
            
            self.printer(u"done.\n")
            return u'inited'

        # Run migrations, if appropriate.
        migrations_to_run = self.migrations_to_run()
        if migrations_to_run:
            self.printer(
                u'~> Updating %s:\n' % self.name_for_printing())
            for migration_number, migration_func in migrations_to_run():
                self.printer(
                    u'   + Running migration %s, "%s"... ' % (
                        migration_number, migration_func.func_name))
                migration_func(self.database)
                self.printer('done.')

            return u'migrated'

        # Otherwise return None.  Well it would do this anyway, but
        # for clarity... ;)
        return None


class RegisterMigration(object):
    """
    Tool for registering migrations

    Call like:

    @RegisterMigration(33)
    def update_dwarves(database):
        [...]

    This will register your migration with the default migration
    registry.  Alternately, to specify a very specific
    migration_registry, you can pass in that as the second argument.

    Note, the number of your migration should NEVER be 0 or less than
    0.  0 is the default "no migrations" state!
    """
    def __init__(self, migration_number, migration_registry):
        assert migration_number > 0, "Migration number must be > 0!"
        assert migration_number not in migration_registry, \
            "Duplicate migration numbers detected!  That's not allowed!"

        self.migration_number = migration_number
        self.migration_registry = migration_registry

    def __call__(self, migration):
        self.migration_registry[self.migration_number] = migration
        return migration


def assure_migrations_table_setup(db):
    """
    Make sure the migrations table is set up in the database.
    """
    from mediagoblin.db.sql.models import MigrationData

    if not MigrationData.__table__.exists(db):
        MigrationData.metadata.create_all(
            db, tables=[MigrationData.__table__])
