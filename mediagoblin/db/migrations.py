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

import six

if six.PY2:
    import migrate

from sqlalchemy import (MetaData, Table, Column, Boolean, SmallInteger,
                        Integer, Unicode, UnicodeText, DateTime,
                        ForeignKey, Date, Index)
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import and_
from sqlalchemy.schema import UniqueConstraint

from mediagoblin.db.extratypes import JSONEncoded, MutationDict
from mediagoblin.db.migration_tools import (
    RegisterMigration, inspect_table, replace_table_hack)
from mediagoblin.db.models import (MediaEntry, Collection, MediaComment, User,
    Privilege, Generator)
from mediagoblin.db.extratypes import JSONEncoded, MutationDict


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
            append_garbage_till_unique(row, six.text_type(row.id))
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
        new_slug = six.text_type(uuid.uuid4())
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

@RegisterMigration(11, MIGRATIONS)
def drop_token_related_User_columns(db):
    """
    Drop unneeded columns from the User table after switching to using
    itsdangerous tokens for email and forgot password verification.
    """
    metadata = MetaData(bind=db.bind)
    user_table = inspect_table(metadata, 'core__users')

    verification_key = user_table.columns['verification_key']
    fp_verification_key = user_table.columns['fp_verification_key']
    fp_token_expire = user_table.columns['fp_token_expire']

    verification_key.drop()
    fp_verification_key.drop()
    fp_token_expire.drop()

    db.commit()


class CommentSubscription_v0(declarative_base()):
    __tablename__ = 'core__comment_subscriptions'
    id = Column(Integer, primary_key=True)

    created = Column(DateTime, nullable=False, default=datetime.datetime.now)

    media_entry_id = Column(Integer, ForeignKey(MediaEntry.id), nullable=False)

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    notify = Column(Boolean, nullable=False, default=True)
    send_email = Column(Boolean, nullable=False, default=True)


class Notification_v0(declarative_base()):
    __tablename__ = 'core__notifications'
    id = Column(Integer, primary_key=True)
    type = Column(Unicode)

    created = Column(DateTime, nullable=False, default=datetime.datetime.now)

    user_id = Column(Integer, ForeignKey(User.id), nullable=False,
                     index=True)
    seen = Column(Boolean, default=lambda: False, index=True)


class CommentNotification_v0(Notification_v0):
    __tablename__ = 'core__comment_notifications'
    id = Column(Integer, ForeignKey(Notification_v0.id), primary_key=True)

    subject_id = Column(Integer, ForeignKey(MediaComment.id))


class ProcessingNotification_v0(Notification_v0):
    __tablename__ = 'core__processing_notifications'

    id = Column(Integer, ForeignKey(Notification_v0.id), primary_key=True)

    subject_id = Column(Integer, ForeignKey(MediaEntry.id))


@RegisterMigration(12, MIGRATIONS)
def add_new_notification_tables(db):
    metadata = MetaData(bind=db.bind)

    user_table = inspect_table(metadata, 'core__users')
    mediaentry_table = inspect_table(metadata, 'core__media_entries')
    mediacomment_table = inspect_table(metadata, 'core__media_comments')

    CommentSubscription_v0.__table__.create(db.bind)

    Notification_v0.__table__.create(db.bind)
    CommentNotification_v0.__table__.create(db.bind)
    ProcessingNotification_v0.__table__.create(db.bind)

    db.commit()


@RegisterMigration(13, MIGRATIONS)
def pw_hash_nullable(db):
    """Make pw_hash column nullable"""
    metadata = MetaData(bind=db.bind)
    user_table = inspect_table(metadata, "core__users")

    user_table.c.pw_hash.alter(nullable=True)

    # sqlite+sqlalchemy seems to drop this constraint during the
    # migration, so we add it back here for now a bit manually.
    if db.bind.url.drivername == 'sqlite':
        constraint = UniqueConstraint('username', table=user_table)
        constraint.create()

    db.commit()


