from mediagoblin.db.sql.models import Base

from sqlalchemy import (
    Column, Integer, Unicode, UnicodeText, DateTime, Boolean, ForeignKey,
    UniqueConstraint)


class ImageData(Base):
    __tablename__ = "image_data"

    id = Column(Integer, primary_key=True)
    width = Column(Integer)
    height = Column(Integer)
    media_entry = Column(
        Integer, ForeignKey('media_entries.id'), nullable=False)


DATA_MODEL = ImageData
MODELS = [ImageData]
