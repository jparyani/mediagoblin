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


from nose.tools import assert_raises
from pymongo import Connection

from mediagoblin.tests.tools import (
    install_fixtures_simple, assert_db_meets_expected)
from mediagoblin.db.util import (
    RegisterMigration, MigrationManager, ObjectId,
    MissingCurrentMigration)

# This one will get filled with local migrations
TEST_MIGRATION_REGISTRY = {}
# this one won't get filled
TEST_EMPTY_MIGRATION_REGISTRY = {}

MIGRATION_DB_NAME = u'__mediagoblin_test_migrations__'


######################
# Fake test migrations
######################

@RegisterMigration(1, TEST_MIGRATION_REGISTRY)
def creature_add_magical_powers(database):
    """
    Add lists of magical powers.

    This defaults to [], an empty list.  Since we haven't declared any
    magical powers, all existing monsters, setting to an empty list is
    fine.
    """
    database['creatures'].update(
        {'magical_powers': {'$exists': False}},
        {'$set': {'magical_powers': []}},
        multi=True)


@RegisterMigration(2, TEST_MIGRATION_REGISTRY)
def creature_rename_num_legs_to_num_limbs(database):
    """
    It turns out we want to track how many limbs a creature has, not
    just how many legs.  We don't care about the ambiguous distinction
    between arms/legs currently.
    """
    # $rename not available till 1.7.2+, Debian Stable only includes
    # 1.4.4... we should do renames manually for now :(

    collection = database['creatures']
    target = collection.find(
        {'num_legs': {'$exists': True}})

    for document in target:
        # A lame manual renaming.
        document['num_limbs'] = document.pop('num_legs')
        collection.save(document)


@RegisterMigration(3, TEST_MIGRATION_REGISTRY)
def creature_remove_is_demon(database):
    """
    It turns out we don't care much about whether creatures are demons
    or not.
    """
    database['creatures'].update(
        {'is_demon': {'$exists': True}},
        {'$unset': {'is_demon': 1}},
        multi=True)


@RegisterMigration(4, TEST_MIGRATION_REGISTRY)
def level_exits_dict_to_list(database):
    """
    For the sake of the indexes we want to write, and because we
    intend to add more flexible fields, we want to move level exits
    from like:

      {'big_door': 'castle_level_id',
       'trapdoor': 'dungeon_level_id'}

    to like:

      [{'name': 'big_door',
        'exits_to': 'castle_level_id'},
       {'name': 'trapdoor',
        'exits_to': 'dungeon_level_id'}]
    """
    collection = database['levels']
    target = collection.find(
        {'exits': {'$type': 3}})

    for level in target:
        new_exits = []
        for exit_name, exits_to in level['exits'].items():
            new_exits.append(
                {'name': exit_name,
                 'exits_to': exits_to})

        level['exits'] = new_exits
        collection.save(level)


CENTIPEDE_OBJECTID = ObjectId()
WOLF_OBJECTID = ObjectId()
WIZARDSNAKE_OBJECTID = ObjectId()

UNMIGRATED_DBDATA = {
    'creatures': [
        {'_id': CENTIPEDE_OBJECTID,
         'name': 'centipede',
         'num_legs': 100,
         'is_demon': False},
        {'_id': WOLF_OBJECTID,
         'name': 'wolf',
         'num_legs': 4,
         'is_demon': False},
        # don't ask me what a wizardsnake is.
        {'_id': WIZARDSNAKE_OBJECTID,
         'name': 'wizardsnake',
         'num_legs': 0,
         'is_demon': True}],
    'levels': [
        {'_id': 'necroplex',
         'name': 'The Necroplex',
         'description': 'A complex full of pure deathzone.',
         'exits': {
                'deathwell': 'evilstorm',
                'portal': 'central_park'}},
        {'_id': 'evilstorm',
         'name': 'Evil Storm',
         'description': 'A storm full of pure evil.',
         'exits': {}}, # you can't escape the evilstorm
        {'_id': 'central_park',
         'name': 'Central Park, NY, NY',
         'description': "New York's friendly Central Park.",
         'exits': {
                'portal': 'necroplex'}}]}


