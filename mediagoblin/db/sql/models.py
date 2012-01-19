# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011,2012 MediaGoblin contributors.  See AUTHORS.
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

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, Integer, Unicode, UnicodeText, DateTime, Boolean, ForeignKey,
    UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy

from mediagoblin.db.sql.extratypes import PathTupleWithSlashes
from mediagoblin.db.sql.base import GMGTableBase
from mediagoblin.db.mixin import UserMixin, MediaEntryMixin


Base = declarative_base(cls=GMGTableBase)


class SimpleFieldAlias(object):
    """An alias for any field"""
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def __get__(self, instance, cls):
        return getattr(instance, self.fieldname)

    def __set__(self, instance, val):
        setattr(instance, self.fieldname, val)


class User(Base, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(Unicode, nullable=False, unique=True)
    email = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    pw_hash = Column(Unicode, nullable=False)
    email_verified = Column(Boolean)
    status = Column(Unicode, default=u"needs_email_verification", nullable=False)
    verification_key = Column(Unicode)
    is_admin = Column(Boolean, default=False, nullable=False)
    url = Column(Unicode)
    bio = Column(UnicodeText)  # ??
    bio_html = Column(UnicodeText)  # ??
    fp_verification_key = Column(Unicode)
    fp_token_expire = Column(DateTime)

    ## TODO
    # plugin data would be in a separate model

    _id = SimpleFieldAlias("id")


class MediaEntry(Base, MediaEntryMixin):
    __tablename__ = "media_entries"

    id = Column(Integer, primary_key=True)
    uploader = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(Unicode, nullable=False)
    slug = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    description = Column(UnicodeText)  # ??
    description_html = Column(UnicodeText)  # ??
    media_type = Column(Unicode, nullable=False)
    state = Column(Unicode, nullable=False)  # or use sqlalchemy.types.Enum?

    fail_error = Column(Unicode)
    fail_metadata = Column(UnicodeText)

    queued_media_file = Column(PathTupleWithSlashes)

    queued_task_id = Column(Unicode)

    __table_args__ = (
        UniqueConstraint('uploader', 'slug'),
        {})

    get_uploader = relationship(User)

    media_files_helper = relationship("MediaFile",
        collection_class=attribute_mapped_collection("name"),
        cascade="all, delete-orphan"
        )
    media_files = association_proxy('media_files_helper', 'file_path',
        creator=lambda k, v: MediaFile(name=k, file_path=v)
        )

    ## TODO
    # media_data
    # attachment_files
    # fail_error


class MediaFile(Base):
    __tablename__ = "mediafiles"

    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id),
        nullable=False, primary_key=True)
    name = Column(Unicode, primary_key=True)
    file_path = Column(PathTupleWithSlashes)

    def __repr__(self):
        return "<MediaFile %s: %r>" % (self.name, self.file_path)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    slug = Column(Unicode, nullable=False, unique=True)


class MediaTag(Base):
    __tablename__ = "media_tags"

    id = Column(Integer, primary_key=True)
    tag = Column(Integer, ForeignKey('tags.id'), nullable=False)
    name = Column(Unicode)
    media_entry = Column(
        Integer, ForeignKey('media_entries.id'),
        nullable=False)
    # created = Column(DateTime, nullable=False, default=datetime.datetime.now)

    __table_args__ = (
        UniqueConstraint('tag', 'media_entry'),
        {})


class MediaComment(Base):
    __tablename__ = "media_comments"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey('media_entries.id'), nullable=False)
    author = Column(Integer, ForeignKey('users.id'), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    content = Column(UnicodeText, nullable=False)
    content_html = Column(UnicodeText)

    get_author = relationship(User)


def show_table_init():
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:', echo=True)

    Base.metadata.create_all(engine)


if __name__ == '__main__':
    show_table_init()
