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

from datetime import datetime, timedelta
from sqlalchemy import (MetaData, Table, Column,
                        Integer, Unicode, Enum, DateTime, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base

from mediagoblin.db.migration_tools import RegisterMigration
from mediagoblin.db.models import User


MIGRATIONS = {}


class OAuthClient_v0(declarative_base()):
    __tablename__ = 'oauth__client'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False,
            default=datetime.now)

    name = Column(Unicode)
    description = Column(Unicode)

    identifier = Column(Unicode, unique=True, index=True)
    secret = Column(Unicode, index=True)

    owner_id = Column(Integer, ForeignKey(User.id))
    redirect_uri = Column(Unicode)

    type = Column(Enum(
        u'confidential',
        u'public',
        name=u'oauth__client_type'))


class OAuthUserClient_v0(declarative_base()):
    __tablename__ = 'oauth__user_client'
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey(User.id))
    client_id = Column(Integer, ForeignKey(OAuthClient_v0.id))

    state = Column(Enum(
        u'approved',
        u'rejected',
        name=u'oauth__relation_state'))


class OAuthToken_v0(declarative_base()):
    __tablename__ = 'oauth__tokens'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False,
            default=datetime.now)
    expires = Column(DateTime, nullable=False,
            default=lambda: datetime.now() + timedelta(days=30))
    token = Column(Unicode, index=True)
    refresh_token = Column(Unicode, index=True)

    user_id = Column(Integer, ForeignKey(User.id), nullable=False,
            index=True)

    client_id = Column(Integer, ForeignKey(OAuthClient_v0.id), nullable=False)

    def __repr__(self):
        return '<{0} #{1} expires {2} [{3}, {4}]>'.format(
                self.__class__.__name__,
                self.id,
                self.expires.isoformat(),
                self.user,
                self.client)


class OAuthCode_v0(declarative_base()):
    __tablename__ = 'oauth__codes'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False,
            default=datetime.now)
    expires = Column(DateTime, nullable=False,
            default=lambda: datetime.now() + timedelta(minutes=5))
    code = Column(Unicode, index=True)

    user_id = Column(Integer, ForeignKey(User.id), nullable=False,
            index=True)

    client_id = Column(Integer, ForeignKey(OAuthClient_v0.id), nullable=False)


class OAuthRefreshToken_v0(declarative_base()):
    __tablename__ = 'oauth__refresh_tokens'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False,
                     default=datetime.now)

    token = Column(Unicode, index=True)

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    # XXX: Is it OK to use OAuthClient_v0.id in this way?
    client_id = Column(Integer, ForeignKey(OAuthClient_v0.id), nullable=False)


@RegisterMigration(1, MIGRATIONS)
def remove_and_replace_token_and_code(db):
    metadata = MetaData(bind=db.bind)

    token_table = Table('oauth__tokens', metadata, autoload=True,
            autoload_with=db.bind)

    token_table.drop()

    code_table = Table('oauth__codes', metadata, autoload=True,
            autoload_with=db.bind)

    code_table.drop()

    OAuthClient_v0.__table__.create(db.bind)
    OAuthUserClient_v0.__table__.create(db.bind)
    OAuthToken_v0.__table__.create(db.bind)
    OAuthCode_v0.__table__.create(db.bind)

    db.commit()


@RegisterMigration(2, MIGRATIONS)
def remove_refresh_token_field(db):
    metadata = MetaData(bind=db.bind)

    token_table = Table('oauth__tokens', metadata, autoload=True,
                        autoload_with=db.bind)

    refresh_token = token_table.columns['refresh_token']

    refresh_token.drop()
    db.commit()

@RegisterMigration(3, MIGRATIONS)
def create_refresh_token_table(db):
    OAuthRefreshToken_v0.__table__.create(db.bind)

    db.commit()
