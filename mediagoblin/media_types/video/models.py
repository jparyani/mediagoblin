from mediagoblin.db.sql.models import Base

from sqlalchemy import (
    Column, Integer, Unicode, UnicodeText, DateTime, Boolean, ForeignKey,
    UniqueConstraint)


class VideoData(Base):
    __tablename__ = "video__data"

    id = Column(Integer, primary_key=True)
    integer


DATA_MODEL = VideoData
MODELS = [VideoData]
