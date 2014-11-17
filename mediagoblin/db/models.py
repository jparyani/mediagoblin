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

from __future__ import print_function

import logging
import datetime

from sqlalchemy import Column, Integer, Unicode, UnicodeText, DateTime, \
        Boolean, ForeignKey, UniqueConstraint, PrimaryKeyConstraint, \
        SmallInteger, Date
from sqlalchemy.orm import relationship, backref, with_polymorphic, validates
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql.expression import desc
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.util import memoized_property

from mediagoblin.db.extratypes import (PathTupleWithSlashes, JSONEncoded,
                                       MutationDict)
from mediagoblin.db.base import Base, DictReadAttrProxy
from mediagoblin.db.mixin import UserMixin, MediaEntryMixin, \
        MediaCommentMixin, CollectionMixin, CollectionItemMixin, \
        ActivityMixin
from mediagoblin.tools.files import delete_media_files
from mediagoblin.tools.common import import_component
from mediagoblin.tools.routing import extract_url_arguments

import six
from pytz import UTC

_log = logging.getLogger(__name__)

class Location(Base):
    """ Represents a physical location """
    __tablename__ = "core__locations"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)

    # GPS coordinates
    position = Column(MutationDict.as_mutable(JSONEncoded))
    address = Column(MutationDict.as_mutable(JSONEncoded))

    @classmethod
    def create(cls, data, obj):
        location = cls()
        location.unserialize(data)
        location.save()
        obj.location = location.id
        return location

    def serialize(self, request):
        location = {"objectType": "place"}

        if self.name is not None:
            location["name"] = self.name

        if self.position:
            location["position"] = self.position

        if self.address:
            location["address"] = self.address

        return location

    def unserialize(self, data):
        if "name" in data:
            self.name = data["name"]

        self.position = {}
        self.address = {}

        # nicer way to do this?
        if "position" in data:
            # TODO: deal with ISO 9709 formatted string as position
            if "altitude" in data["position"]:
                self.position["altitude"] = data["position"]["altitude"]

            if "direction" in data["position"]:
                self.position["direction"] = data["position"]["direction"]

            if "longitude" in data["position"]:
                self.position["longitude"] = data["position"]["longitude"]

            if "latitude" in data["position"]:
                self.position["latitude"] = data["position"]["latitude"]

        if "address" in data:
            if "formatted" in data["address"]:
                self.address["formatted"] = data["address"]["formatted"]

            if "streetAddress" in data["address"]:
                self.address["streetAddress"] = data["address"]["streetAddress"]

            if "locality" in data["address"]:
                self.address["locality"] = data["address"]["locality"]

            if "region" in data["address"]:
                self.address["region"] = data["address"]["region"]

            if "postalCode" in data["address"]:
                self.address["postalCode"] = data["addresss"]["postalCode"]

            if "country" in data["address"]:
                self.address["country"] = data["address"]["country"]

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
    pw_hash = Column(Unicode)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    # Intented to be nullable=False, but migrations would not work for it
    # set to nullable=True implicitly.
    wants_comment_notification = Column(Boolean, default=True)
    wants_notifications = Column(Boolean, default=True)
    license_preference = Column(Unicode)
    url = Column(Unicode)
    bio = Column(UnicodeText)  # ??
    uploaded = Column(Integer, default=0)
    upload_limit = Column(Integer)
    location = Column(Integer, ForeignKey("core__locations.id"))
    get_location = relationship("Location", lazy="joined")

    activity = Column(Integer, ForeignKey("core__activity_intermediators.id"))

    ## TODO
    # plugin data would be in a separate model

    def __repr__(self):
        return '<{0} #{1} {2} {3} "{4}">'.format(
                self.__class__.__name__,
                self.id,
                'verified' if self.has_privilege(u'active') else 'non-verified',
                'admin' if self.has_privilege(u'admin') else 'user',
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

    def has_privilege(self, privilege, allow_admin=True):
        """
        This method checks to make sure a user has all the correct privileges
        to access a piece of content.

        :param  privilege       A unicode object which represent the different
                                privileges which may give the user access to
                                content.

        :param  allow_admin     If this is set to True the then if the user is
                                an admin, then this will always return True
                                even if the user hasn't been given the
                                privilege. (defaults to True)
        """
        priv = Privilege.query.filter_by(privilege_name=privilege).one()
        if priv in self.all_privileges:
            return True
        elif allow_admin and self.has_privilege(u'admin', allow_admin=False):
            return True

        return False

    def is_banned(self):
        """
        Checks if this user is banned.

            :returns                True if self is banned
            :returns                False if self is not
        """
        return UserBan.query.get(self.id) is not None


    def serialize(self, request):
        published = UTC.localize(self.created)
        user = {
            "id": "acct:{0}@{1}".format(self.username, request.host),
            "published": published.isoformat(),
            "preferredUsername": self.username,
            "displayName": "{0}@{1}".format(self.username, request.host),
            "objectType": self.object_type,
            "pump_io": {
                "shared": False,
                "followed": False,
            },
            "links": {
                "self": {
                    "href": request.urlgen(
                            "mediagoblin.federation.user.profile",
                             username=self.username,
                             qualified=True
                             ),
                },
                "activity-inbox": {
                    "href": request.urlgen(
                            "mediagoblin.federation.inbox",
                            username=self.username,
                            qualified=True
                            )
                },
                "activity-outbox": {
                    "href": request.urlgen(
                            "mediagoblin.federation.feed",
                            username=self.username,
                            qualified=True
                            )
                },
            },
        }

        if self.bio:
            user.update({"summary": self.bio})
        if self.url:
            user.update({"url": self.url})
        if self.location:
            user.update({"location": self.get_location.serialize(request)})

        return user

    def unserialize(self, data):
        if "summary" in data:
            self.bio = data["summary"]

        if "location" in data:
            Location.create(data, self)

class Client(Base):
    """
        Model representing a client - Used for API Auth
    """
    __tablename__ = "core__clients"

    id = Column(Unicode, nullable=True, primary_key=True)
    secret = Column(Unicode, nullable=False)
    expirey = Column(DateTime, nullable=True)
    application_type = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated = Column(DateTime, nullable=False, default=datetime.datetime.now)

    # optional stuff
    redirect_uri = Column(JSONEncoded, nullable=True)
    logo_url = Column(Unicode, nullable=True)
    application_name = Column(Unicode, nullable=True)
    contacts = Column(JSONEncoded, nullable=True)

    def __repr__(self):
        if self.application_name:
            return "<Client {0} - {1}>".format(self.application_name, self.id)
        else:
            return "<Client {0}>".format(self.id)

class RequestToken(Base):
    """
        Model for representing the request tokens
    """
    __tablename__ = "core__request_tokens"

    token = Column(Unicode, primary_key=True)
    secret = Column(Unicode, nullable=False)
    client = Column(Unicode, ForeignKey(Client.id))
    user = Column(Integer, ForeignKey(User.id), nullable=True)
    used = Column(Boolean, default=False)
    authenticated = Column(Boolean, default=False)
    verifier = Column(Unicode, nullable=True)
    callback = Column(Unicode, nullable=False, default=u"oob")
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated = Column(DateTime, nullable=False, default=datetime.datetime.now)

    get_client = relationship(Client)

class AccessToken(Base):
    """
        Model for representing the access tokens
    """
    __tablename__ = "core__access_tokens"

    token = Column(Unicode, nullable=False, primary_key=True)
    secret = Column(Unicode, nullable=False)
    user = Column(Integer, ForeignKey(User.id))
    request_token = Column(Unicode, ForeignKey(RequestToken.token))
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated = Column(DateTime, nullable=False, default=datetime.datetime.now)

    get_requesttoken = relationship(RequestToken)


class NonceTimestamp(Base):
    """
        A place the timestamp and nonce can be stored - this is for OAuth1
    """
    __tablename__ = "core__nonce_timestamps"

    nonce = Column(Unicode, nullable=False, primary_key=True)
    timestamp = Column(DateTime, nullable=False, primary_key=True)

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
    file_size = Column(Integer, default=0)
    location = Column(Integer, ForeignKey("core__locations.id"))
    get_location = relationship("Location", lazy="joined")

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
    media_metadata = Column(MutationDict.as_mutable(JSONEncoded),
        default=MutationDict())

    activity = Column(Integer, ForeignKey("core__activity_intermediators.id"))

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

    def get_file_metadata(self, file_key, metadata_key=None):
        """
        Return the file_metadata dict of a MediaFile. If metadata_key is given,
        return the value of the key.
        """
        media_file = MediaFile.query.filter_by(media_entry=self.id,
                                               name=six.text_type(file_key)).first()

        if media_file:
            if metadata_key:
                return media_file.file_metadata.get(metadata_key, None)

            return media_file.file_metadata

    def set_file_metadata(self, file_key, **kwargs):
        """
        Update the file_metadata of a MediaFile.
        """
        media_file = MediaFile.query.filter_by(media_entry=self.id,
                                               name=six.text_type(file_key)).first()

        file_metadata = media_file.file_metadata or {}

        for key, value in six.iteritems(kwargs):
            file_metadata[key] = value

        media_file.file_metadata = file_metadata
        media_file.save()

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
            for field, value in six.iteritems(kwargs):
                setattr(media_data, field, value)

    @memoized_property
    def media_data_ref(self):
        return import_component(self.media_type + '.models:BACKREF_NAME')

    def __repr__(self):
        if six.PY2:
            # obj.__repr__() should return a str on Python 2
            safe_title = self.title.encode('utf-8', 'replace')
        else:
            safe_title = self.title

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
        except OSError as error:
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

    def serialize(self, request, show_comments=True):
        """ Unserialize MediaEntry to object """
        href = request.urlgen(
            "mediagoblin.federation.object",
            object_type=self.object_type,
            id=self.id,
            qualified=True
        )
        author = self.get_uploader
        published = UTC.localize(self.created)
        updated = UTC.localize(self.created)
        context = {
            "id": href,
            "author": author.serialize(request),
            "objectType": self.object_type,
            "url": self.url_for_self(request.urlgen, qualified=True),
            "image": {
                "url": request.host_url + self.thumb_url[1:],
            },
            "fullImage":{
                "url": request.host_url + self.original_url[1:],
            },
            "published": published.isoformat(),
            "updated": updated.isoformat(),
            "pump_io": {
                "shared": False,
            },
            "links": {
                "self": {
                    "href": href,
                },

            }
        }

        if self.title:
            context["displayName"] = self.title

        if self.description:
            context["content"] = self.description

        if self.license:
            context["license"] = self.license

        if self.location:
            context["location"] = self.get_location.serialize(request)

        if show_comments:
            comments = [
                comment.serialize(request) for comment in self.get_comments()]
            total = len(comments)
            context["replies"] = {
                "totalItems": total,
                "items": comments,
                "url": request.urlgen(
                        "mediagoblin.federation.object.comments",
                        object_type=self.object_type,
                        id=self.id,
                        qualified=True
                        ),
            }

        return context

    def unserialize(self, data):
        """ Takes API objects and unserializes on existing MediaEntry """
        if "displayName" in data:
            self.title = data["displayName"]

        if "content" in data:
            self.description = data["content"]

        if "license" in data:
            self.license = data["license"]

        if "location" in data:
            Licence.create(data["location"], self)

        return True

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
    file_metadata = Column(MutationDict.as_mutable(JSONEncoded))

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
    location = Column(Integer, ForeignKey("core__locations.id"))
    get_location = relationship("Location", lazy="joined")

    # Cascade: Comments are owned by their creator. So do the full thing.
    # lazy=dynamic: People might post a *lot* of comments,
    #     so make the "posted_comments" a query-like thing.
    get_author = relationship(User,
                              backref=backref("posted_comments",
                                              lazy="dynamic",
                                              cascade="all, delete-orphan"))
    get_entry = relationship(MediaEntry,
                             backref=backref("comments",
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


    activity = Column(Integer, ForeignKey("core__activity_intermediators.id"))

    def serialize(self, request):
        """ Unserialize to python dictionary for API """
        href = request.urlgen(
            "mediagoblin.federation.object",
            object_type=self.object_type,
            id=self.id,
            qualified=True
        )
        media = MediaEntry.query.filter_by(id=self.media_entry).first()
        author = self.get_author
        context = {
            "id": href,
            "objectType": self.object_type,
            "content": self.content,
            "inReplyTo": media.serialize(request, show_comments=False),
            "author": author.serialize(request)
        }

        if self.location:
            context["location"] = self.get_location.seralize(request)

        return context

    def unserialize(self, data, request):
        """ Takes API objects and unserializes on existing comment """
        # Do initial checks to verify the object is correct
        required_attributes = ["content", "inReplyTo"]
        for attr in required_attributes:
            if attr not in data:
                return False

        # Validate inReplyTo has ID
        if "id" not in data["inReplyTo"]:
            return False

        # Validate that the ID is correct
        try:
            media_id = int(extract_url_arguments(
                url=data["inReplyTo"]["id"],
                urlmap=request.app.url_map
            )["id"])
        except ValueError:
            return False

        media = MediaEntry.query.filter_by(id=media_id).first()
        if media is None:
            return False

        self.media_entry = media.id
        self.content = data["content"]

        if "location" in data:
            Location.create(data["location"], self)

        return True



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
    location = Column(Integer, ForeignKey("core__locations.id"))
    get_location = relationship("Location", lazy="joined")

    # TODO: No of items in Collection. Badly named, can we migrate to num_items?
    items = Column(Integer, default=0)

    # Cascade: Collections are owned by their creator. So do the full thing.
    get_creator = relationship(User,
                               backref=backref("collections",
                                               cascade="all, delete-orphan"))

    activity = Column(Integer, ForeignKey("core__activity_intermediators.id"))

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

    def __repr__(self):
        safe_title = self.title.encode('ascii', 'replace')
        return '<{classname} #{id}: {title} by {creator}>'.format(
            id=self.id,
            classname=self.__class__.__name__,
            creator=self.creator,
            title=safe_title)

    def serialize(self, request):
        # Get all serialized output in a list
        items = []
        for item in self.get_collection_items():
            items.append(item.serialize(request))

        return {
            "totalItems": self.items,
            "url": self.url_for_self(request.urlgen, qualified=True),
            "items": items,
        }


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

    def __repr__(self):
        return '<{classname} #{id}: Entry {entry} in {collection}>'.format(
            id=self.id,
            classname=self.__class__.__name__,
            collection=self.collection,
            entry=self.media_entry)

    def serialize(self, request):
        return self.get_media_entry.serialize(request)


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


class CommentSubscription(Base):
    __tablename__ = 'core__comment_subscriptions'
    id = Column(Integer, primary_key=True)

    created = Column(DateTime, nullable=False, default=datetime.datetime.now)

    media_entry_id = Column(Integer, ForeignKey(MediaEntry.id), nullable=False)
    media_entry = relationship(MediaEntry,
                        backref=backref('comment_subscriptions',
                                        cascade='all, delete-orphan'))

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User,
                        backref=backref('comment_subscriptions',
                                        cascade='all, delete-orphan'))

    notify = Column(Boolean, nullable=False, default=True)
    send_email = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return ('<{classname} #{id}: {user} {media} notify: '
                '{notify} email: {email}>').format(
            id=self.id,
            classname=self.__class__.__name__,
            user=self.user,
            media=self.media_entry,
            notify=self.notify,
            email=self.send_email)


class Notification(Base):
    __tablename__ = 'core__notifications'
    id = Column(Integer, primary_key=True)
    type = Column(Unicode)

    created = Column(DateTime, nullable=False, default=datetime.datetime.now)

    user_id = Column(Integer, ForeignKey('core__users.id'), nullable=False,
                     index=True)
    seen = Column(Boolean, default=lambda: False, index=True)
    user = relationship(
        User,
        backref=backref('notifications', cascade='all, delete-orphan'))

    __mapper_args__ = {
        'polymorphic_identity': 'notification',
        'polymorphic_on': type
    }

    def __repr__(self):
        return '<{klass} #{id}: {user}: {subject} ({seen})>'.format(
            id=self.id,
            klass=self.__class__.__name__,
            user=self.user,
            subject=getattr(self, 'subject', None),
            seen='unseen' if not self.seen else 'seen')

    def __unicode__(self):
        return u'<{klass} #{id}: {user}: {subject} ({seen})>'.format(
            id=self.id,
            klass=self.__class__.__name__,
            user=self.user,
            subject=getattr(self, 'subject', None),
            seen='unseen' if not self.seen else 'seen')


class CommentNotification(Notification):
    __tablename__ = 'core__comment_notifications'
    id = Column(Integer, ForeignKey(Notification.id), primary_key=True)

    subject_id = Column(Integer, ForeignKey(MediaComment.id))
    subject = relationship(
        MediaComment,
        backref=backref('comment_notifications', cascade='all, delete-orphan'))

    __mapper_args__ = {
        'polymorphic_identity': 'comment_notification'
    }


class ProcessingNotification(Notification):
    __tablename__ = 'core__processing_notifications'

    id = Column(Integer, ForeignKey(Notification.id), primary_key=True)

    subject_id = Column(Integer, ForeignKey(MediaEntry.id))
    subject = relationship(
        MediaEntry,
        backref=backref('processing_notifications',
                        cascade='all, delete-orphan'))

    __mapper_args__ = {
        'polymorphic_identity': 'processing_notification'
    }

# the with_polymorphic call has been moved to the bottom above MODELS
# this is because it causes conflicts with relationship calls.

class ReportBase(Base):
    """
    This is the basic report object which the other reports are based off of.

        :keyword    reporter_id         Holds the id of the user who created
                                            the report, as an Integer column.
        :keyword    report_content      Hold the explanation left by the repor-
                                            -ter to indicate why they filed the
                                            report in the first place, as a
                                            Unicode column.
        :keyword    reported_user_id    Holds the id of the user who created
                                            the content which was reported, as
                                            an Integer column.
        :keyword    created             Holds a datetime column of when the re-
                                            -port was filed.
        :keyword    discriminator       This column distinguishes between the
                                            different types of reports.
        :keyword    resolver_id         Holds the id of the moderator/admin who
                                            resolved the report.
        :keyword    resolved            Holds the DateTime object which descri-
                                            -bes when this report was resolved
        :keyword    result              Holds the UnicodeText column of the
                                            resolver's reasons for resolving
                                            the report this way. Some of this
                                            is auto-generated
    """
    __tablename__ = 'core__reports'
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey(User.id), nullable=False)
    reporter =  relationship(
        User,
        backref=backref("reports_filed_by",
            lazy="dynamic",
            cascade="all, delete-orphan"),
        primaryjoin="User.id==ReportBase.reporter_id")
    report_content = Column(UnicodeText)
    reported_user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    reported_user = relationship(
        User,
        backref=backref("reports_filed_on",
            lazy="dynamic",
            cascade="all, delete-orphan"),
        primaryjoin="User.id==ReportBase.reported_user_id")
    created = Column(DateTime, nullable=False, default=datetime.datetime.now())
    discriminator = Column('type', Unicode(50))
    resolver_id = Column(Integer, ForeignKey(User.id))
    resolver = relationship(
        User,
        backref=backref("reports_resolved_by",
            lazy="dynamic",
            cascade="all, delete-orphan"),
        primaryjoin="User.id==ReportBase.resolver_id")

    resolved = Column(DateTime)
    result = Column(UnicodeText)
    __mapper_args__ = {'polymorphic_on': discriminator}

    def is_comment_report(self):
        return self.discriminator=='comment_report'

    def is_media_entry_report(self):
        return self.discriminator=='media_report'

    def is_archived_report(self):
        return self.resolved is not None

    def archive(self,resolver_id, resolved, result):
        self.resolver_id   = resolver_id
        self.resolved   = resolved
        self.result     = result


class CommentReport(ReportBase):
    """
    Reports that have been filed on comments.
        :keyword    comment_id          Holds the integer value of the reported
                                            comment's ID
    """
    __tablename__ = 'core__reports_on_comments'
    __mapper_args__ = {'polymorphic_identity': 'comment_report'}

    id = Column('id',Integer, ForeignKey('core__reports.id'),
                                                primary_key=True)
    comment_id = Column(Integer, ForeignKey(MediaComment.id), nullable=True)
    comment = relationship(
        MediaComment, backref=backref("reports_filed_on",
            lazy="dynamic"))


class MediaReport(ReportBase):
    """
    Reports that have been filed on media entries
        :keyword    media_entry_id      Holds the integer value of the reported
                                            media entry's ID
    """
    __tablename__ = 'core__reports_on_media'
    __mapper_args__ = {'polymorphic_identity': 'media_report'}

    id = Column('id',Integer, ForeignKey('core__reports.id'),
                                                primary_key=True)
    media_entry_id = Column(Integer, ForeignKey(MediaEntry.id), nullable=True)
    media_entry = relationship(
        MediaEntry,
        backref=backref("reports_filed_on",
            lazy="dynamic"))

class UserBan(Base):
    """
    Holds the information on a specific user's ban-state. As long as one of
        these is attached to a user, they are banned from accessing mediagoblin.
        When they try to log in, they are greeted with a page that tells them
        the reason why they are banned and when (if ever) the ban will be
        lifted

        :keyword user_id          Holds the id of the user this object is
                                    attached to. This is a one-to-one
                                    relationship.
        :keyword expiration_date  Holds the date that the ban will be lifted.
                                    If this is null, the ban is permanent
                                    unless a moderator manually lifts it.
        :keyword reason           Holds the reason why the user was banned.
    """
    __tablename__ = 'core__user_bans'

    user_id = Column(Integer, ForeignKey(User.id), nullable=False,
                                                        primary_key=True)
    expiration_date = Column(Date)
    reason = Column(UnicodeText, nullable=False)


class Privilege(Base):
    """
    The Privilege table holds all of the different privileges a user can hold.
    If a user 'has' a privilege, the User object is in a relationship with the
    privilege object.

        :keyword privilege_name   Holds a unicode object that is the recognizable
                                    name of this privilege. This is the column
                                    used for identifying whether or not a user
                                    has a necessary privilege or not.

    """
    __tablename__ = 'core__privileges'

    id = Column(Integer, nullable=False, primary_key=True)
    privilege_name = Column(Unicode, nullable=False, unique=True)
    all_users = relationship(
        User,
        backref='all_privileges',
        secondary="core__privileges_users")

    def __init__(self, privilege_name):
        '''
        Currently consructors are required for tables that are initialized thru
        the FOUNDATIONS system. This is because they need to be able to be con-
        -structed by a list object holding their arg*s
        '''
        self.privilege_name = privilege_name

    def __repr__(self):
        return "<Privilege %s>" % (self.privilege_name)


class PrivilegeUserAssociation(Base):
    '''
    This table holds the many-to-many relationship between User and Privilege
    '''

    __tablename__ = 'core__privileges_users'

    user = Column(
        "user",
        Integer,
        ForeignKey(User.id),
        primary_key=True)
    privilege = Column(
        "privilege",
        Integer,
        ForeignKey(Privilege.id),
        primary_key=True)

class Generator(Base):
    """ Information about what created an activity """
    __tablename__ = "core__generators"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    published = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, default=datetime.datetime.now)
    object_type = Column(Unicode, nullable=False)

    def __repr__(self):
        return "<{klass} {name}>".format(
            klass=self.__class__.__name__,
            name=self.name
        )

    def serialize(self, request):
        href = request.urlgen(
            "mediagoblin.federation.object",
            object_type=self.object_type,
            id=self.id,
            qualified=True
        )
        published = UTC.localize(self.published)
        updated = UTC.localize(self.updated)
        return {
            "id": href,
            "displayName": self.name,
            "published": published.isoformat(),
            "updated": updated.isoformat(),
            "objectType": self.object_type,
        }

    def unserialize(self, data):
        if "displayName" in data:
            self.name = data["displayName"]


