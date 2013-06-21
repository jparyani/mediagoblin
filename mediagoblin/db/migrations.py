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

import datetime
import uuid

from sqlalchemy import (MetaData, Table, Column, Boolean, SmallInteger,
                        Integer, Unicode, UnicodeText, DateTime,
                        ForeignKey)
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import and_
from migrate.changeset.constraint import UniqueConstraint

from mediagoblin.db.migration_tools import RegisterMigration, inspect_table
from mediagoblin.db.models import MediaEntry, Collection, User

MIGRATIONS = {}


@RegisterMigration(1, MIGRATIONS)
def ogg_to_webm_audio(db_conn):
    metadata = MetaData(bind=db_conn.bind)

    file_keynames = Table('core__file_keynames', metadata, autoload=True,
                          autoload_with=db_conn.bind)

    db_conn.execute(
        file_keynames.update().where(file_keynames.c.name == 'ogg').
            values(name='webm_audio')
    )
    db_conn.commit()


@RegisterMigration(2, MIGRATIONS)
def add_wants_notification_column(db_conn):
    metadata = MetaData(bind=db_conn.bind)

    users = Table('core__users', metadata, autoload=True,
            autoload_with=db_conn.bind)

    col = Column('wants_comment_notification', Boolean,
            default=True, nullable=True)
    col.create(users, populate_defaults=True)
    db_conn.commit()


@RegisterMigration(3, MIGRATIONS)
def add_transcoding_progress(db_conn):
    metadata = MetaData(bind=db_conn.bind)

    media_entry = inspect_table(metadata, 'core__media_entries')

    col = Column('transcoding_progress', SmallInteger)
    col.create(media_entry)
    db_conn.commit()


class Collection_v0(declarative_base()):
    __tablename__ = "core__collections"

    id = Column(Integer, primary_key=True)
    title = Column(Unicode, nullable=False)
    slug = Column(Unicode)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now,
        index=True)
    description = Column(UnicodeText)
    creator = Column(Integer, ForeignKey(User.id), nullable=False)
    items = Column(Integer, default=0)

class CollectionItem_v0(declarative_base()):
    __tablename__ = "core__collection_items"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id), nullable=False, index=True)
    collection = Column(Integer, ForeignKey(Collection.id), nullable=False)
    note = Column(UnicodeText, nullable=True)
    added = Column(DateTime, nullable=False, default=datetime.datetime.now)
    position = Column(Integer)

    ## This should be activated, normally.
    ## But this would change the way the next migration used to work.
    ## So it's commented for now.
    __table_args__ = (
        UniqueConstraint('collection', 'media_entry'),
        {})

collectionitem_unique_constraint_done = False

@RegisterMigration(4, MIGRATIONS)
def add_collection_tables(db_conn):
    Collection_v0.__table__.create(db_conn.bind)
    CollectionItem_v0.__table__.create(db_conn.bind)

    global collectionitem_unique_constraint_done
    collectionitem_unique_constraint_done = True

    db_conn.commit()


@RegisterMigration(5, MIGRATIONS)
def add_mediaentry_collected(db_conn):
    metadata = MetaData(bind=db_conn.bind)

    media_entry = inspect_table(metadata, 'core__media_entries')

    col = Column('collected', Integer, default=0)
    col.create(media_entry)
    db_conn.commit()


class ProcessingMetaData_v0(declarative_base()):
    __tablename__ = 'core__processing_metadata'

    id = Column(Integer, primary_key=True)
    media_entry_id = Column(Integer, ForeignKey(MediaEntry.id), nullable=False,
            index=True)
    callback_url = Column(Unicode)

@RegisterMigration(6, MIGRATIONS)
def create_processing_metadata_table(db):
    ProcessingMetaData_v0.__table__.create(db.bind)
    db.commit()


