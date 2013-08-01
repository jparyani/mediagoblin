# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2012, 2012 MediaGoblin contributors.  See AUTHORS.
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

import copy

from sqlalchemy import (
    Table, Column, MetaData, Index,
    Integer, Float, Unicode, UnicodeText, DateTime, Boolean,
    ForeignKey, UniqueConstraint, PickleType, VARCHAR)
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select, insert
from migrate import changeset

from mediagoblin.db.base import GMGTableBase
from mediagoblin.db.migration_tools import MigrationManager, RegisterMigration
from mediagoblin.tools.common import CollectingPrinter


# This one will get filled with local migrations
FULL_MIGRATIONS = {}


#######################################################
# Migration set 1: Define initial models, no migrations
#######################################################

Base1 = declarative_base(cls=GMGTableBase)

class Creature1(Base1):
    __tablename__ = "creature"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True, nullable=False, index=True)
    num_legs = Column(Integer, nullable=False)
    is_demon = Column(Boolean)

class Level1(Base1):
    __tablename__ = "level"

    id = Column(Unicode, primary_key=True)
    name = Column(Unicode)
    description = Column(Unicode)
    exits = Column(PickleType)

SET1_MODELS = [Creature1, Level1]

FOUNDATIONS = {Creature1:[{'name':u'goblin','num_legs':2,'is_demon':False},
                          {'name':u'cerberus','num_legs':4,'is_demon':True}]
              }

SET1_MIGRATIONS = {}

#######################################################
# Migration set 2: A few migrations and new model
#######################################################

Base2 = declarative_base(cls=GMGTableBase)

class Creature2(Base2):
    __tablename__ = "creature"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True, nullable=False, index=True)
    num_legs = Column(Integer, nullable=False)
    magical_powers = relationship("CreaturePower2")

class CreaturePower2(Base2):
    __tablename__ = "creature_power"

    id = Column(Integer, primary_key=True)
    creature = Column(
        Integer, ForeignKey('creature.id'), nullable=False)
    name = Column(Unicode)
    description = Column(Unicode)
    hitpower = Column(Integer, nullable=False)

class Level2(Base2):
    __tablename__ = "level"

    id = Column(Unicode, primary_key=True)
    name = Column(Unicode)
    description = Column(Unicode)

class LevelExit2(Base2):
    __tablename__ = "level_exit"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    from_level = Column(
        Unicode, ForeignKey('level.id'), nullable=False)
    to_level = Column(
        Unicode, ForeignKey('level.id'), nullable=False)

SET2_MODELS = [Creature2, CreaturePower2, Level2, LevelExit2]


@RegisterMigration(1, FULL_MIGRATIONS)
def creature_remove_is_demon(db_conn):
    """
    Remove the is_demon field from the creature model.  We don't need
    it!
    """
    # :( Commented out 'cuz of:
    # http://code.google.com/p/sqlalchemy-migrate/issues/detail?id=143&thanks=143&ts=1327882242

    # metadata = MetaData(bind=db_conn.bind)
    # creature_table = Table(
    #     'creature', metadata,
    #     autoload=True, autoload_with=db_conn.bind)
    # creature_table.drop_column('is_demon')
    pass


@RegisterMigration(2, FULL_MIGRATIONS)
def creature_powers_new_table(db_conn):
    """
    Add a new table for creature powers.  Nothing needs to go in it
    yet though as there wasn't anything that previously held this
    information
    """
    metadata = MetaData(bind=db_conn.bind)

    # We have to access the creature table so sqlalchemy can make the
    # foreign key relationship
    creature_table = Table(
        'creature', metadata,
        autoload=True, autoload_with=db_conn.bind)

    creature_powers = Table(
        'creature_power', metadata,
        Column('id', Integer, primary_key=True),
        Column('creature', 
               Integer, ForeignKey('creature.id'), nullable=False),
        Column('name', Unicode),
        Column('description', Unicode),
        Column('hitpower', Integer, nullable=False))
    metadata.create_all(db_conn.bind)