class ActivityIntermediator(Base):
    """
    This is used so that objects/targets can have a foreign key back to this
    object and activities can a foreign key to this object. This objects to be
    used multiple times for the activity object or target and also allows for
    different types of objects to be used as an Activity.
    """
    __tablename__ = "core__activity_intermediators"

    id = Column(Integer, primary_key=True)
    type = Column(Unicode, nullable=False)

    TYPES = {
        "user": User,
        "media": MediaEntry,
        "comment": MediaComment,
        "collection": Collection,
    }

    def _find_model(self, obj):
        """ Finds the model for a given object """
        for key, model in self.TYPES.items():
            if isinstance(obj, model):
                return key, model

        return None, None

    def set(self, obj):
        """ This sets itself as the activity """
        key, model = self._find_model(obj)
        if key is None:
            raise ValueError("Invalid type of object given")

        self.type = key

        # We need to populate the self.id so we need to save but, we don't
        # want to save this AI in the database (yet) so commit=False.
        self.save(commit=False)
        obj.activity = self.id
        obj.save()

    def get(self):
        """ Finds the object for an activity """
        if self.type is None:
            return None

        model = self.TYPES[self.type]
        return model.query.filter_by(activity=self.id).first()

    @validates("type")
    def validate_type(self, key, value):
        """ Validate that the type set is a valid type """
        assert value in self.TYPES
        return value

