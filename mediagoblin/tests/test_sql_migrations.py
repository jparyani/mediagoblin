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
    Table, Column, MetaData, Index
    Integer, Float, Unicode, UnicodeText, DateTime, Boolean,
    ForeignKey, UniqueConstraint, PickleType)
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select, insert
from migrate import changeset

from mediagoblin.db.sql.base import GMGTableBase


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
    name = Column(Unicode, unique=True, nullable=False, index=True)
    description = Column(UnicodeText)
    exits = Column(PickleType)

SET1_MODELS = [Creature1, Level1]

SET1_MIGRATIONS = []

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
    description = Column(UnicodeText)

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
    metadata = MetaData(bind=db_conn.engine)
    creature_table = Table(
        'creature', metadata,
        autoload=True, autoload_with=db_conn.engine)
    creature_table.drop_column('is_demon')
    

@RegisterMigration(2, FULL_MIGRATIONS)
def creature_powers_new_table(db_conn):
    """
    Add a new table for creature powers.  Nothing needs to go in it
    yet though as there wasn't anything that previously held this
    information
    """
    metadata = MetaData(bind=db_conn.engine)
    creature_powers = Table(
        'creature_power', metadata,
        Column('id', Integer, primary_key=True),
        Column('creature', 
               Integer, ForeignKey('creature.id'), nullable=False),
        Column('name', Unicode),
        Column('description', Unicode),
        Column('hitpower', Integer, nullable=False))
    metadata.create_all(db_conn.engine)


@RegisterMigration(3, FULL_MIGRATIONS)
def level_exits_new_table(db_conn):
    """
    Make a new table for level exits and move the previously pickled
    stuff over to here (then drop the old unneeded table)
    """
    # First, create the table
    # -----------------------
    metadata = MetaData(bind=db_conn.engine)
    level_exits = Table(
        'level_exit', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', Unicode),
        Column('from_level',
               Integer, ForeignKey('level.id'), nullable=False),
        Column('to_level',
               Integer, ForeignKey('level.id'), nullable=False))
    metadata.create_all(db_conn.engine)

    # And now, convert all the old exit pickles to new level exits
    # ------------------------------------------------------------

    # Minimal representation of level table.
    # Not auto-introspecting here because of pickle table.  I'm not
    # sure sqlalchemy can auto-introspect pickle columns.
    levels = Table(
        'level', metadata,
        Column('id', Integer, primary_key=True),
        Column('exits', PickleType))

    # query over and insert
    result = db_conn.execute(
        select([levels], levels.c.exits!=None))

    for level in result:
        this_exit = level['exits']
        
        # Insert the level exit
        db_conn.execute(
            level_exits.insert().values(
                name=this_exit['name'],
                from_level=this_exit['from_level'],
                to_level=this_exit['to_level']))

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

class CreaturePower3(Base3):
    __tablename__ = "creature_power"

    id = Column(Integer, primary_key=True)
    creature = Column(
        Integer, ForeignKey('creature.id'), nullable=False, index=True)
    name = Column(Unicode)
    description = Column(Unicode)
    hitpower = Column(Float, nullable=False)
    magical_powers = relationship("CreaturePower3")

class Level3(Base3):
    __tablename__ = "level"

    id = Column(Unicode, primary_key=True)
    name = Column(Unicode)
    description = Column(UnicodeText)

class LevelExit3(Base3):
    __tablename__ = "level_exit"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    from_level = Column(
        Unicode, ForeignKey('level.id'), nullable=False, index=True)
    to_level = Column(
        Unicode, ForeignKey('level.id'), nullable=False, index=True)


SET3_MODELS = [Creature3, CreaturePower3, Level3, LevelExit3]


@RegisterMigration(4, FULL_MIGRATIONS)
def creature_num_legs_to_num_limbs(db_conn):
    """
    Turns out we're tracking all sorts of limbs, not "legs"
    specifically.  Humans would be 4 here, for instance.  So we
    renamed the column.
    """
    metadata = MetaData(bind=db_conn.engine)
    creature_table = Table(
        'creature', metadata,
        autoload=True, autoload_with=db_conn.engine)
    creature_table.c.num_legs.alter(name="num_limbs")


@RegisterMigration(5, FULL_MIGRATIONS)
def level_exit_index_from_and_to_level(db_conn):
    """
    Index the from and to levels of the level exit table.
    """
    metadata = MetaData(bind=db_conn.engine)
    level_exit = Table(
        'level_exit', metadata,
        autoload=True, autoload_with=db_conn.engine)
    Index('ix_from_level', level_exit.c.from_level).create(engine)
    Index('ix_to_exit', level_exit.c.to_exit).create(engine)


@RegisterMigration(6, FULL_MIGRATIONS)
def creature_power_index_creature(db_conn):
    """
    Index our foreign key relationship to the creatures
    """
    metadata = MetaData(bind=db_conn.engine)
    creature_power = Table(
        'creature_power', metadata,
        autoload=True, autoload_with=db_conn.engine)
    Index('ix_creature', creature_power.c.creature).create(engine)


@RegisterMigration(7, FULL_MIGRATIONS)
def creature_power_hitpower_to_float(db_conn):
    """
    Convert hitpower column on creature power table from integer to
    float.

    Turns out we want super precise values of how much hitpower there
    really is.
    """
    metadata = MetaData(bind=db_conn.engine)
    creature_power = Table(
        'creature_power', metadata,
        autoload=True, autoload_with=db_conn.engine)
    creature_power.c.hitpower.alter(type=Float)


