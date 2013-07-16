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

from mediagoblin.db.base import Base
from mediagoblin.db.models import Collection, User

from sqlalchemy import (
    Column, Integer, ForeignKey, Unicode, UnicodeText, DateTime)
from sqlalchemy.orm import relationship, backref

class Blog(Base):
	__tablename__ = "core__blogs"
	id = Column(Integer, primary_key=True)
	title = Column(Unicode)
	description = Column(UnicodeText)
	author = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
	created = Column(DateTime, nullable=False, default=datetime.datetime.now,
        index=True)
    
    
BACKREF_NAME = "blogpost__media_data"


class BlogpostData(Base):
    __tablename__ = "blogpost__mediadata"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('core__media_entries.id'),
        primary_key=True)
    get_media_entry = relationship("MediaEntry",
        backref=backref(BACKREF_NAME, uselist=False,
                        cascade="all, delete-orphan"))


DATA_MODEL = BlogpostData
MODELS = [BlogpostData]