EXPECTED_POST_MIGRATION_UNMIGRATED_DBDATA = {
    'creatures': [
        {'_id': CENTIPEDE_OBJECTID,
         'name': 'centipede',
         'num_limbs': 100,
         'magical_powers': []},
        {'_id': WOLF_OBJECTID,
         'name': 'wolf',
         'num_limbs': 4,
         # kept around namely to check that it *isn't* removed!
         'magical_powers': []},
        {'_id': WIZARDSNAKE_OBJECTID,
         'name': 'wizardsnake',
         'num_limbs': 0,
         'magical_powers': []}],
    'levels': [
        {'_id': 'necroplex',
         'name': 'The Necroplex',
         'description': 'A complex full of pure deathzone.',
         'exits': [
                {'name': 'deathwell',
                 'exits_to': 'evilstorm'},
                {'name': 'portal',
                 'exits_to': 'central_park'}]},
        {'_id': 'evilstorm',
         'name': 'Evil Storm',
         'description': 'A storm full of pure evil.',
         'exits': []}, # you can't escape the evilstorm
        {'_id': 'central_park',
         'name': 'Central Park, NY, NY',
         'description': "New York's friendly Central Park.",
         'exits': [
                {'name': 'portal',
                 'exits_to': 'necroplex'}]}]}

# We want to make sure that if we're at migration 3, migration 3
# doesn't get re-run.

SEMI_MIGRATED_DBDATA = {
    'creatures': [
        {'_id': CENTIPEDE_OBJECTID,
         'name': 'centipede',
         'num_limbs': 100,
         'magical_powers': []},
        {'_id': WOLF_OBJECTID,
         'name': 'wolf',
         'num_limbs': 4,
         # kept around namely to check that it *isn't* removed!
         'is_demon': False,
         'magical_powers': [
                'ice_breath', 'death_stare']},
        {'_id': WIZARDSNAKE_OBJECTID,
         'name': 'wizardsnake',
         'num_limbs': 0,
         'magical_powers': [
                'death_rattle', 'sneaky_stare',
                'slithery_smoke', 'treacherous_tremors'],
         'is_demon': True}],
    'levels': [
        {'_id': 'necroplex',
         'name': 'The Necroplex',
         'description': 'A complex full of pure deathzone.',
         'exits': {
                'deathwell': 'evilstorm',
                'portal': 'central_park'}},
        {'_id': 'evilstorm',
         'name': 'Evil Storm',
         'description': 'A storm full of pure evil.',
         'exits': {}}, # you can't escape the evilstorm
        {'_id': 'central_park',
         'name': 'Central Park, NY, NY',
         'description': "New York's friendly Central Park.",
         'exits': {
                'portal': 'necroplex'}}]}


EXPECTED_POST_MIGRATION_SEMI_MIGRATED_DBDATA = {
    'creatures': [
        {'_id': CENTIPEDE_OBJECTID,
         'name': 'centipede',
         'num_limbs': 100,
         'magical_powers': []},
        {'_id': WOLF_OBJECTID,
         'name': 'wolf',
         'num_limbs': 4,
         # kept around namely to check that it *isn't* removed!
         'is_demon': False,
         'magical_powers': [
                'ice_breath', 'death_stare']},
        {'_id': WIZARDSNAKE_OBJECTID,
         'name': 'wizardsnake',
         'num_limbs': 0,
         'magical_powers': [
                'death_rattle', 'sneaky_stare',
                'slithery_smoke', 'treacherous_tremors'],
         'is_demon': True}],
    'levels': [
        {'_id': 'necroplex',
         'name': 'The Necroplex',
         'description': 'A complex full of pure deathzone.',
         'exits': [
                {'name': 'deathwell',
                 'exits_to': 'evilstorm'},
                {'name': 'portal',
                 'exits_to': 'central_park'}]},
        {'_id': 'evilstorm',
         'name': 'Evil Storm',
         'description': 'A storm full of pure evil.',
         'exits': []}, # you can't escape the evilstorm
        {'_id': 'central_park',
         'name': 'Central Park, NY, NY',
         'description': "New York's friendly Central Park.",
         'exits': [
                {'name': 'portal',
                 'exits_to': 'necroplex'}]}]}


