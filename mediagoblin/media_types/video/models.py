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
from mediagoblin.media_types import video


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

    def source_type(self):
        """
        Construct a useful type=... that is to say, used like:
          <video><source type="{{ entry.media_data.source_type() }}" /></video>

        Try to construct it out of self.orig_metadata... if we fail we
        just dope'ily fall back on DEFAULT_WEBM_TYPE
        """
        orig_metadata = self.orig_metadata or {}

        if "webm_video" not in self.get_media_entry.media_files \
           and "mimetype" in orig_metadata \
           and "tags" in orig_metadata \
           and "audio-codec" in orig_metadata["tags"] \
           and "video-codec" in orig_metadata["tags"]:
            if orig_metadata['mimetype'] == 'application/ogg':
                # stupid ambiguous .ogg extension
                mimetype = "video/ogg"
            else:
                mimetype = orig_metadata['mimetype']

            video_codec = orig_metadata["tags"]["video-codec"].lower()
            audio_codec = orig_metadata["tags"]["audio-codec"].lower()

            # We don't want the "video" at the end of vp8...
            # not sure of a nicer way to be cleaning this stuff
            if video_codec == "vp8 video":
                video_codec = "vp8"

            return '%s; codecs="%s, %s"' % (
                mimetype, video_codec, audio_codec)
        else:
            return video.VideoMediaManager.default_webm_type


DATA_MODEL = VideoData
MODELS = [VideoData]
