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

###########################################################################
# WHAT IS THIS FILE?
# ------------------
#
# Upon occasion, someone runs into this file and wonders why we have
# both a models.py and a models_v0.py.
#
# The short of it is: you can ignore this file.
#
# The long version is, in two parts:
#
#  - We used to use MongoDB, then we switched to SQL and SQLAlchemy.
#    We needed to convert peoples' databases; the script we had would
#    switch them to the first version right after Mongo, convert over
#    all their tables, then run any migrations that were added after.
#
#  - That script is now removed, but there is some discussion of
#    writing a test that would set us at the first SQL migration and
#    run everything after.  If we wrote that, this file would still be
#    useful.  But for now, it's legacy!
#
###########################################################################


import datetime
import sys

from sqlalchemy import (
    Column, Integer, Unicode, UnicodeText, DateTime, Boolean, ForeignKey,
    UniqueConstraint, PrimaryKeyConstraint, SmallInteger, Float)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.util import memoized_property

from mediagoblin.db.extratypes import PathTupleWithSlashes, JSONEncoded
from mediagoblin.db.base import GMGTableBase, Session


Base_v0 = declarative_base(cls=GMGTableBase)


class User(Base_v0):
    """
    TODO: We should consider moving some rarely used fields
    into some sort of "shadow" table.
    """
    __tablename__ = "core__users"

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


class MediaEntry(Base_v0):
    """
    TODO: Consider fetching the media_files using join
    """
    __tablename__ = "core__media_entries"

    id = Column(Integer, primary_key=True)
    uploader = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    title = Column(Unicode, nullable=False)
    slug = Column(Unicode)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now,
        index=True)
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

    attachment_files_helper = relationship("MediaAttachmentFile",
        cascade="all, delete-orphan",
        order_by="MediaAttachmentFile.created"
        )

    tags_helper = relationship("MediaTag",
        cascade="all, delete-orphan"
        )

    def media_data_init(self, **kwargs):
        """
        Initialize or update the contents of a media entry's media_data row
        """
        session = Session()

        media_data = session.query(self.media_data_table).filter_by(
            media_entry=self.id).first()

        # No media data, so actually add a new one
        if media_data is None:
            media_data = self.media_data_table(
                media_entry=self.id,
                **kwargs)
            session.add(media_data)
        # Update old media data
        else:
            for field, value in kwargs.iteritems():
                setattr(media_data, field, value)

    @memoized_property
    def media_data_table(self):
        # TODO: memoize this
        models_module = self.media_type + '.models'
        __import__(models_module)
        return sys.modules[models_module].DATA_MODEL


class FileKeynames(Base_v0):
    """
    keywords for various places.
    currently the MediaFile keys
    """
    __tablename__ = "core__file_keynames"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)

    def __repr__(self):
        return "<FileKeyname %r: %r>" % (self.id, self.name)

    @classmethod
    def find_or_new(cls, name):
        t = cls.query.filter_by(name=name).first()
        if t is not None:
            return t
        return cls(name=name)


class MediaFile(Base_v0):
    """
    TODO: Highly consider moving "name" into a new table.
    TODO: Consider preloading said table in software
    """
    __tablename__ = "core__mediafiles"

    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id),
        nullable=False)
    name_id = Column(SmallInteger, ForeignKey(FileKeynames.id), nullable=False)
    file_path = Column(PathTupleWithSlashes)

    __table_args__ = (
        PrimaryKeyConstraint('media_entry', 'name_id'),
        {})

    def __repr__(self):
        return "<MediaFile %s: %r>" % (self.name, self.file_path)

    name_helper = relationship(FileKeynames, lazy="joined", innerjoin=True)
    name = association_proxy('name_helper', 'name',
        creator=FileKeynames.find_or_new
        )


class MediaAttachmentFile(Base_v0):
    __tablename__ = "core__attachment_files"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id),
        nullable=False)
    name = Column(Unicode, nullable=False)
    filepath = Column(PathTupleWithSlashes)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)


class Tag(Base_v0):
    __tablename__ = "core__tags"

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


class MediaTag(Base_v0):
    __tablename__ = "core__media_tags"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id),
        nullable=False, index=True)
    tag = Column(Integer, ForeignKey(Tag.id), nullable=False, index=True)
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
        Base_v0.__init__(self)
        if name is not None:
            self.name = name
        if slug is not None:
            self.tag_helper = Tag.find_or_new(slug)


class MediaComment(Base_v0):
    __tablename__ = "core__media_comments"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id), nullable=False, index=True)
    author = Column(Integer, ForeignKey(User.id), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    content = Column(UnicodeText, nullable=False)

    get_author = relationship(User)


class ImageData(Base_v0):
    __tablename__ = "image__mediadata"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('core__media_entries.id'),
        primary_key=True)
    get_media_entry = relationship("MediaEntry",
        backref=backref("image__media_data", cascade="all, delete-orphan"))

    width = Column(Integer)
    height = Column(Integer)
    exif_all = Column(JSONEncoded)
    gps_longitude = Column(Float)
    gps_latitude = Column(Float)
    gps_altitude = Column(Float)
    gps_direction = Column(Float)


class VideoData(Base_v0):
    __tablename__ = "video__mediadata"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('core__media_entries.id'),
        primary_key=True)
    get_media_entry = relationship("MediaEntry",
        backref=backref("video__media_data", cascade="all, delete-orphan"))

    width = Column(SmallInteger)
    height = Column(SmallInteger)


class AsciiData(Base_v0):
    __tablename__ = "ascii__mediadata"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('core__media_entries.id'),
        primary_key=True)
    get_media_entry = relationship("MediaEntry",
        backref=backref("ascii__media_data", cascade="all, delete-orphan"))


class AudioData(Base_v0):
    __tablename__ = "audio__mediadata"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('core__media_entries.id'),
        primary_key=True)
    get_media_entry = relationship("MediaEntry",
        backref=backref("audio__media_data", cascade="all, delete-orphan"))


######################################################
# Special, migrations-tracking table
#
# Not listed in MODELS because this is special and not
# really migrated, but used for migrations (for now)
######################################################

class MigrationData(Base_v0):
    __tablename__ = "core__migrations"

    name = Column(Unicode, primary_key=True)
    version = Column(Integer, nullable=False, default=0)

######################################################