@RegisterMigration(3, FULL_MIGRATIONS)
def level_exits_new_table(db_conn):
    """
    Make a new table for level exits and move the previously pickled
    stuff over to here (then drop the old unneeded table)
    """
    # First, create the table
    # -----------------------
    metadata = MetaData(bind=db_conn.bind)

    # Minimal representation of level table.
    # Not auto-introspecting here because of pickle table.  I'm not
    # sure sqlalchemy can auto-introspect pickle columns.
    levels = Table(
        'level', metadata,
        Column('id', Unicode, primary_key=True),
        Column('name', Unicode),
        Column('description', Unicode),
        Column('exits', PickleType))

    level_exits = Table(
        'level_exit', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', Unicode),
        Column('from_level',
               Unicode, ForeignKey('level.id'), nullable=False),
        Column('to_level',
               Unicode, ForeignKey('level.id'), nullable=False))
    metadata.create_all(db_conn.bind)

    # And now, convert all the old exit pickles to new level exits
    # ------------------------------------------------------------

    # query over and insert
    result = db_conn.execute(
        select([levels], levels.c.exits!=None))

    for level in result:

        for exit_name, to_level in level['exits'].iteritems():
            # Insert the level exit
            db_conn.execute(
                level_exits.insert().values(
                    name=exit_name,
                    from_level=level.id,
                    to_level=to_level))

    # Finally, drop the old level exits pickle table
    # ----------------------------------------------
    levels.drop_column('exits')    


# A hack!  At this point we freeze-fame and get just a partial list of
# migrations

SET2_MIGRATIONS = copy.copy(FULL_MIGRATIONS)

#######################################################
# Migration set 3: Final migrations
#######################################################

Base3 = declarative_base(cls=GMGTableBase)

class Creature3(Base3):
    __tablename__ = "creature"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True, nullable=False, index=True)
    num_limbs= Column(Integer, nullable=False)
    magical_powers = relationship("CreaturePower3")

class CreaturePower3(Base3):
    __tablename__ = "creature_power"

    id = Column(Integer, primary_key=True)
    creature = Column(
        Integer, ForeignKey('creature.id'), nullable=False, index=True)
    name = Column(Unicode)
    description = Column(Unicode)
    hitpower = Column(Float, nullable=False)

class Level3(Base3):
    __tablename__ = "level"

    id = Column(Unicode, primary_key=True)
    name = Column(Unicode)
    description = Column(Unicode)

class LevelExit3(Base3):
    __tablename__ = "level_exit"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    from_level = Column(
        Unicode, ForeignKey('level.id'), nullable=False, index=True)
    to_level = Column(
        Unicode, ForeignKey('level.id'), nullable=False, index=True)


SET3_MODELS = [Creature3, CreaturePower3, Level3, LevelExit3]
SET3_MIGRATIONS = FULL_MIGRATIONS


@RegisterMigration(4, FULL_MIGRATIONS)
def creature_num_legs_to_num_limbs(db_conn):
    """
    Turns out we're tracking all sorts of limbs, not "legs"
    specifically.  Humans would be 4 here, for instance.  So we
    renamed the column.
    """
    metadata = MetaData(bind=db_conn.bind)
    creature_table = Table(
        'creature', metadata,
        autoload=True, autoload_with=db_conn.bind)
    creature_table.c.num_legs.alter(name=u"num_limbs")


@RegisterMigration(5, FULL_MIGRATIONS)
def level_exit_index_from_and_to_level(db_conn):
    """
    Index the from and to levels of the level exit table.
    """
    metadata = MetaData(bind=db_conn.bind)
    level_exit = Table(
        'level_exit', metadata,
        autoload=True, autoload_with=db_conn.bind)
    Index('ix_level_exit_from_level',
          level_exit.c.from_level).create(db_conn.bind)
    Index('ix_level_exit_to_level',
          level_exit.c.to_level).create(db_conn.bind)


@RegisterMigration(6, FULL_MIGRATIONS)
def creature_power_index_creature(db_conn):
    """
    Index our foreign key relationship to the creatures
    """
    metadata = MetaData(bind=db_conn.bind)
    creature_power = Table(
        'creature_power', metadata,
        autoload=True, autoload_with=db_conn.bind)
    Index('ix_creature_power_creature',
          creature_power.c.creature).create(db_conn.bind)


