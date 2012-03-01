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


from mediagoblin.db.sql.models import Base

from sqlalchemy import (
    Column, Integer, SmallInteger, ForeignKey)


class VideoData(Base):
    __tablename__ = "video_data"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('media_entries.id'),
        primary_key=True)
    width = Column(SmallInteger)
    height = Column(SmallInteger)


DATA_MODEL = VideoData
MODELS = [VideoData]
