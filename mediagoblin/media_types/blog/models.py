# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors. See AUTHORS.
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
from mediagoblin.db.models import Collection, User, MediaEntry
from mediagoblin.db.mixin import GenerateSlugMixin

from mediagoblin.media_types.blog.lib import check_blog_slug_used

from mediagoblin.tools.text import cleaned_markdown_conversion

from sqlalchemy import (
    Column, Integer, ForeignKey, Unicode, UnicodeText, DateTime)
from sqlalchemy.orm import relationship, backref


class BlogMixin(GenerateSlugMixin):
    def check_slug_used(self, slug):
        return check_blog_slug_used(self.author, slug, self.id)

class Blog(Base, BlogMixin):
    __tablename__ = "mediatype__blogs"
    id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    description = Column(UnicodeText)
    author = Column(Integer, ForeignKey(User.id), nullable=False, index=True) #similar to uploader
    created = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    slug = Column(Unicode)
    
#class BlogPost(MediaEntry):
    #__tablename__ = "mediatype__blog_blogposts"
    #blog = Column(Integer, ForeignKey(Blog.id), nullable=False)
    
BACKREF_NAME = "blogpost__media_data"


class BlogpostData(Base):
    __tablename__ = "blogpost__mediadata"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('core__media_entries.id'), primary_key=True)
    get_media_entry = relationship("MediaEntry",
        backref=backref(BACKREF_NAME, uselist=False,
                        cascade="all, delete-orphan"))


DATA_MODEL = BlogpostData
MODELS = [BlogpostData, Blog]