@RegisterMigration(7, FULL_MIGRATIONS)
def creature_power_hitpower_to_float(db_conn):
    """
    Convert hitpower column on creature power table from integer to
    float.

    Turns out we want super precise values of how much hitpower there
    really is.
    """
    metadata = MetaData(bind=db_conn.bind)

    # We have to access the creature table so sqlalchemy can make the
    # foreign key relationship
    creature_table = Table(
        'creature', metadata,
        autoload=True, autoload_with=db_conn.bind)

    creature_power = Table(
        'creature_power', metadata,
        Column('id', Integer, primary_key=True),
        Column('creature', Integer,
               ForeignKey('creature.id'), nullable=False,
               index=True),
        Column('name', Unicode),
        Column('description', Unicode),
        Column('hitpower', Integer, nullable=False))

    creature_power.c.hitpower.alter(type=Float)


@RegisterMigration(8, FULL_MIGRATIONS)
def creature_power_name_creature_unique(db_conn):
    """
    Add a unique constraint to name and creature on creature_power.

    We don't want multiple creature powers with the same name per creature!
    """
    # Note: We don't actually check to see if this constraint is set
    # up because at present there's no way to do so in sqlalchemy :\

    metadata = MetaData(bind=db_conn.bind)

    creature_power = Table(
        'creature_power', metadata,
        autoload=True, autoload_with=db_conn.bind)
        
    cons = changeset.constraint.UniqueConstraint(
        'name', 'creature', table=creature_power)

    cons.create()


def _insert_migration1_objects(session):
    """
    Test objects to insert for the first set of things
    """
    # Insert creatures
    session.add_all(
        [Creature1(name=u'centipede',
                   num_legs=100,
                   is_demon=False),
         Creature1(name=u'wolf',
                   num_legs=4,
                   is_demon=False),
         # don't ask me what a wizardsnake is.
         Creature1(name=u'wizardsnake',
                   num_legs=0,
                   is_demon=True)])

    # Insert levels
    session.add_all(
        [Level1(id=u'necroplex',
                name=u'The Necroplex',
                description=u'A complex full of pure deathzone.',
                exits={
                    u'deathwell': u'evilstorm',
                    u'portal': u'central_park'}),
         Level1(id=u'evilstorm',
                name=u'Evil Storm',
                description=u'A storm full of pure evil.',
                exits={}), # you can't escape the evilstorm
         Level1(id=u'central_park',
                name=u'Central Park, NY, NY',
                description=u"New York's friendly Central Park.",
                exits={
                    u'portal': u'necroplex'})])

    session.commit()


def _insert_migration2_objects(session):
    """
    Test objects to insert for the second set of things
    """
    # Insert creatures
    session.add_all(
        [Creature2(
                name=u'centipede',
                num_legs=100),
         Creature2(
                name=u'wolf',
                num_legs=4,
                magical_powers = [
                    CreaturePower2(
                        name=u"ice breath",
                        description=u"A blast of icy breath!",
                        hitpower=20),
                    CreaturePower2(
                        name=u"death stare",
                        description=u"A frightening stare, for sure!",
                        hitpower=45)]),
         Creature2(
                name=u'wizardsnake',
                num_legs=0,
                magical_powers=[
                    CreaturePower2(
                        name=u'death_rattle',
                        description=u'A rattle... of DEATH!',
                        hitpower=1000),
                    CreaturePower2(
                        name=u'sneaky_stare',
                        description=u"The sneakiest stare you've ever seen!",
                        hitpower=300),
                    CreaturePower2(
                        name=u'slithery_smoke',
                        description=u"A blast of slithery, slithery smoke.",
                        hitpower=10),
                    CreaturePower2(
                        name=u'treacherous_tremors',
                        description=u"The ground shakes beneath footed animals!",
                        hitpower=0)])])

    # Insert levels
    session.add_all(
        [Level2(id=u'necroplex',
                name=u'The Necroplex',
                description=u'A complex full of pure deathzone.'),
         Level2(id=u'evilstorm',
                name=u'Evil Storm',
                description=u'A storm full of pure evil.',
                exits=[]), # you can't escape the evilstorm
         Level2(id=u'central_park',
                name=u'Central Park, NY, NY',
                description=u"New York's friendly Central Park.")])

    # necroplex exits
    session.add_all(
        [LevelExit2(name=u'deathwell',
                    from_level=u'necroplex',
                    to_level=u'evilstorm'),
         LevelExit2(name=u'portal',
                    from_level=u'necroplex',
                    to_level=u'central_park')])

    # there are no evilstorm exits because there is no exit from the
    # evilstorm
      
    # central park exits
    session.add_all(
        [LevelExit2(name=u'portal',
                    from_level=u'central_park',
                    to_level=u'necroplex')])

    session.commit()