# oauth1 migrations
class Client_v0(declarative_base()):
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

class RequestToken_v0(declarative_base()):
    """
        Model for representing the request tokens
    """
    __tablename__ = "core__request_tokens"

    token = Column(Unicode, primary_key=True)
    secret = Column(Unicode, nullable=False)
    client = Column(Unicode, ForeignKey(Client_v0.id))
    user = Column(Integer, ForeignKey(User.id), nullable=True)
    used = Column(Boolean, default=False)
    authenticated = Column(Boolean, default=False)
    verifier = Column(Unicode, nullable=True)
    callback = Column(Unicode, nullable=False, default=u"oob")
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated = Column(DateTime, nullable=False, default=datetime.datetime.now)

class AccessToken_v0(declarative_base()):
    """
        Model for representing the access tokens
    """
    __tablename__ = "core__access_tokens"

    token = Column(Unicode, nullable=False, primary_key=True)
    secret = Column(Unicode, nullable=False)
    user = Column(Integer, ForeignKey(User.id))
    request_token = Column(Unicode, ForeignKey(RequestToken_v0.token))
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated = Column(DateTime, nullable=False, default=datetime.datetime.now)


class NonceTimestamp_v0(declarative_base()):
    """
        A place the timestamp and nonce can be stored - this is for OAuth1
    """
    __tablename__ = "core__nonce_timestamps"

    nonce = Column(Unicode, nullable=False, primary_key=True)
    timestamp = Column(DateTime, nullable=False, primary_key=True)


@RegisterMigration(14, MIGRATIONS)
def create_oauth1_tables(db):
    """ Creates the OAuth1 tables """

    Client_v0.__table__.create(db.bind)
    RequestToken_v0.__table__.create(db.bind)
    AccessToken_v0.__table__.create(db.bind)
    NonceTimestamp_v0.__table__.create(db.bind)

    db.commit()

@RegisterMigration(15, MIGRATIONS)
def wants_notifications(db):
    """Add a wants_notifications field to User model"""
    metadata = MetaData(bind=db.bind)
    user_table = inspect_table(metadata, "core__users")
    col = Column('wants_notifications', Boolean, default=True)
    col.create(user_table)
    db.commit()



@RegisterMigration(16, MIGRATIONS)
def upload_limits(db):
    """Add user upload limit columns"""
    metadata = MetaData(bind=db.bind)

    user_table = inspect_table(metadata, 'core__users')
    media_entry_table = inspect_table(metadata, 'core__media_entries')

    col = Column('uploaded', Integer, default=0)
    col.create(user_table)

    col = Column('upload_limit', Integer)
    col.create(user_table)

    col = Column('file_size', Integer, default=0)
    col.create(media_entry_table)

    db.commit()


@RegisterMigration(17, MIGRATIONS)
def add_file_metadata(db):
    """Add file_metadata to MediaFile"""
    metadata = MetaData(bind=db.bind)
    media_file_table = inspect_table(metadata, "core__mediafiles")

    col = Column('file_metadata', MutationDict.as_mutable(JSONEncoded))
    col.create(media_file_table)

    db.commit()

###################
# Moderation tables
###################

class ReportBase_v0(declarative_base()):
    __tablename__ = 'core__reports'
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey(User.id), nullable=False)
    report_content = Column(UnicodeText)
    reported_user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    discriminator = Column('type', Unicode(50))
    resolver_id = Column(Integer, ForeignKey(User.id))
    resolved = Column(DateTime)
    result = Column(UnicodeText)
    __mapper_args__ = {'polymorphic_on': discriminator}


class CommentReport_v0(ReportBase_v0):
    __tablename__ = 'core__reports_on_comments'
    __mapper_args__ = {'polymorphic_identity': 'comment_report'}

    id = Column('id',Integer, ForeignKey('core__reports.id'),
                                                primary_key=True)
    comment_id = Column(Integer, ForeignKey(MediaComment.id), nullable=True)


