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


from pymongo import Connection

from mediagoblin.tests.tools import install_fixtures_simple
from mediagoblin.db.util import RegisterMigration, MigrationManager

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
    magical powers, all existing monsters should 
    """
    database['creatures'].update(
        {'magical_powers': {'$exists': False}},
        {'$set': {'magical_powers': []}})


@RegisterMigration(2, TEST_MIGRATION_REGISTRY)
def creature_rename_num_legs_to_num_limbs(database):
    """
    It turns out we want to track how many limbs a creature has, not
    just how many legs.  We don't care about the ambiguous distinction
    between arms/legs currently.
    """
    database['creatures'].update(
        {'num_legs': {'$exists': True}},
        {'$rename': {'num_legs': 'num_limbs'}})


@RegisterMigration(3, TEST_MIGRATION_REGISTRY)
def creature_remove_is_demon(database):
    """
    It turns out we don't care much about whether creatures are demons
    or not.
    """
    database['creatures'].update(
        {'is_demon': {'$exists': True}},
        {'$unset': {'is_demon': 1}})


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
    target = database['levels'].find(
        {'exits': {'$type': 3}})

    for level in target:
        new_exits = []
        for exit_name, exits_to in level['exits'].items():
            new_exits.append(
                {'name': exit_name,
                 'exits_to': exits_to})

        level['exits'] = new_exits
        database['levels'].save(level)


UNMIGRATED_DBDATA = {
    'creatures': [
        {'name': 'centipede',
         'num_legs': 100,
         'is_demon': False},
        {'name': 'wolf',
         'num_legs': 4,
         'is_demon': False},
        # don't ask me what a wizardsnake is.
        {'name': 'wizardsnake',
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
                    

# We want to make sure that if we're at migration 3, migration 3
# doesn't get re-run.

SEMI_MIGRATED_DBDATA = {
    'creatures': [
        {'name': 'centipede',
         'num_limbs': 100,
         'magical_powers': []},
        {'name': 'wolf',
         'num_limbs': 4,
         # kept around namely to check that it *isn't* removed!
         'is_demon': False,
         'magical_powers': [
                'ice_breath', 'death_stare']},
        {'name': 'wizardsnake',
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

    def tearDown(self):
        self.connection.drop_database(MIGRATION_DB_NAME)

