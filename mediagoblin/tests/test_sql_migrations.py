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

import copy

from sqlalchemy import (
    Table, Column, MetaData,
    Integer, Unicode, UnicodeText, DateTime, Boolean, ForeignKey,
    UniqueConstraint, PickleType)
from sqlalchemy.ext.declarative import declarative_base
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

    id = Column(Integer, primary_key=True)
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

class CreaturePower2(Base2):
    __tablename__ = "creature_power"

    id = Column(Integer, primary_key=True)
    creature = Column(
        Integer, ForeignKey('creature.id'), nullable=False)
    name = Column(Unicode)
    description = Column(Unicode)

class Level2(Base2):
    __tablename__ = "level"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    description = Column(UnicodeText)

class LevelExit2(Base2):
    __tablename__ = "level_exit"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    from_level = Column(
        Integer, ForeignKey('level.id'), nullable=False)
    to_level = Column(
        Integer, ForeignKey('level.id'), nullable=False)

SET2_MODELS = [Creature2, CreaturePower2, Level2, LevelExit2]


@RegisterMigration(1, FULL_MIGRATIONS)
def creature_remove_is_demon(db_conn):
    creature_table = Table(
        'creature', MetaData(),
        autoload=True, autoload_with=db_conn.engine)
    db_conn.execute(
        creature_table.drop_column('is_demon'))
    

@RegisterMigration(2, FULL_MIGRATIONS)
def creature_powers_new_table(db_conn):
    pass

@RegisterMigration(3, FULL_MIGRATIONS)
def level_exits_new_table(db_conn):
    pass


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

class Level3(Base3):
    __tablename__ = "level"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    description = Column(UnicodeText)

class LevelExit3(Base3):
    __tablename__ = "level_exit"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    from_level = Column(
        Integer, ForeignKey('level.id'), nullable=False, index=True)
    to_level = Column(
        Integer, ForeignKey('level.id'), nullable=False, index=True)


SET3_MODELS = [Creature3, CreaturePower3, Level3, LevelExit3]


@RegisterMigration(4, FULL_MIGRATIONS)
def creature_num_legs_to_num_limbs(db_conn):
    pass

@RegisterMigration(5, FULL_MIGRATIONS)
def level_exit_index_from_and_to_level(db_conn):
    pass

@RegisterMigration(6, FULL_MIGRATIONS)
def creature_power_index_creature(db_conn):
    pass
