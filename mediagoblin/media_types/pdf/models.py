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


from mediagoblin.db.base import Base

from sqlalchemy import (
    Column, Float, Integer, String, DateTime, ForeignKey)
from sqlalchemy.orm import relationship, backref


BACKREF_NAME = "pdf__media_data"


class PdfData(Base):
    __tablename__ = "pdf__mediadata"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('core__media_entries.id'),
        primary_key=True)
    get_media_entry = relationship("MediaEntry",
        backref=backref(BACKREF_NAME, uselist=False,
                        cascade="all, delete-orphan"))
    pages = Column(Integer)

    # These are taken from what pdfinfo can do, perhaps others make sense too
    pdf_author = Column(String)
    pdf_title = Column(String)
    # note on keywords: this is the pdf parsed string, it should be considered a cached
    # value like the rest of these values, since they can be deduced at query time / client
    # side too.
    pdf_keywords = Column(String)
    pdf_creator = Column(String)
    pdf_producer = Column(String)
    pdf_creation_date = Column(DateTime)
    pdf_modified_date = Column(DateTime)
    pdf_version_major = Column(Integer)
    pdf_version_minor = Column(Integer)
    pdf_page_size_width = Column(Float) # unit: pts
    pdf_page_size_height = Column(Float)
    pdf_pages = Column(Integer)


DATA_MODEL = PdfData
MODELS = [PdfData]