def _insert_migration3_objects(session):
    """
    Test objects to insert for the third set of things
    """
    # Insert creatures
    session.add_all(
        [Creature3(
                name=u'centipede',
                num_limbs=100),
         Creature3(
                name=u'wolf',
                num_limbs=4,
                magical_powers = [
                    CreaturePower3(
                        name=u"ice breath",
                        description=u"A blast of icy breath!",
                        hitpower=20.0),
                    CreaturePower3(
                        name=u"death stare",
                        description=u"A frightening stare, for sure!",
                        hitpower=45.0)]),
         Creature3(
                name=u'wizardsnake',
                num_limbs=0,
                magical_powers=[
                    CreaturePower3(
                        name=u'death_rattle',
                        description=u'A rattle... of DEATH!',
                        hitpower=1000.0),
                    CreaturePower3(
                        name=u'sneaky_stare',
                        description=u"The sneakiest stare you've ever seen!",
                        hitpower=300.0),
                    CreaturePower3(
                        name=u'slithery_smoke',
                        description=u"A blast of slithery, slithery smoke.",
                        hitpower=10.0),
                    CreaturePower3(
                        name=u'treacherous_tremors',
                        description=u"The ground shakes beneath footed animals!",
                        hitpower=0.0)])],
        # annnnnd one more to test a floating point hitpower
        Creature3(
                name=u'deity',
                numb_limbs=30,
                magical_powers=[
                    CreaturePower3(
                        name=u'smite',
                        description=u'Smitten by holy wrath!',
                        hitpower=9999.9)]))

    # Insert levels
    session.add_all(
        [Level3(id=u'necroplex',
                name=u'The Necroplex',
                description=u'A complex full of pure deathzone.'),
         Level3(id=u'evilstorm',
                name=u'Evil Storm',
                description=u'A storm full of pure evil.',
                exits=[]), # you can't escape the evilstorm
         Level3(id=u'central_park',
                name=u'Central Park, NY, NY',
                description=u"New York's friendly Central Park.")])

    # necroplex exits
    session.add_all(
        [LevelExit3(name=u'deathwell',
                    from_level=u'necroplex',
                    to_level=u'evilstorm'),
         LevelExit3(name=u'portal',
                    from_level=u'necroplex',
                    to_level=u'central_park')])

    # there are no evilstorm exits because there is no exit from the
    # evilstorm
      
    # central park exits
    session.add_all(
        [LevelExit3(name=u'portal',
                    from_level=u'central_park',
                    to_level=u'necroplex')])

    session.commit()

def create_test_engine():
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:', echo=False)
    Session = sessionmaker(bind=engine)
    return engine, Session


def assert_col_type(column, this_class):
    assert isinstance(column.type, this_class)


def _get_level3_exits(session, level):
    return dict(
        [(level_exit.name, level_exit.to_level)
         for level_exit in
         session.query(LevelExit3).filter_by(from_level=level.id)])