def _insert_migration1_objects(session):
    """
    Test objects to insert for the first set of things
    """
    # Insert creatures
    session.add_all(
        [Creature1(name='centipede',
                   num_legs=100,
                   is_demon=False),
         Creature1(name='wolf',
                   num_legs=4,
                   is_demon=False),
         # don't ask me what a wizardsnake is.
         Creature1(name='wizardsnake',
                   num_legs=0,
                   is_demon=True)])

    # Insert levels
    session.add_all(
        [Level1(id='necroplex',
                name='The Necroplex',
                description='A complex full of pure deathzone.',
                exits={
                    'deathwell': 'evilstorm',
                    'portal': 'central_park'}),
         Level1(id='evilstorm',
                name='Evil Storm',
                description='A storm full of pure evil.',
                exits={}), # you can't escape the evilstorm
         Level1(id='central_park'
                name='Central Park, NY, NY',
                description="New York's friendly Central Park.",
                exits={
                    'portal': 'necroplex'})])

    session.commit()


def _insert_migration2_objects(session):
    """
    Test objects to insert for the second set of things
    """
    # Insert creatures
    session.add_all(
        [Creature2(
                name='centipede',
                num_legs=100),
         Creature2(
                name='wolf',
                num_legs=4,
                magical_powers = [
                    CreaturePower2(
                        name="ice breath",
                        description="A blast of icy breath!",
                        hitpower=20),
                    CreaturePower2(
                        name="death stare",
                        description="A frightening stare, for sure!",
                        hitpower=45)]),
         Creature2(
                name='wizardsnake',
                num_legs=0,
                magical_powers=[
                    CreaturePower2(
                        name='death_rattle',
                        description='A rattle... of DEATH!',
                        hitpower=1000),
                    CreaturePower2(
                        name='sneaky_stare',
                        description="The sneakiest stare you've ever seen!"
                        hitpower=300),
                    CreaturePower2(
                        name='slithery_smoke',
                        description="A blast of slithery, slithery smoke.",
                        hitpower=10),
                    CreaturePower2(
                        name='treacherous_tremors',
                        description="The ground shakes beneath footed animals!",
                        hitpower=0)])])

    # Insert levels
    session.add_all(
        [Level2(id='necroplex',
                name='The Necroplex',
                description='A complex full of pure deathzone.'),
         Level2(id='evilstorm',
                name='Evil Storm',
                description='A storm full of pure evil.',
                exits=[]), # you can't escape the evilstorm
         Level2(id='central_park'
                name='Central Park, NY, NY',
                description="New York's friendly Central Park.")])

    # necroplex exits
    session.add_all(
        [LevelExit2(name='deathwell',
                    from_level='necroplex',
                    to_level='evilstorm'),
         LevelExit2(name='portal',
                    from_level='necroplex',
                    to_level='central_park')])

    # there are no evilstorm exits because there is no exit from the
    # evilstorm
      
    # central park exits
    session.add_all(
        [LevelExit2(name='portal',
                    from_level='central_park',
                    to_level='necroplex')])

    session.commit()


def _insert_migration3_objects(session):
    """
    Test objects to insert for the third set of things
    """
    # Insert creatures
    session.add_all(
        [Creature3(
                name='centipede',
                num_limbs=100),
         Creature3(
                name='wolf',
                num_limbs=4,
                magical_powers = [
                    CreaturePower3(
                        name="ice breath",
                        description="A blast of icy breath!",
                        hitpower=20.0),
                    CreaturePower3(
                        name="death stare",
                        description="A frightening stare, for sure!",
                        hitpower=45.0)]),
         Creature3(
                name='wizardsnake',
                num_limbs=0,
                magical_powers=[
                    CreaturePower3(
                        name='death_rattle',
                        description='A rattle... of DEATH!',
                        hitpower=1000.0),
                    CreaturePower3(
                        name='sneaky_stare',
                        description="The sneakiest stare you've ever seen!"
                        hitpower=300.0),
                    CreaturePower3(
                        name='slithery_smoke',
                        description="A blast of slithery, slithery smoke.",
                        hitpower=10.0),
                    CreaturePower3(
                        name='treacherous_tremors',
                        description="The ground shakes beneath footed animals!",
                        hitpower=0.0)])],
        # annnnnd one more to test a floating point hitpower
        Creature3(
                name='deity',
                numb_limbs=30,
                magical_powers[
                    CreaturePower3(
                        name='smite',
                        description='Smitten by holy wrath!',
                        hitpower=9999.9))))

    # Insert levels
    session.add_all(
        [Level3(id='necroplex',
                name='The Necroplex',
                description='A complex full of pure deathzone.'),
         Level3(id='evilstorm',
                name='Evil Storm',
                description='A storm full of pure evil.',
                exits=[]), # you can't escape the evilstorm
         Level3(id='central_park'
                name='Central Park, NY, NY',
                description="New York's friendly Central Park.")])

    # necroplex exits
    session.add_all(
        [LevelExit3(name='deathwell',
                    from_level='necroplex',
                    to_level='evilstorm'),
         LevelExit3(name='portal',
                    from_level='necroplex',
                    to_level='central_park')])

    # there are no evilstorm exits because there is no exit from the
    # evilstorm
      
    # central park exits
    session.add_all(
        [LevelExit3(name='portal',
                    from_level='central_park',
                    to_level='necroplex')])

    session.commit()


def create_test_engine():
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:', echo=False)
    return engine


def test_set1_to_set3():
    # Create / connect to database
    # Create tables by migrating on empty initial set

    # Install the initial set
    # Check version in database
    # Sanity check a few things in the database

    # Migrate
    # Make sure version matches expected
    # Check all things in database match expected
    pass


def test_set2_to_set3():
    # Create / connect to database
    # Create tables by migrating on empty initial set

    # Install the initial set
    # Check version in database
    # Sanity check a few things in the database

    # Migrate
    # Make sure version matches expected
    # Check all things in database match expected
    pass


def test_set1_to_set2_to_set3():
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
    pass
