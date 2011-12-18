import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, Integer, Unicode, UnicodeText, DateTime, Boolean, ForeignKey,
    UniqueConstraint)

from mediagoblin.db.sql.base import GMGTableBase


Base = declarative_base(cls=GMGTableBase)


class User(Base):
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
    bio = Column(UnicodeText) # ??
    bio_html = Column(UnicodeText) # ??
    fp_verification_key = Column(Unicode)
    fp_token_expire = Column(DateTime)

    ## TODO
    # plugin data would be in a separate model


class MediaEntry(Base):
    __tablename__ = "media_entries"

    id = Column(Integer, primary_key=True)
    uploader = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(Unicode, nullable=False)
    slug = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    description = Column(UnicodeText) # ??
    description_html = Column(UnicodeText) # ??
    media_type = Column(Unicode, nullable=False)
    
    fail_error = Column(Unicode)
    fail_metadata = Column(UnicodeText)

    queued_media_file = Column(Unicode)

    queued_task_id = Column(Unicode)

    __table_args__ = (
        UniqueConstraint('uploader', 'slug'),
        {})

    ## TODO
    # media_files
    # media_data
    # attachment_files
    # fail_error


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


def show_table_init():
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:', echo=True)

    Base.metadata.create_all(engine)


if __name__ == '__main__':
    show_table_init()