def test_set1_to_set3():
    # Create / connect to database
    # ----------------------------

    engine, Session = create_test_engine()

    # Create tables by migrating on empty initial set
    # -----------------------------------------------

    printer = CollectingPrinter()
    migration_manager = MigrationManager(
        u'__main__', SET1_MODELS, FOUNDATIONS, SET1_MIGRATIONS, Session(),
        printer)

    # Check latest migration and database current migration
    assert migration_manager.latest_migration == 0
    assert migration_manager.database_current_migration == None

    result = migration_manager.init_or_migrate()

    # Make sure output was "inited"
    assert result == u'inited'
    # Check output
    assert printer.combined_string == (
        "-> Initializing main mediagoblin tables... done.\n" + \
        "   + Laying foundations for Creature1 table\n"    )
    # Check version in database
    assert migration_manager.latest_migration == 0
    assert migration_manager.database_current_migration == 0


    # Install the initial set
    # -----------------------

    _insert_migration1_objects(Session())

    # Try to "re-migrate" with same manager settings... nothing should happen
    migration_manager = MigrationManager(
        u'__main__', SET1_MODELS, FOUNDATIONS, SET1_MIGRATIONS, 
        Session(), printer)
    assert migration_manager.init_or_migrate() == None

    # Check version in database
    assert migration_manager.latest_migration == 0
    assert migration_manager.database_current_migration == 0

    # Sanity check a few things in the database...
    metadata = MetaData(bind=engine)

    # Check the structure of the creature table
    creature_table = Table(
        'creature', metadata,
        autoload=True, autoload_with=engine)
    assert set(creature_table.c.keys()) == set(
        ['id', 'name', 'num_legs', 'is_demon'])
    assert_col_type(creature_table.c.id, Integer)
    assert_col_type(creature_table.c.name, VARCHAR)
    assert creature_table.c.name.nullable is False
    #assert creature_table.c.name.index is True
    #assert creature_table.c.name.unique is True
    assert_col_type(creature_table.c.num_legs, Integer)
    assert creature_table.c.num_legs.nullable is False
    assert_col_type(creature_table.c.is_demon, Boolean)

    # Check the structure of the level table
    level_table = Table(
        'level', metadata,
        autoload=True, autoload_with=engine)
    assert set(level_table.c.keys()) == set(
        ['id', 'name', 'description', 'exits'])
    assert_col_type(level_table.c.id, VARCHAR)
    assert level_table.c.id.primary_key is True
    assert_col_type(level_table.c.name, VARCHAR)
    assert_col_type(level_table.c.description, VARCHAR)
    # Skipping exits... Not sure if we can detect pickletype, not a
    # big deal regardless.

    # Now check to see if stuff seems to be in there.
    session = Session()

    # Check the creation of the foundation rows on the creature table
    creature = session.query(Creature1).filter_by(
        name=u'goblin').one()
    assert creature.num_legs == 2
    assert creature.is_demon == False

    creature = session.query(Creature1).filter_by(
        name=u'cerberus').one()
    assert creature.num_legs == 4
    assert creature.is_demon == True

    
    # Check the creation of the inserted rows on the creature and levels tables
  
    creature = session.query(Creature1).filter_by(
        name=u'centipede').one()
    assert creature.num_legs == 100
    assert creature.is_demon == False

    creature = session.query(Creature1).filter_by(
        name=u'wolf').one()
    assert creature.num_legs == 4
    assert creature.is_demon == False

    creature = session.query(Creature1).filter_by(
        name=u'wizardsnake').one()
    assert creature.num_legs == 0
    assert creature.is_demon == True

    level = session.query(Level1).filter_by(
        id=u'necroplex').one()
    assert level.name == u'The Necroplex'
    assert level.description == u'A complex full of pure deathzone.'
    assert level.exits == {
        'deathwell': 'evilstorm',
        'portal': 'central_park'}

    level = session.query(Level1).filter_by(
        id=u'evilstorm').one()
    assert level.name == u'Evil Storm'
    assert level.description == u'A storm full of pure evil.'
    assert level.exits == {}  # You still can't escape the evilstorm!

    level = session.query(Level1).filter_by(
        id=u'central_park').one()
    assert level.name == u'Central Park, NY, NY'
    assert level.description == u"New York's friendly Central Park."
    assert level.exits == {
        'portal': 'necroplex'}

    # Create new migration manager, but make sure the db migration
    # isn't said to be updated yet
    printer = CollectingPrinter()
    migration_manager = MigrationManager(
        u'__main__', SET3_MODELS, FOUNDATIONS, SET3_MIGRATIONS, Session(),
        printer)

    assert migration_manager.latest_migration == 8
    assert migration_manager.database_current_migration == 0

    # Migrate
    result = migration_manager.init_or_migrate()

    # Make sure result was "migrated"
    assert result == u'migrated'

    # TODO: Check output to user
    assert printer.combined_string == """\
-> Updating main mediagoblin tables:
   + Running migration 1, "creature_remove_is_demon"... done.
   + Running migration 2, "creature_powers_new_table"... done.
   + Running migration 3, "level_exits_new_table"... done.
   + Running migration 4, "creature_num_legs_to_num_limbs"... done.
   + Running migration 5, "level_exit_index_from_and_to_level"... done.
   + Running migration 6, "creature_power_index_creature"... done.
   + Running migration 7, "creature_power_hitpower_to_float"... done.
   + Running migration 8, "creature_power_name_creature_unique"... done.
"""
    
    # Make sure version matches expected
    migration_manager = MigrationManager(
        u'__main__', SET3_MODELS, FOUNDATIONS, SET3_MIGRATIONS, Session(),
        printer)
    assert migration_manager.latest_migration == 8
    assert migration_manager.database_current_migration == 8

    # Check all things in database match expected

    # Check the creature table
    metadata = MetaData(bind=engine)
    creature_table = Table(
        'creature', metadata,
        autoload=True, autoload_with=engine)
    # assert set(creature_table.c.keys()) == set(
    #     ['id', 'name', 'num_limbs'])
    assert set(creature_table.c.keys()) == set(
        [u'id', 'name', u'num_limbs', u'is_demon'])
    assert_col_type(creature_table.c.id, Integer)
    assert_col_type(creature_table.c.name, VARCHAR)
    assert creature_table.c.name.nullable is False
    #assert creature_table.c.name.index is True
    #assert creature_table.c.name.unique is True
    assert_col_type(creature_table.c.num_limbs, Integer)
    assert creature_table.c.num_limbs.nullable is False

    # Check the CreaturePower table
    creature_power_table = Table(
        'creature_power', metadata,
        autoload=True, autoload_with=engine)
    assert set(creature_power_table.c.keys()) == set(
        ['id', 'creature', 'name', 'description', 'hitpower'])
    assert_col_type(creature_power_table.c.id, Integer)
    assert_col_type(creature_power_table.c.creature, Integer)
    assert creature_power_table.c.creature.nullable is False
    assert_col_type(creature_power_table.c.name, VARCHAR)
    assert_col_type(creature_power_table.c.description, VARCHAR)
    assert_col_type(creature_power_table.c.hitpower, Float)
    assert creature_power_table.c.hitpower.nullable is False

    # Check the structure of the level table
    level_table = Table(
        'level', metadata,
        autoload=True, autoload_with=engine)
    assert set(level_table.c.keys()) == set(
        ['id', 'name', 'description'])
    assert_col_type(level_table.c.id, VARCHAR)
    assert level_table.c.id.primary_key is True
    assert_col_type(level_table.c.name, VARCHAR)
    assert_col_type(level_table.c.description, VARCHAR)

    # Check the structure of the level_exits table
    level_exit_table = Table(
        'level_exit', metadata,
        autoload=True, autoload_with=engine)
    assert set(level_exit_table.c.keys()) == set(
        ['id', 'name', 'from_level', 'to_level'])
    assert_col_type(level_exit_table.c.id, Integer)
    assert_col_type(level_exit_table.c.name, VARCHAR)
    assert_col_type(level_exit_table.c.from_level, VARCHAR)
    assert level_exit_table.c.from_level.nullable is False
    #assert level_exit_table.c.from_level.index is True
    assert_col_type(level_exit_table.c.to_level, VARCHAR)
    assert level_exit_table.c.to_level.nullable is False
    #assert level_exit_table.c.to_level.index is True

    # Now check to see if stuff seems to be in there.
    session = Session()


    # Start with making sure that the foundations did not run again
    assert session.query(Creature3).filter_by(
        name=u'goblin').count() == 1
    assert session.query(Creature3).filter_by(
        name=u'cerberus').count() == 1

    # Then make sure the models have been migrated correctly
    creature = session.query(Creature3).filter_by(
        name=u'centipede').one()
    assert creature.num_limbs == 100.0
    assert creature.magical_powers == []

    creature = session.query(Creature3).filter_by(
        name=u'wolf').one()
    assert creature.num_limbs == 4.0
    assert creature.magical_powers == []

    creature = session.query(Creature3).filter_by(
        name=u'wizardsnake').one()
    assert creature.num_limbs == 0.0
    assert creature.magical_powers == []

    level = session.query(Level3).filter_by(
        id=u'necroplex').one()
    assert level.name == u'The Necroplex'
    assert level.description == u'A complex full of pure deathzone.'
    level_exits = _get_level3_exits(session, level)
    assert level_exits == {
        u'deathwell': u'evilstorm',
        u'portal': u'central_park'}

    level = session.query(Level3).filter_by(
        id=u'evilstorm').one()
    assert level.name == u'Evil Storm'
    assert level.description == u'A storm full of pure evil.'
    level_exits = _get_level3_exits(session, level)
    assert level_exits == {}  # You still can't escape the evilstorm!

    level = session.query(Level3).filter_by(
        id=u'central_park').one()
    assert level.name == u'Central Park, NY, NY'
    assert level.description == u"New York's friendly Central Park."
    level_exits = _get_level3_exits(session, level)
    assert level_exits == {
        'portal': 'necroplex'}