class Activity(Base, ActivityMixin):
    """
    This holds all the metadata about an activity such as uploading an image,
    posting a comment, etc.
    """
    __tablename__ = "core__activities"

    id = Column(Integer, primary_key=True)
    actor = Column(Integer,
                   ForeignKey("core__users.id"),
                   nullable=False)
    published = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated = Column(DateTime, nullable=False, default=datetime.datetime.now)
    verb = Column(Unicode, nullable=False)
    content = Column(Unicode, nullable=True)
    title = Column(Unicode, nullable=True)
    generator = Column(Integer,
                       ForeignKey("core__generators.id"),
                       nullable=True)
    object = Column(Integer,
                    ForeignKey("core__activity_intermediators.id"),
                    nullable=False)
    target = Column(Integer,
                    ForeignKey("core__activity_intermediators.id"),
                    nullable=True)

    get_actor = relationship(User,
        foreign_keys="Activity.actor", post_update=True)
    get_generator = relationship(Generator)

    def __repr__(self):
        if self.content is None:
            return "<{klass} verb:{verb}>".format(
                klass=self.__class__.__name__,
                verb=self.verb
            )
        else:
            return "<{klass} {content}>".format(
                klass=self.__class__.__name__,
                content=self.content
            )

    @property
    def get_object(self):
        if self.object is None:
            return None

        ai = ActivityIntermediator.query.filter_by(id=self.object).first()
        return ai.get()

    def set_object(self, obj):
        self.object = self._set_model(obj)

    @property
    def get_target(self):
        if self.target is None:
            return None

        ai = ActivityIntermediator.query.filter_by(id=self.target).first()
        return ai.get()

    def set_target(self, obj):
        self.target = self._set_model(obj)

    def _set_model(self, obj):
        # Firstly can we set obj
        if not hasattr(obj, "activity"):
            raise ValueError(
                "{0!r} is unable to be set on activity".format(obj))

        if obj.activity is None:
            # We need to create a new AI
            ai = ActivityIntermediator()
            ai.set(obj)
            ai.save()
            return ai.id

        # Okay we should have an existing AI
        return ActivityIntermediator.query.filter_by(id=obj.activity).first().id

    def save(self, set_updated=True, *args, **kwargs):
        if set_updated:
            self.updated = datetime.datetime.now()
        super(Activity, self).save(*args, **kwargs)

