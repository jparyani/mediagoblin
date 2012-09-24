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

from sqlalchemy import (MetaData, Table, Column, Boolean, SmallInteger,
                        Integer, Unicode, UnicodeText, DateTime, ForeignKey)

from mediagoblin.db.sql.util import RegisterMigration
from mediagoblin.db.sql.models import MediaEntry, Collection, User, \
        ProcessingMetaData

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

    media_entry = Table('core__media_entries', metadata, autoload=True,
            autoload_with=db_conn.bind)

    col = Column('transcoding_progress', SmallInteger)
    col.create(media_entry)
    db_conn.commit()


@RegisterMigration(4, MIGRATIONS)
def add_collection_tables(db_conn):
    metadata = MetaData(bind=db_conn.bind)

    collection = Table('core__collections', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('title', Unicode, nullable=False),
                       Column('slug', Unicode),
                       Column('created', DateTime, nullable=False, default=datetime.datetime.now, index=True),
                       Column('description', UnicodeText),
                       Column('creator', Integer, ForeignKey(User.id), nullable=False),
                       Column('items', Integer, default=0))

    collection_item = Table('core__collection_items', metadata,
                            Column('id', Integer, primary_key=True),
                            Column('media_entry', Integer, ForeignKey(MediaEntry.id), nullable=False, index=True),
                            Column('collection', Integer, ForeignKey(Collection.id), nullable=False),
                            Column('note', UnicodeText, nullable=True),
                            Column('added', DateTime, nullable=False, default=datetime.datetime.now),
                            Column('position', Integer))

    collection.create()
    collection_item.create()

    db_conn.commit()


@RegisterMigration(5, MIGRATIONS)
def add_mediaentry_collected(db_conn):
    metadata = MetaData(bind=db_conn.bind)

    media_entry = Table('core__media_entries', metadata, autoload=True,
            autoload_with=db_conn.bind)

    col = Column('collected', Integer, default=0)
    col.create(media_entry)
    db_conn.commit()


@RegisterMigration(6, MIGRATIONS)
def create_processing_metadata_table(db):
    metadata = MetaData(bind=db.bind)

    metadata_table = Table('core__processing_metadata', metadata,
            Column('id', Integer, primary_key=True),
            Column('media_entry_id', Integer, ForeignKey(MediaEntry.id),
                nullable=False, index=True),
            Column('callback_url', Unicode))

    metadata_table.create()
    db.commit()