#def test_set2_to_set3():
    # Create / connect to database
    # Create tables by migrating on empty initial set

    # Install the initial set
    # Check version in database
    # Sanity check a few things in the database

    # Migrate
    # Make sure version matches expected
    # Check all things in database match expected
    # pass


#def test_set1_to_set2_to_set3():
    # Create / connect to database
    # Create tables by migrating on empty initial set

    # Install the initial set
    # Check version in database
    # Sanity check a few things in the database

    # Migrate
    # Make sure version matches expected
    # Check all things in database match expected

    # Migrate again
    # Make sure version matches expected again
    # Check all things in database match expected again

    ##### Set2
    # creature_table = Table(
    #     'creature', metadata,
    #     autoload=True, autoload_with=db_conn.bind)
    # assert set(creature_table.c.keys()) == set(
    #     ['id', 'name', 'num_legs'])
    # assert_col_type(creature_table.c.id, Integer)
    # assert_col_type(creature_table.c.name, VARCHAR)
    # assert creature_table.c.name.nullable is False
    # assert creature_table.c.name.index is True
    # assert creature_table.c.name.unique is True
    # assert_col_type(creature_table.c.num_legs, Integer)
    # assert creature_table.c.num_legs.nullable is False

    # # Check the CreaturePower table
    # creature_power_table = Table(
    #     'creature_power', metadata,
    #     autoload=True, autoload_with=db_conn.bind)
    # assert set(creature_power_table.c.keys()) == set(
    #     ['id', 'creature', 'name', 'description', 'hitpower'])
    # assert_col_type(creature_power_table.c.id, Integer)
    # assert_col_type(creature_power_table.c.creature, Integer)
    # assert creature_power_table.c.creature.nullable is False
    # assert_col_type(creature_power_table.c.name, VARCHAR)
    # assert_col_type(creature_power_table.c.description, VARCHAR)
    # assert_col_type(creature_power_table.c.hitpower, Integer)
    # assert creature_power_table.c.hitpower.nullable is False

    # # Check the structure of the level table
    # level_table = Table(
    #     'level', metadata,
    #     autoload=True, autoload_with=db_conn.bind)
    # assert set(level_table.c.keys()) == set(
    #     ['id', 'name', 'description'])
    # assert_col_type(level_table.c.id, VARCHAR)
    # assert level_table.c.id.primary_key is True
    # assert_col_type(level_table.c.name, VARCHAR)
    # assert_col_type(level_table.c.description, VARCHAR)

    # # Check the structure of the level_exits table
    # level_exit_table = Table(
    #     'level_exit', metadata,
    #     autoload=True, autoload_with=db_conn.bind)
    # assert set(level_exit_table.c.keys()) == set(
    #     ['id', 'name', 'from_level', 'to_level'])
    # assert_col_type(level_exit_table.c.id, Integer)
    # assert_col_type(level_exit_table.c.name, VARCHAR)
    # assert_col_type(level_exit_table.c.from_level, VARCHAR)
    # assert level_exit_table.c.from_level.nullable is False
    # assert_col_type(level_exit_table.c.to_level, VARCHAR)

    # pass
