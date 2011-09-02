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

"""
Utilities for database operations.

Some note on migration and indexing tools:

We store information about what the state of the database is in the
'mediagoblin' document of the 'app_metadata' collection.  Keys in that
document relevant to here:

 - 'migration_number': The integer representing the current state of
   the migrations
"""

import copy

# Imports that other modules might use
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import InvalidId
from mongokit import ObjectId

from mediagoblin.db.indexes import ACTIVE_INDEXES, DEPRECATED_INDEXES


################
# Indexing tools
################


def add_new_indexes(database, active_indexes=ACTIVE_INDEXES):
    """
    Add any new indexes to the database.

    Args:
     - database: pymongo or mongokit database instance.
     - active_indexes: indexes to possibly add in the pattern of:
       {'collection_name': {
            'identifier': {
                'index': [index_foo_goes_here],
                'unique': True}}
       where 'index' is the index to add and all other options are
       arguments for collection.create_index.

    Returns:
      A list of indexes added in form ('collection', 'index_name')
    """
    indexes_added = []

    for collection_name, indexes in active_indexes.iteritems():
        collection = database[collection_name]
        collection_indexes = collection.index_information().keys()

        for index_name, index_data in indexes.iteritems():
            if not index_name in collection_indexes:
                # Get a copy actually so we don't modify the actual
                # structure
                index_data = copy.copy(index_data)
                index = index_data.pop('index')
                collection.create_index(
                    index, name=index_name, **index_data)

                indexes_added.append((collection_name, index_name))

    return indexes_added


def remove_deprecated_indexes(database, deprecated_indexes=DEPRECATED_INDEXES):
    """
    Remove any deprecated indexes from the database.

    Args:
     - database: pymongo or mongokit database instance.
     - deprecated_indexes: the indexes to deprecate in the pattern of:
       {'collection_name': {
            'identifier': {
                'index': [index_foo_goes_here],
                'unique': True}}

       (... although we really only need the 'identifier' here, as the
       rest of the information isn't used in this case.  But it's kept
       around so we can remember what it was)

    Returns:
      A list of indexes removed in form ('collection', 'index_name')
    """
    indexes_removed = []

    for collection_name, indexes in deprecated_indexes.iteritems():
        collection = database[collection_name]
        collection_indexes = collection.index_information().keys()

        for index_name, index_data in indexes.iteritems():
            if index_name in collection_indexes:
                collection.drop_index(index_name)

                indexes_removed.append((collection_name, index_name))

    return indexes_removed


#################
# Migration tools
#################

# The default migration registry...
# 
# Don't set this yourself!  RegisterMigration will automatically fill
# this with stuff via decorating methods in migrations.py

class MissingCurrentMigration(Exception): pass


MIGRATIONS = {}


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
    def __init__(self, migration_number, migration_registry=MIGRATIONS):
        assert migration_number > 0, "Migration number must be > 0!"
        assert not migration_registry.has_key(migration_number), \
            "Duplicate migration numbers detected!  That's not allowed!"

        self.migration_number = migration_number
        self.migration_registry = migration_registry

    def __call__(self, migration):
        self.migration_registry[self.migration_number] = migration
        return migration


class MigrationManager(object):
    """
    Migration handling tool.

    Takes information about a database, lets you update the database
    to the latest migrations, etc.
    """
    def __init__(self, database, migration_registry=MIGRATIONS):
        """
        Args:
         - database: database we're going to migrate
         - migration_registry: where we should find all migrations to
           run
        """
        self.database = database
        self.migration_registry = migration_registry
        self._sorted_migrations = None

    def _ensure_current_migration_record(self):
        """
        If there isn't a database[u'app_metadata'] mediagoblin entry
        with the 'current_migration', throw an error.
        """
        if self.database_current_migration() is None:
            raise MissingCurrentMigration(
                "Tried to call function which requires "
                "'current_migration' set in database")

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

    def set_current_migration(self, migration_number):
        """
        Set the migration in the database to migration_number
        """
        # Add the mediagoblin migration if necessary
        self.database[u'app_metadata'].update(
            {u'_id': u'mediagoblin'},
            {u'$set': {u'current_migration': migration_number}},
            upsert=True)

    def install_migration_version_if_missing(self):
        """
        Sets the migration to the latest version if no migration
        version at all is set.
        """
        mgoblin_metadata = self.database[u'app_metadata'].find_one(
            {u'_id': u'mediagoblin'})
        if not mgoblin_metadata:
            latest_migration = self.latest_migration()
            self.set_current_migration(latest_migration)

    def database_current_migration(self):
        """
        Return the current migration in the database.
        """
        mgoblin_metadata = self.database[u'app_metadata'].find_one(
            {u'_id': u'mediagoblin'})
        if not mgoblin_metadata:
            return None
        else:
            return mgoblin_metadata[u'current_migration']

    def database_at_latest_migration(self):
        """
        See if the database is at the latest migration.
        Returns a boolean.
        """
        current_migration = self.database_current_migration()
        return current_migration == self.latest_migration()

    def migrations_to_run(self):
        """
        Get a list of migrations to run still, if any.
        
        Note that calling this will set your migration version to the
        latest version if it isn't installed to anything yet!
        """
        self._ensure_current_migration_record()

        db_current_migration = self.database_current_migration()

        return [
            (migration_number, migration_func)
            for migration_number, migration_func in self.sorted_migrations
            if migration_number > db_current_migration]

    def migrate_new(self, pre_callback=None, post_callback=None):
        """
        Run all migrations.

        Includes two optional args:
         - pre_callback: if called, this is a callback on something to
           run pre-migration.  Takes (migration_number, migration_func)
           as arguments
         - pre_callback: if called, this is a callback on something to
           run post-migration.  Takes (migration_number, migration_func)
           as arguments
        """
        # If we aren't set to any version number, presume we're at the
        # latest (which means we'll do nothing here...)
        self.install_migration_version_if_missing()

        for migration_number, migration_func in self.migrations_to_run():
            if pre_callback:
                pre_callback(migration_number, migration_func)
            migration_func(self.database)
            self.set_current_migration(migration_number)
            if post_callback:
                post_callback(migration_number, migration_func)
