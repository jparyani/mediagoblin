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

from mediagoblin.db.sql.base import Base
from mediagoblin.db.sql.models import User

from sqlalchemy import (
        Column, Unicode, Integer, DateTime, ForeignKey)
from sqlalchemy.orm import relationship


class OAuthToken(Base):
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
    user = relationship(User)


class OAuthCode(Base):
    __tablename__ = 'oauth__codes'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False,
            default=datetime.now)
    expires = Column(DateTime, nullable=False,
            default=lambda: datetime.now() + timedelta(minutes=5))
    code = Column(Unicode, index=True)

    user_id = Column(Integer, ForeignKey(User.id), nullable=False,
            index=True)
    user = relationship(User)


MODELS = [OAuthToken, OAuthCode]
