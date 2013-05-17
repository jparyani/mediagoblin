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

import logging
import datetime

from sqlalchemy import Column, Integer, Unicode, UnicodeText, DateTime, \
        Boolean, ForeignKey, UniqueConstraint, PrimaryKeyConstraint, \
        SmallInteger
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql.expression import desc
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.util import memoized_property

from mediagoblin.db.extratypes import PathTupleWithSlashes, JSONEncoded
from mediagoblin.db.base import Base, DictReadAttrProxy
from mediagoblin.db.mixin import UserMixin, MediaEntryMixin, MediaCommentMixin, CollectionMixin, CollectionItemMixin
from mediagoblin.tools.files import delete_media_files
from mediagoblin.tools.common import import_component

# It's actually kind of annoying how sqlalchemy-migrate does this, if
# I understand it right, but whatever.  Anyway, don't remove this :P
#
# We could do migration calls more manually instead of relying on
# this import-based meddling...
from migrate import changeset

_log = logging.getLogger(__name__)


class User(Base, UserMixin):
    """
    TODO: We should consider moving some rarely used fields
    into some sort of "shadow" table.
    """
    __tablename__ = "core__users"

    id = Column(Integer, primary_key=True)
    username = Column(Unicode, nullable=False, unique=True)
    # Note: no db uniqueness constraint on email because it's not
    # reliable (many email systems case insensitive despite against
    # the RFC) and because it would be a mess to implement at this
    # point.
    email = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    pw_hash = Column(Unicode, nullable=False)
    email_verified = Column(Boolean, default=False)
    status = Column(Unicode, default=u"needs_email_verification", nullable=False)
    # Intented to be nullable=False, but migrations would not work for it
    # set to nullable=True implicitly.
    wants_comment_notification = Column(Boolean, default=True)
    license_preference = Column(Unicode)
    verification_key = Column(Unicode)
    is_admin = Column(Boolean, default=False, nullable=False)
    url = Column(Unicode)
    bio = Column(UnicodeText)  # ??
    fp_verification_key = Column(Unicode)
    fp_token_expire = Column(DateTime)

    ## TODO
    # plugin data would be in a separate model

    def __repr__(self):
        return '<{0} #{1} {2} {3} "{4}">'.format(
                self.__class__.__name__,
                self.id,
                'verified' if self.email_verified else 'non-verified',
                'admin' if self.is_admin else 'user',
                self.username)

    def delete(self, **kwargs):
        """Deletes a User and all related entries/comments/files/..."""
        # Collections get deleted by relationships.

        media_entries = MediaEntry.query.filter(MediaEntry.uploader == self.id)
        for media in media_entries:
            # TODO: Make sure that "MediaEntry.delete()" also deletes
            # all related files/Comments
            media.delete(del_orphan_tags=False, commit=False)

        # Delete now unused tags
        # TODO: import here due to cyclic imports!!! This cries for refactoring
        from mediagoblin.db.util import clean_orphan_tags
        clean_orphan_tags(commit=False)

        # Delete user, pass through commit=False/True in kwargs
        super(User, self).delete(**kwargs)
        _log.info('Deleted user "{0}" account'.format(self.username))


class MediaEntry(Base, MediaEntryMixin):
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
    collected = Column(Integer, default=0)

    fail_error = Column(Unicode)
    fail_metadata = Column(JSONEncoded)

    transcoding_progress = Column(SmallInteger)

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
        cascade="all, delete-orphan" # should be automatically deleted
        )
    tags = association_proxy("tags_helper", "dict_view",
        creator=lambda v: MediaTag(name=v["name"], slug=v["slug"])
        )

    collections_helper = relationship("CollectionItem",
        cascade="all, delete-orphan"
        )
    collections = association_proxy("collections_helper", "in_collection")

    ## TODO
    # fail_error

    def get_comments(self, ascending=False):
        order_col = MediaComment.created
        if not ascending:
            order_col = desc(order_col)
        return self.all_comments.order_by(order_col)

    def url_to_prev(self, urlgen):
        """get the next 'newer' entry by this user"""
        media = MediaEntry.query.filter(
            (MediaEntry.uploader == self.uploader)
            & (MediaEntry.state == u'processed')
            & (MediaEntry.id > self.id)).order_by(MediaEntry.id).first()

        if media is not None:
            return media.url_for_self(urlgen)

    def url_to_next(self, urlgen):
        """get the next 'older' entry by this user"""
        media = MediaEntry.query.filter(
            (MediaEntry.uploader == self.uploader)
            & (MediaEntry.state == u'processed')
            & (MediaEntry.id < self.id)).order_by(desc(MediaEntry.id)).first()

        if media is not None:
            return media.url_for_self(urlgen)

    @property
    def media_data(self):
        return getattr(self, self.media_data_ref)

    def media_data_init(self, **kwargs):
        """
        Initialize or update the contents of a media entry's media_data row
        """
        media_data = self.media_data

        if media_data is None:
            # Get the correct table:
            table = import_component(self.media_type + '.models:DATA_MODEL')
            # No media data, so actually add a new one
            media_data = table(**kwargs)
            # Get the relationship set up.
            media_data.get_media_entry = self
        else:
            # Update old media data
            for field, value in kwargs.iteritems():
                setattr(media_data, field, value)

    @memoized_property
    def media_data_ref(self):
        return import_component(self.media_type + '.models:BACKREF_NAME')

    def __repr__(self):
        safe_title = self.title.encode('ascii', 'replace')

        return '<{classname} {id}: {title}>'.format(
                classname=self.__class__.__name__,
                id=self.id,
                title=safe_title)

    def delete(self, del_orphan_tags=True, **kwargs):
        """Delete MediaEntry and all related files/attachments/comments

        This will *not* automatically delete unused collections, which
        can remain empty...

        :param del_orphan_tags: True/false if we delete unused Tags too
        :param commit: True/False if this should end the db transaction"""
        # User's CollectionItems are automatically deleted via "cascade".
        # Comments on this Media are deleted by cascade, hopefully.

        # Delete all related files/attachments
        try:
            delete_media_files(self)
        except OSError, error:
            # Returns list of files we failed to delete
            _log.error('No such files from the user "{1}" to delete: '
                       '{0}'.format(str(error), self.get_uploader))
        _log.info('Deleted Media entry id "{0}"'.format(self.id))
        # Related MediaTag's are automatically cleaned, but we might
        # want to clean out unused Tag's too.
        if del_orphan_tags:
            # TODO: Import here due to cyclic imports!!!
            #       This cries for refactoring
            from mediagoblin.db.util import clean_orphan_tags
            clean_orphan_tags(commit=False)
        # pass through commit=False/True in kwargs
        super(MediaEntry, self).delete(**kwargs)