class TestMigrations(object):
    def setUp(self):
        # Set up the connection, drop an existing possible database
        self.connection = Connection()
        self.connection.drop_database(MIGRATION_DB_NAME)
        self.db = Connection()[MIGRATION_DB_NAME]
        self.migration_manager = MigrationManager(
            self.db, TEST_MIGRATION_REGISTRY)
        self.empty_migration_manager = MigrationManager(
            self.db, TEST_EMPTY_MIGRATION_REGISTRY)
        self.run_migrations = []

    def tearDown(self):
        self.connection.drop_database(MIGRATION_DB_NAME)

    def _record_migration(self, migration_number, migration_func):
        self.run_migrations.append((migration_number, migration_func))

    def test_migrations_registered_and_sorted(self):
        """
        Make sure that migrations get registered and are sorted right
        in the migration manager
        """
        assert TEST_MIGRATION_REGISTRY == {
            1: creature_add_magical_powers,
            2: creature_rename_num_legs_to_num_limbs,
            3: creature_remove_is_demon,
            4: level_exits_dict_to_list}
        assert self.migration_manager.sorted_migrations == [
            (1, creature_add_magical_powers),
            (2, creature_rename_num_legs_to_num_limbs),
            (3, creature_remove_is_demon),
            (4, level_exits_dict_to_list)]
        assert self.empty_migration_manager.sorted_migrations == []

    def test_run_full_migrations(self):
        """
        Make sure that running the full migration suite from 0 updates
        everything
        """
        self.migration_manager.set_current_migration(0)
        assert self.migration_manager.database_current_migration() == 0
        install_fixtures_simple(self.db, UNMIGRATED_DBDATA)
        self.migration_manager.migrate_new(post_callback=self._record_migration)

        assert self.run_migrations == [
            (1, creature_add_magical_powers),
            (2, creature_rename_num_legs_to_num_limbs),
            (3, creature_remove_is_demon),
            (4, level_exits_dict_to_list)]

        assert_db_meets_expected(
            self.db, EXPECTED_POST_MIGRATION_UNMIGRATED_DBDATA)

        # Make sure the migration is recorded correctly
        assert self.migration_manager.database_current_migration() == 4

        # run twice!  It should do nothing the second time.
        # ------------------------------------------------
        self.run_migrations = []
        self.migration_manager.migrate_new(post_callback=self._record_migration)
        assert self.run_migrations == []
        assert_db_meets_expected(
            self.db, EXPECTED_POST_MIGRATION_UNMIGRATED_DBDATA)
        assert self.migration_manager.database_current_migration() == 4


    def test_run_partial_migrations(self):
        """
        Make sure that running full migration suite from 3 only runs
        last migration
        """
        self.migration_manager.set_current_migration(3)
        assert self.migration_manager.database_current_migration() == 3
        install_fixtures_simple(self.db, SEMI_MIGRATED_DBDATA)
        self.migration_manager.migrate_new(post_callback=self._record_migration)

        assert self.run_migrations == [
            (4, level_exits_dict_to_list)]

        assert_db_meets_expected(
            self.db, EXPECTED_POST_MIGRATION_SEMI_MIGRATED_DBDATA)

        # Make sure the migration is recorded correctly
        assert self.migration_manager.database_current_migration() == 4

    def test_migrations_recorded_as_latest(self):
        """
        Make sure that if we don't have a migration_status
        pre-recorded it's marked as the latest
        """
        self.migration_manager.install_migration_version_if_missing()
        assert self.migration_manager.database_current_migration() == 4

    def test_no_migrations_recorded_as_zero(self):
        """
        Make sure that if we don't have a migration_status
        but there *are* no migrations that it's marked as 0
        """
        self.empty_migration_manager.install_migration_version_if_missing()
        assert self.empty_migration_manager.database_current_migration() == 0

    def test_migrations_to_run(self):
        """
        Make sure we get the right list of migrations to run
        """
        self.migration_manager.set_current_migration(0)

        assert self.migration_manager.migrations_to_run() == [
            (1, creature_add_magical_powers),
            (2, creature_rename_num_legs_to_num_limbs),
            (3, creature_remove_is_demon),
            (4, level_exits_dict_to_list)]

        self.migration_manager.set_current_migration(3)

        assert self.migration_manager.migrations_to_run() == [
            (4, level_exits_dict_to_list)]

        self.migration_manager.set_current_migration(4)

        assert self.migration_manager.migrations_to_run() == []


    def test_no_migrations_raises_exception(self):
        """
        If we don't have the current migration set in the database,
        this should error out.
        """
        assert_raises(
            MissingCurrentMigration,
            self.migration_manager.migrations_to_run)
