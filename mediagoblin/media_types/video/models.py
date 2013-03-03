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
    Column, Integer, SmallInteger, ForeignKey)
from sqlalchemy.orm import relationship, backref
from mediagoblin.db.extratypes import JSONEncoded


BACKREF_NAME = "video__media_data"


class VideoData(Base):
    """
    Attributes:
     - media_data: the originating media entry (of course)
     - width: width of the transcoded video
     - height: height of the transcoded video
     - orig_metadata: A loose json structure containing metadata gstreamer
         pulled from the original video.
         This field is NOT GUARANTEED to exist!
    
         Likely metadata extracted:
           "videoheight", "videolength", "videowidth",
           "audiorate", "audiolength", "audiochannels", "audiowidth",
           "mimetype", "tags"
     
         TODO: document the above better.
    """
    __tablename__ = "video__mediadata"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('core__media_entries.id'),
        primary_key=True)
    get_media_entry = relationship("MediaEntry",
        backref=backref(BACKREF_NAME, uselist=False,
                        cascade="all, delete-orphan"))

    width = Column(SmallInteger)
    height = Column(SmallInteger)

    orig_metadata = Column(JSONEncoded)


DATA_MODEL = VideoData
MODELS = [VideoData]