class MediaReport_v0(ReportBase_v0):
    __tablename__ = 'core__reports_on_media'
    __mapper_args__ = {'polymorphic_identity': 'media_report'}

    id = Column('id',Integer, ForeignKey('core__reports.id'), primary_key=True)
    media_entry_id = Column(Integer, ForeignKey(MediaEntry.id), nullable=True)


class UserBan_v0(declarative_base()):
    __tablename__ = 'core__user_bans'
    user_id = Column(Integer, ForeignKey(User.id), nullable=False,
                                         primary_key=True)
    expiration_date = Column(Date)
    reason = Column(UnicodeText, nullable=False)


class Privilege_v0(declarative_base()):
    __tablename__ = 'core__privileges'
    id = Column(Integer, nullable=False, primary_key=True, unique=True)
    privilege_name = Column(Unicode, nullable=False, unique=True)


class PrivilegeUserAssociation_v0(declarative_base()):
    __tablename__ = 'core__privileges_users'
    privilege_id = Column(
        'core__privilege_id',
        Integer,
        ForeignKey(User.id),
        primary_key=True)
    user_id = Column(
        'core__user_id',
        Integer,
        ForeignKey(Privilege.id),
        primary_key=True)


PRIVILEGE_FOUNDATIONS_v0 = [{'privilege_name':u'admin'},
                            {'privilege_name':u'moderator'},
                            {'privilege_name':u'uploader'},
                            {'privilege_name':u'reporter'},
                            {'privilege_name':u'commenter'},
                            {'privilege_name':u'active'}]

# vR1 stands for "version Rename 1".  This only exists because we need
# to deal with dropping some booleans and it's otherwise impossible
# with sqlite.

class User_vR1(declarative_base()):
    __tablename__ = 'rename__users'
    id = Column(Integer, primary_key=True)
    username = Column(Unicode, nullable=False, unique=True)
    email = Column(Unicode, nullable=False)
    pw_hash = Column(Unicode)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    wants_comment_notification = Column(Boolean, default=True)
    wants_notifications = Column(Boolean, default=True)
    license_preference = Column(Unicode)
    url = Column(Unicode)
    bio = Column(UnicodeText)  # ??
    uploaded = Column(Integer, default=0)
    upload_limit = Column(Integer)