with_polymorphic(
    Notification,
    [ProcessingNotification, CommentNotification])

MODELS = [
    User, MediaEntry, Tag, MediaTag, MediaComment, Collection, CollectionItem,
    MediaFile, FileKeynames, MediaAttachmentFile, ProcessingMetaData,
    Notification, CommentNotification, ProcessingNotification, Client,
    CommentSubscription, ReportBase, CommentReport, MediaReport, UserBan,
	Privilege, PrivilegeUserAssociation,
    RequestToken, AccessToken, NonceTimestamp,
    Activity, ActivityIntermediator, Generator,
    Location]

"""
 Foundations are the default rows that are created immediately after the tables
 are initialized. Each entry to  this dictionary should be in the format of:
                 ModelConstructorObject:List of Dictionaries
 (Each Dictionary represents a row on the Table to be created, containing each
  of the columns' names as a key string, and each of the columns' values as a
  value)

 ex. [NOTE THIS IS NOT BASED OFF OF OUR USER TABLE]
    user_foundations = [{'name':u'Joanna', 'age':24},
                        {'name':u'Andrea', 'age':41}]

    FOUNDATIONS = {User:user_foundations}
"""
privilege_foundations = [{'privilege_name':u'admin'},
						{'privilege_name':u'moderator'},
						{'privilege_name':u'uploader'},
						{'privilege_name':u'reporter'},
						{'privilege_name':u'commenter'},
						{'privilege_name':u'active'}]
FOUNDATIONS = {Privilege:privilege_foundations}

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
    print(repr(argv))
    if len(argv) == 2:
        uri = argv[1]
    else:
        uri = None
    show_table_init(uri)