# Okay, problem being:
#  Migration #4 forgot to add the uniqueconstraint for the
#  new tables. While creating the tables from scratch had
#  the constraint enabled.
#
# So we have four situations that should end up at the same
# db layout:
#
# 1. Fresh install.
#    Well, easy. Just uses the tables in models.py
# 2. Fresh install using a git version just before this migration
#    The tables are all there, the unique constraint is also there.
#    This migration should do nothing.
#    But as we can't detect the uniqueconstraint easily,
#    this migration just adds the constraint again.
#    And possibly fails very loud. But ignores the failure.
# 3. old install, not using git, just releases.
#    This one will get the new tables in #4 (now with constraint!)
#    And this migration is just skipped silently.
# 4. old install, always on latest git.
#    This one has the tables, but lacks the constraint.
#    So this migration adds the constraint.
@RegisterMigration(7, MIGRATIONS)
def fix_CollectionItem_v0_constraint(db_conn):
    """Add the forgotten Constraint on CollectionItem"""

    global collectionitem_unique_constraint_done
    if collectionitem_unique_constraint_done:
        # Reset it. Maybe the whole thing gets run again
        # For a different db?
        collectionitem_unique_constraint_done = False
        return

    metadata = MetaData(bind=db_conn.bind)

    CollectionItem_table = inspect_table(metadata, 'core__collection_items')

    constraint = UniqueConstraint('collection', 'media_entry',
        name='core__collection_items_collection_media_entry_key',
        table=CollectionItem_table)

    try:
        constraint.create()
    except ProgrammingError:
        # User probably has an install that was run since the
        # collection tables were added, so we don't need to run this migration.
        pass

    db_conn.commit()


@RegisterMigration(8, MIGRATIONS)
def add_license_preference(db):
    metadata = MetaData(bind=db.bind)

    user_table = inspect_table(metadata, 'core__users')

    col = Column('license_preference', Unicode)
    col.create(user_table)
    db.commit()


@RegisterMigration(9, MIGRATIONS)
def mediaentry_new_slug_era(db):
    """
    Update for the new era for media type slugs.

    Entries without slugs now display differently in the url like:
      /u/cwebber/m/id=251/

    ... because of this, we should back-convert:
     - entries without slugs should be converted to use the id, if possible, to
       make old urls still work
     - slugs with = (or also : which is now also not allowed) to have those
       stripped out (small possibility of breakage here sadly)
    """

    def slug_and_user_combo_exists(slug, uploader):
        return db.execute(
            media_table.select(
                and_(media_table.c.uploader==uploader,
                     media_table.c.slug==slug))).first() is not None

    def append_garbage_till_unique(row, new_slug):
        """
        Attach junk to this row until it's unique, then save it
        """
        if slug_and_user_combo_exists(new_slug, row.uploader):
            # okay, still no success;
            # let's whack junk on there till it's unique.
            new_slug += '-' + uuid.uuid4().hex[:4]
            # keep going if necessary!
            while slug_and_user_combo_exists(new_slug, row.uploader):
                new_slug += uuid.uuid4().hex[:4]

        db.execute(
            media_table.update(). \
            where(media_table.c.id==row.id). \
            values(slug=new_slug))

    metadata = MetaData(bind=db.bind)

    media_table = inspect_table(metadata, 'core__media_entries')

    for row in db.execute(media_table.select()):
        # no slug, try setting to an id
        if not row.slug:
            append_garbage_till_unique(row, unicode(row.id))
        # has "=" or ":" in it... we're getting rid of those
        elif u"=" in row.slug or u":" in row.slug:
            append_garbage_till_unique(
                row, row.slug.replace(u"=", u"-").replace(u":", u"-"))

    db.commit()


@RegisterMigration(10, MIGRATIONS)
def unique_collections_slug(db):
    """Add unique constraint to collection slug"""
    metadata = MetaData(bind=db.bind)
    collection_table = inspect_table(metadata, "core__collections")
    existing_slugs = {}
    slugs_to_change = []

    for row in db.execute(collection_table.select()):
        # if duplicate slug, generate a unique slug
        if row.creator in existing_slugs and row.slug in \
           existing_slugs[row.creator]:
            slugs_to_change.append(row.id)
        else:
            if not row.creator in existing_slugs:
                existing_slugs[row.creator] = [row.slug]
            else:
                existing_slugs[row.creator].append(row.slug)

    for row_id in slugs_to_change:
        new_slug = unicode(uuid.uuid4())
        db.execute(collection_table.update().
                   where(collection_table.c.id == row_id).
                   values(slug=new_slug))
    # sqlite does not like to change the schema when a transaction(update) is
    # not yet completed
    db.commit()

    constraint = UniqueConstraint('creator', 'slug',
                                  name='core__collection_creator_slug_key',
                                  table=collection_table)
    constraint.create()

    db.commit()