@RegisterMigration(18, MIGRATIONS)
def create_moderation_tables(db):

    # First, we will create the new tables in the database.
    #--------------------------------------------------------------------------
    ReportBase_v0.__table__.create(db.bind)
    CommentReport_v0.__table__.create(db.bind)
    MediaReport_v0.__table__.create(db.bind)
    UserBan_v0.__table__.create(db.bind)
    Privilege_v0.__table__.create(db.bind)
    PrivilegeUserAssociation_v0.__table__.create(db.bind)

    db.commit()

    # Then initialize the tables that we will later use
    #--------------------------------------------------------------------------
    metadata = MetaData(bind=db.bind)
    privileges_table= inspect_table(metadata, "core__privileges")
    user_table = inspect_table(metadata, 'core__users')
    user_privilege_assoc = inspect_table(
        metadata, 'core__privileges_users')

    # This section initializes the default Privilege foundations, that
    # would be created through the FOUNDATIONS system in a new instance
    #--------------------------------------------------------------------------
    for parameters in PRIVILEGE_FOUNDATIONS_v0:
        db.execute(privileges_table.insert().values(**parameters))

    db.commit()

    # This next section takes the information from the old is_admin and status
    # columns and converts those to the new privilege system
    #--------------------------------------------------------------------------
    admin_users_ids, active_users_ids, inactive_users_ids = (
        db.execute(
            user_table.select().where(
                user_table.c.is_admin==True)).fetchall(),
        db.execute(
            user_table.select().where(
                user_table.c.is_admin==False).where(
                user_table.c.status==u"active")).fetchall(),
        db.execute(
            user_table.select().where(
                user_table.c.is_admin==False).where(
                user_table.c.status!=u"active")).fetchall())

    # Get the ids for each of the privileges so we can reference them ~~~~~~~~~
    (admin_privilege_id, uploader_privilege_id,
     reporter_privilege_id, commenter_privilege_id,
     active_privilege_id) = [
        db.execute(privileges_table.select().where(
            privileges_table.c.privilege_name==privilege_name)).first()['id']
        for privilege_name in
            [u"admin",u"uploader",u"reporter",u"commenter",u"active"]
    ]

    # Give each user the appopriate privileges depending whether they are an
    # admin, an active user or an inactive user ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for admin_user in admin_users_ids:
        admin_user_id = admin_user['id']
        for privilege_id in [admin_privilege_id, uploader_privilege_id,
                            reporter_privilege_id, commenter_privilege_id,
                            active_privilege_id]:
            db.execute(user_privilege_assoc.insert().values(
                core__privilege_id=admin_user_id,
                core__user_id=privilege_id))

    for active_user in active_users_ids:
        active_user_id = active_user['id']
        for privilege_id in [uploader_privilege_id, reporter_privilege_id,
                            commenter_privilege_id, active_privilege_id]:
            db.execute(user_privilege_assoc.insert().values(
                core__privilege_id=active_user_id,
                core__user_id=privilege_id))

    for inactive_user in inactive_users_ids:
        inactive_user_id = inactive_user['id']
        for privilege_id in [uploader_privilege_id, reporter_privilege_id,
                             commenter_privilege_id]:
            db.execute(user_privilege_assoc.insert().values(
                core__privilege_id=inactive_user_id,
                core__user_id=privilege_id))

    db.commit()

    # And then, once the information is taken from is_admin & status columns
    # we drop all of the vestigial columns from the User table.
    #--------------------------------------------------------------------------
    if db.bind.url.drivername == 'sqlite':
        # SQLite has some issues that make it *impossible* to drop boolean
        # columns. So, the following code is a very hacky workaround which
        # makes it possible. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        User_vR1.__table__.create(db.bind)
        db.commit()
        new_user_table = inspect_table(metadata, 'rename__users')
        replace_table_hack(db, user_table, new_user_table)
    else:
        # If the db is not run using SQLite, this process is much simpler ~~~~~

        status = user_table.columns['status']
        email_verified = user_table.columns['email_verified']
        is_admin = user_table.columns['is_admin']
        status.drop()
        email_verified.drop()
        is_admin.drop()

    db.commit()


@RegisterMigration(19, MIGRATIONS)
def drop_MediaEntry_collected(db):
    """
    Drop unused MediaEntry.collected column
    """
    metadata = MetaData(bind=db.bind)

    media_collected= inspect_table(metadata, 'core__media_entries')
    media_collected = media_collected.columns['collected']

    media_collected.drop()

    db.commit()


@RegisterMigration(20, MIGRATIONS)
def add_metadata_column(db):
    metadata = MetaData(bind=db.bind)

    media_entry = inspect_table(metadata, 'core__media_entries')

    col = Column('media_metadata', MutationDict.as_mutable(JSONEncoded),
        default=MutationDict())
    col.create(media_entry)

    db.commit()


class PrivilegeUserAssociation_R1(declarative_base()):
    __tablename__ = 'rename__privileges_users'
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

