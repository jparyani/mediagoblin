from mediagoblin.db.sql.models import Base

from sqlalchemy import (
    Column, Integer, Float, ForeignKey)


class ImageData(Base):
    __tablename__ = "image_data"

    # The primary key *and* reference to the main media_entry
    media_entry = Column(Integer, ForeignKey('media_entries.id'),
        primary_key=True)
    width = Column(Integer)
    height = Column(Integer)
    gps_longitude = Column(Float)
    gps_latitude = Column(Float)
    gps_altitude = Column(Float)
    gps_direction = Column(Float)


DATA_MODEL = ImageData
MODELS = [ImageData]
