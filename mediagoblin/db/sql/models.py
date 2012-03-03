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

"""
TODO: indexes on foreignkeys, where useful.
"""


import datetime

from sqlalchemy import (
    Column, Integer, Unicode, UnicodeText, DateTime, Boolean, ForeignKey,
    UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql.expression import desc
from sqlalchemy.ext.associationproxy import association_proxy

from mediagoblin.db.sql.extratypes import PathTupleWithSlashes, JSONEncoded
from mediagoblin.db.sql.base import Base, DictReadAttrProxy
from mediagoblin.db.mixin import UserMixin, MediaEntryMixin, MediaCommentMixin

# It's actually kind of annoying how sqlalchemy-migrate does this, if
# I understand it right, but whatever.  Anyway, don't remove this :P
# 
# We could do migration calls more manually instead of relying on
# this import-based meddling...
from migrate import changeset


class SimpleFieldAlias(object):
    """An alias for any field"""
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def __get__(self, instance, cls):
        return getattr(instance, self.fieldname)

    def __set__(self, instance, val):
        setattr(instance, self.fieldname, val)


class User(Base, UserMixin):
    """
    TODO: We should consider moving some rarely used fields
    into some sort of "shadow" table.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(Unicode, nullable=False, unique=True)
    email = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    pw_hash = Column(Unicode, nullable=False)
    email_verified = Column(Boolean, default=False)
    status = Column(Unicode, default=u"needs_email_verification", nullable=False)
    verification_key = Column(Unicode)
    is_admin = Column(Boolean, default=False, nullable=False)
    url = Column(Unicode)
    bio = Column(UnicodeText)  # ??
    fp_verification_key = Column(Unicode)
    fp_token_expire = Column(DateTime)

    ## TODO
    # plugin data would be in a separate model

    _id = SimpleFieldAlias("id")


class MediaEntry(Base, MediaEntryMixin):
    """
    TODO: Consider fetching the media_files using join
    """
    __tablename__ = "media_entries"

    id = Column(Integer, primary_key=True)
    uploader = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(Unicode, nullable=False)
    slug = Column(Unicode)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    description = Column(UnicodeText) # ??
    media_type = Column(Unicode, nullable=False)
    state = Column(Unicode, default=u'unprocessed', nullable=False)
        # or use sqlalchemy.types.Enum?
    license = Column(Unicode)

    fail_error = Column(Unicode)
    fail_metadata = Column(JSONEncoded)

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

    attachment_files_helper = relationship("MediaAttachmentFile",
        cascade="all, delete-orphan",
        order_by="MediaAttachmentFile.created"
        )
    attachment_files = association_proxy("attachment_files_helper", "dict_view",
        creator=lambda v: MediaAttachmentFile(
            name=v["name"], filepath=v["filepath"])
        )

    tags_helper = relationship("MediaTag",
        cascade="all, delete-orphan"
        )
    tags = association_proxy("tags_helper", "dict_view",
        creator=lambda v: MediaTag(name=v["name"], slug=v["slug"])
        )

    ## TODO
    # media_data
    # fail_error

    _id = SimpleFieldAlias("id")

    def get_comments(self, ascending=False):
        order_col = MediaComment.created
        if not ascending:
            order_col = desc(order_col)
        return MediaComment.query.filter_by(
            media_entry=self.id).order_by(order_col)

    def url_to_prev(self, urlgen):
        """get the next 'newer' entry by this user"""
        media = MediaEntry.query.filter(
            (MediaEntry.uploader == self.uploader)
            & (MediaEntry.state == 'processed')
            & (MediaEntry.id > self.id)).order_by(MediaEntry.id).first()

        if media is not None:
            return media.url_for_self(urlgen)

    def url_to_next(self, urlgen):
        """get the next 'older' entry by this user"""
        media = MediaEntry.query.filter(
            (MediaEntry.uploader == self.uploader)
            & (MediaEntry.state == 'processed')
            & (MediaEntry.id < self.id)).order_by(desc(MediaEntry.id)).first()

        if media is not None:
            return media.url_for_self(urlgen)

    @property
    def media_data(self):
        # TODO: Replace with proper code to read the correct table
        return {}

    def media_data_init(self, **kwargs):
        # TODO: Implement this
        pass


class MediaFile(Base):
    """
    TODO: Highly consider moving "name" into a new table.
    TODO: Consider preloading said table in software
    """
    __tablename__ = "mediafiles"

    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id),
        nullable=False, primary_key=True)
    name = Column(Unicode, primary_key=True)
    file_path = Column(PathTupleWithSlashes)

    def __repr__(self):
        return "<MediaFile %s: %r>" % (self.name, self.file_path)


class MediaAttachmentFile(Base):
    __tablename__ = "core__attachment_files"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id),
        nullable=False)
    name = Column(Unicode, nullable=False)
    filepath = Column(PathTupleWithSlashes)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)

    @property
    def dict_view(self):
        """A dict like view on this object"""
        return DictReadAttrProxy(self)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    slug = Column(Unicode, nullable=False, unique=True)

    def __repr__(self):
        return "<Tag %r: %r>" % (self.id, self.slug)

    @classmethod
    def find_or_new(cls, slug):
        t = cls.query.filter_by(slug=slug).first()
        if t is not None:
            return t
        return cls(slug=slug)


class MediaTag(Base):
    __tablename__ = "media_tags"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id),
        nullable=False)
    tag = Column(Integer, ForeignKey('tags.id'), nullable=False)
    name = Column(Unicode)
    # created = Column(DateTime, nullable=False, default=datetime.datetime.now)

    __table_args__ = (
        UniqueConstraint('tag', 'media_entry'),
        {})

    tag_helper = relationship(Tag)
    slug = association_proxy('tag_helper', 'slug',
        creator=Tag.find_or_new
        )

    def __init__(self, name=None, slug=None):
        Base.__init__(self)
        if name is not None:
            self.name = name
        if slug is not None:
            self.tag_helper = Tag.find_or_new(slug)

    @property
    def dict_view(self):
        """A dict like view on this object"""
        return DictReadAttrProxy(self)


class MediaComment(Base, MediaCommentMixin):
    __tablename__ = "media_comments"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey('media_entries.id'), nullable=False)
    author = Column(Integer, ForeignKey('users.id'), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    content = Column(UnicodeText, nullable=False)

    get_author = relationship(User)

    _id = SimpleFieldAlias("id")


MODELS = [
    User, MediaEntry, Tag, MediaTag, MediaComment]


######################################################
# Special, migrations-tracking table
#
# Not listed in MODELS because this is special and not
# really migrated, but used for migrations (for now)
######################################################

class MigrationData(Base):
    __tablename__ = "migrations"

    name = Column(Unicode, primary_key=True)
    version = Column(Integer, nullable=False, default=0)

######################################################


def show_table_init(engine_uri):
    if engine_uri is None:
        engine_uri = 'sqlite:///:memory:'
    from sqlalchemy import create_engine
    engine = create_engine(engine_uri, echo=True)

    Base.metadata.create_all(engine)


if __name__ == '__main__':
    from sys import argv
    print repr(argv)
    if len(argv) == 2:
        uri = argv[1]
    else:
        uri = None
    show_table_init(uri)