@RegisterMigration(21, MIGRATIONS)
def fix_privilege_user_association_table(db):
    """
    There was an error in the PrivilegeUserAssociation table that allowed for a
    dangerous sql error. We need to the change the name of the columns to be
    unique, and properly referenced.
    """
    metadata = MetaData(bind=db.bind)

    privilege_user_assoc = inspect_table(
        metadata, 'core__privileges_users')

    # This whole process is more complex if we're dealing with sqlite
    if db.bind.url.drivername == 'sqlite':
        PrivilegeUserAssociation_R1.__table__.create(db.bind)
        db.commit()

        new_privilege_user_assoc = inspect_table(
            metadata, 'rename__privileges_users')
        result = db.execute(privilege_user_assoc.select())
        for row in result:
            # The columns were improperly named before, so we switch the columns
            user_id, priv_id = row['core__privilege_id'], row['core__user_id']
            db.execute(new_privilege_user_assoc.insert().values(
                user=user_id,
                privilege=priv_id))

        db.commit()

        privilege_user_assoc.drop()
        new_privilege_user_assoc.rename('core__privileges_users')

    # much simpler if postgres though!
    else:
        privilege_user_assoc.c.core__user_id.alter(name="privilege")
        privilege_user_assoc.c.core__privilege_id.alter(name="user")

    db.commit()


@RegisterMigration(22, MIGRATIONS)
def add_index_username_field(db):
    """
    This migration has been found to be doing the wrong thing.  See
    the documentation in migration 23 (revert_username_index) below
    which undoes this for those databases that did run this migration.

    Old description:
      This indexes the User.username field which is frequently queried
      for example a user logging in. This solves the issue #894
    """
    ## This code is left commented out *on purpose!*
    ##
    ## We do not normally allow commented out code like this in
    ## MediaGoblin but this is a special case: since this migration has
    ## been nullified but with great work to set things back below,
    ## this is commented out for historical clarity.
    #
    # metadata = MetaData(bind=db.bind)
    # user_table = inspect_table(metadata, "core__users")
    #
    # new_index = Index("ix_core__users_uploader", user_table.c.username)
    # new_index.create()
    #
    # db.commit()
    pass


@RegisterMigration(23, MIGRATIONS)
def revert_username_index(db):
    """
    Revert the stuff we did in migration 22 above.

    There were a couple of problems with what we did:
     - There was never a need for this migration!  The unique
       constraint had an implicit b-tree index, so it wasn't really
       needed.  (This is my (Chris Webber's) fault for suggesting it
       needed to happen without knowing what's going on... my bad!)
     - On top of that, databases created after the models.py was
       changed weren't the same as those that had been run through
       migration 22 above.

    As such, we're setting things back to the way they were before,
    but as it turns out, that's tricky to do!
    """
    metadata = MetaData(bind=db.bind)
    user_table = inspect_table(metadata, "core__users")
    indexes = dict(
        [(index.name, index) for index in user_table.indexes])

    # index from unnecessary migration
    users_uploader_index = indexes.get(u'ix_core__users_uploader')
    # index created from models.py after (unique=True, index=True)
    # was set in models.py
    users_username_index = indexes.get(u'ix_core__users_username')

    if users_uploader_index is None and users_username_index is None:
        # We don't need to do anything.
        # The database isn't in a state where it needs fixing
        #
        # (ie, either went through the previous borked migration or
        #  was initialized with a models.py where core__users was both
        #  unique=True and index=True)
        return

    if db.bind.url.drivername == 'sqlite':
        # Again, sqlite has problems.  So this is tricky.

        # Yes, this is correct to use User_vR1!  Nothing has changed
        # between the *correct* version of this table and migration 18.
        User_vR1.__table__.create(db.bind)
        db.commit()
        new_user_table = inspect_table(metadata, 'rename__users')
        replace_table_hack(db, user_table, new_user_table)

    else:
        # If the db is not run using SQLite, we don't need to do crazy
        # table copying.

        # Remove whichever of the not-used indexes are in place
        if users_uploader_index is not None:
            users_uploader_index.drop()
        if users_username_index is not None:
            users_username_index.drop()

        # Given we're removing indexes then adding a unique constraint
        # which *we know might fail*, thus probably rolling back the
        # session, let's commit here.
        db.commit()

        try:
            # Add the unique constraint
            constraint = UniqueConstraint(
                'username', table=user_table)
            constraint.create()
        except ProgrammingError:
            # constraint already exists, no need to add
            db.rollback()

    db.commit()

