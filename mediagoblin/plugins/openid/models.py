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
from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relationship, backref

from mediagoblin.db.models import User
from mediagoblin.db.base import Base


class OpenIDUserURL(Base):
    __tablename__ = "openid__user_urls"

    id = Column(Integer, primary_key=True)
    openid_url = Column(Unicode, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    # OpenID's are owned by their user, so do the full thing.
    user = relationship(User, backref=backref('openid_urls',
                                              cascade='all, delete-orphan'))


# OpenID Store Models
class Nonce(Base):
    __tablename__ = "openid__nonce"

    server_url = Column(Unicode, primary_key=True)
    timestamp = Column(Integer, primary_key=True)
    salt = Column(Unicode, primary_key=True)

    def __unicode__(self):
        return u'Nonce: %r, %r' % (self.server_url, self.salt)


class Association(Base):
    __tablename__ = "openid__association"

    server_url = Column(Unicode, primary_key=True)
    handle = Column(Unicode, primary_key=True)
    secret = Column(Unicode)
    issued = Column(Integer)
    lifetime = Column(Integer)
    assoc_type = Column(Unicode)

    def __unicode__(self):
        return u'Association: %r, %r' % (self.server_url, self.handle)


MODELS = [
    OpenIDUserURL,
    Nonce,
    Association
]