class FileKeynames(Base):
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


class MediaFile(Base):
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


class MediaTag(Base):
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
    __tablename__ = "core__media_comments"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id), nullable=False, index=True)
    author = Column(Integer, ForeignKey(User.id), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    content = Column(UnicodeText, nullable=False)

    # Cascade: Comments are owned by their creator. So do the full thing.
    # lazy=dynamic: People might post a *lot* of comments,
    #     so make the "posted_comments" a query-like thing.
    get_author = relationship(User,
                              backref=backref("posted_comments",
                                              lazy="dynamic",
                                              cascade="all, delete-orphan"))

    # Cascade: Comments are somewhat owned by their MediaEntry.
    #     So do the full thing.
    # lazy=dynamic: MediaEntries might have many comments,
    #     so make the "all_comments" a query-like thing.
    get_media_entry = relationship(MediaEntry,
                                   backref=backref("all_comments",
                                                   lazy="dynamic",
                                                   cascade="all, delete-orphan"))


class Collection(Base, CollectionMixin):
    """An 'album' or 'set' of media by a user.

    On deletion, contained CollectionItems get automatically reaped via
    SQL cascade"""
    __tablename__ = "core__collections"

    id = Column(Integer, primary_key=True)
    title = Column(Unicode, nullable=False)
    slug = Column(Unicode)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now,
                     index=True)
    description = Column(UnicodeText)
    creator = Column(Integer, ForeignKey(User.id), nullable=False)
    # TODO: No of items in Collection. Badly named, can we migrate to num_items?
    items = Column(Integer, default=0)

    # Cascade: Collections are owned by their creator. So do the full thing.
    get_creator = relationship(User,
                               backref=backref("collections",
                                               cascade="all, delete-orphan"))

    __table_args__ = (
        UniqueConstraint('creator', 'slug'),
        {})

    def get_collection_items(self, ascending=False):
        #TODO, is this still needed with self.collection_items being available?
        order_col = CollectionItem.position
        if not ascending:
            order_col = desc(order_col)
        return CollectionItem.query.filter_by(
            collection=self.id).order_by(order_col)


class CollectionItem(Base, CollectionItemMixin):
    __tablename__ = "core__collection_items"

    id = Column(Integer, primary_key=True)
    media_entry = Column(
        Integer, ForeignKey(MediaEntry.id), nullable=False, index=True)
    collection = Column(Integer, ForeignKey(Collection.id), nullable=False)
    note = Column(UnicodeText, nullable=True)
    added = Column(DateTime, nullable=False, default=datetime.datetime.now)
    position = Column(Integer)

    # Cascade: CollectionItems are owned by their Collection. So do the full thing.
    in_collection = relationship(Collection,
                                 backref=backref(
                                     "collection_items",
                                     cascade="all, delete-orphan"))

    get_media_entry = relationship(MediaEntry)

    __table_args__ = (
        UniqueConstraint('collection', 'media_entry'),
        {})

    @property
    def dict_view(self):
        """A dict like view on this object"""
        return DictReadAttrProxy(self)


class ProcessingMetaData(Base):
    __tablename__ = 'core__processing_metadata'

    id = Column(Integer, primary_key=True)
    media_entry_id = Column(Integer, ForeignKey(MediaEntry.id), nullable=False,
            index=True)
    media_entry = relationship(MediaEntry,
            backref=backref('processing_metadata',
                cascade='all, delete-orphan'))
    callback_url = Column(Unicode)

    @property
    def dict_view(self):
        """A dict like view on this object"""
        return DictReadAttrProxy(self)


MODELS = [
    User, MediaEntry, Tag, MediaTag, MediaComment, Collection, CollectionItem, MediaFile, FileKeynames,
    MediaAttachmentFile, ProcessingMetaData]


######################################################
# Special, migrations-tracking table
#
# Not listed in MODELS because this is special and not
# really migrated, but used for migrations (for now)
######################################################

class MigrationData(Base):
    __tablename__ = "core__migrations"

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