class Generator_R0(declarative_base()):
    __tablename__ = "core__generators"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    published = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated = Column(DateTime, nullable=False, default=datetime.datetime.now)
    object_type = Column(Unicode, nullable=False)

class ActivityIntermediator_R0(declarative_base()):
    __tablename__ = "core__activity_intermediators"
    id = Column(Integer, primary_key=True)
    type = Column(Unicode, nullable=False)

class Activity_R0(declarative_base()):
    __tablename__ = "core__activities"
    id = Column(Integer, primary_key=True)
    actor = Column(Integer, ForeignKey(User.id), nullable=False)
    published = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated = Column(DateTime, nullable=False, default=datetime.datetime.now)
    verb = Column(Unicode, nullable=False)
    content = Column(Unicode, nullable=True)
    title = Column(Unicode, nullable=True)
    generator = Column(Integer, ForeignKey(Generator_R0.id), nullable=True)
    object = Column(Integer,
                    ForeignKey(ActivityIntermediator_R0.id),
                    nullable=False)
    target = Column(Integer,
                    ForeignKey(ActivityIntermediator_R0.id),
                    nullable=True)

@RegisterMigration(24, MIGRATIONS)
def activity_migration(db):
    """
    Creates everything to create activities in GMG
    - Adds Activity, ActivityIntermediator and Generator table
    - Creates GMG service generator for activities produced by the server
    - Adds the activity_as_object and activity_as_target to objects/targets
    - Retroactively adds activities for what we can acurately work out
    """
    # Set constants we'll use later
    FOREIGN_KEY = "core__activity_intermediators.id"
    ACTIVITY_COLUMN = "activity"

    # Create the new tables.
    ActivityIntermediator_R0.__table__.create(db.bind)
    Generator_R0.__table__.create(db.bind)
    Activity_R0.__table__.create(db.bind)
    db.commit()

    # Initiate the tables we want to use later
    metadata = MetaData(bind=db.bind)
    user_table = inspect_table(metadata, "core__users")
    activity_table = inspect_table(metadata, "core__activities")
    generator_table = inspect_table(metadata, "core__generators")
    collection_table = inspect_table(metadata, "core__collections")
    media_entry_table = inspect_table(metadata, "core__media_entries")
    media_comments_table = inspect_table(metadata, "core__media_comments")
    ai_table = inspect_table(metadata, "core__activity_intermediators")


    # Create the foundations for Generator
    db.execute(generator_table.insert().values(
        name="GNU Mediagoblin",
        object_type="service",
        published=datetime.datetime.now(),
        updated=datetime.datetime.now()
    ))
    db.commit()

    # Get the ID of that generator
    gmg_generator = db.execute(generator_table.select(
        generator_table.c.name==u"GNU Mediagoblin")).first()


    # Now we want to modify the tables which MAY have an activity at some point
    media_col = Column(ACTIVITY_COLUMN, Integer, ForeignKey(FOREIGN_KEY))
    media_col.create(media_entry_table)

    user_col = Column(ACTIVITY_COLUMN, Integer, ForeignKey(FOREIGN_KEY))
    user_col.create(user_table)

    comments_col = Column(ACTIVITY_COLUMN, Integer, ForeignKey(FOREIGN_KEY))
    comments_col.create(media_comments_table)

    collection_col = Column(ACTIVITY_COLUMN, Integer, ForeignKey(FOREIGN_KEY))
    collection_col.create(collection_table)
    db.commit()


    # Now we want to retroactively add what activities we can
    # first we'll add activities when people uploaded media.
    # these can't have content as it's not fesible to get the
    # correct content strings.
    for media in db.execute(media_entry_table.select()):
        # Now we want to create the intermedaitory
        db_ai = db.execute(ai_table.insert().values(
            type="media",
        ))
        db_ai = db.execute(ai_table.select(
            ai_table.c.id==db_ai.inserted_primary_key[0]
        )).first()

        # Add the activity
        activity = {
            "verb": "create",
            "actor": media.uploader,
            "published": media.created,
            "updated": media.created,
            "generator": gmg_generator.id,
            "object": db_ai.id
        }
        db.execute(activity_table.insert().values(**activity))

        # Add the AI to the media.
        db.execute(media_entry_table.update().values(
            activity=db_ai.id
        ).where(media_entry_table.c.id==media.id))

    # Now we want to add all the comments people made
    for comment in db.execute(media_comments_table.select()):
        # Get the MediaEntry for the comment
        media_entry = db.execute(
            media_entry_table.select(
                media_entry_table.c.id==comment.media_entry
        )).first()

        # Create an AI for target
        db_ai_media = db.execute(ai_table.select(
            ai_table.c.id==media_entry.activity
        )).first().id

        db.execute(
            media_comments_table.update().values(
                activity=db_ai_media
        ).where(media_comments_table.c.id==media_entry.id))

        # Now create the AI for the comment
        db_ai_comment = db.execute(ai_table.insert().values(
            type="comment"
        )).inserted_primary_key[0]

        activity = {
            "verb": "comment",
            "actor": comment.author,
            "published": comment.created,
            "updated": comment.created,
            "generator": gmg_generator.id,
            "object": db_ai_comment,
            "target": db_ai_media,
        }

        # Now add the comment object
        db.execute(activity_table.insert().values(**activity))

        # Now add activity to comment
        db.execute(media_comments_table.update().values(
            activity=db_ai_comment
        ).where(media_comments_table.c.id==comment.id))

    # Create 'create' activities for all collections
    for collection in db.execute(collection_table.select()):
        # create AI
        db_ai = db.execute(ai_table.insert().values(
            type="collection"
        ))
        db_ai = db.execute(ai_table.select(
            ai_table.c.id==db_ai.inserted_primary_key[0]
        )).first()

        # Now add link the collection to the AI
        db.execute(collection_table.update().values(
            activity=db_ai.id
        ).where(collection_table.c.id==collection.id))

        activity = {
            "verb": "create",
            "actor": collection.creator,
            "published": collection.created,
            "updated": collection.created,
            "generator": gmg_generator.id,
            "object": db_ai.id,
        }

        db.execute(activity_table.insert().values(**activity))

        # Now add the activity to the collection
        db.execute(collection_table.update().values(
            activity=db_ai.id
        ).where(collection_table.c.id==collection.id))

    db.commit()

class Location_V0(declarative_base()):
    __tablename__ = "core__locations"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    position = Column(MutationDict.as_mutable(JSONEncoded))
    address = Column(MutationDict.as_mutable(JSONEncoded))

@RegisterMigration(25, MIGRATIONS)
def add_location_model(db):
    """ Add location model """
    metadata = MetaData(bind=db.bind)

    # Create location table
    Location_V0.__table__.create(db.bind)
    db.commit()

    # Inspect the tables we need
    user = inspect_table(metadata, "core__users")
    collections = inspect_table(metadata, "core__collections")
    media_entry = inspect_table(metadata, "core__media_entries")
    media_comments = inspect_table(metadata, "core__media_comments")

    # Now add location support to the various models
    col = Column("location", Integer, ForeignKey(Location_V0.id))
    col.create(user)

    col = Column("location", Integer, ForeignKey(Location_V0.id))
    col.create(collections)

    col = Column("location", Integer, ForeignKey(Location_V0.id))
    col.create(media_entry)

    col = Column("location", Integer, ForeignKey(Location_V0.id))
    col.create(media_comments)

    db.commit()
