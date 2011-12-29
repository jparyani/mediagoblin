from mediagoblin.db.sql.models import Base

from sqlalchemy import (
    Column, Integer, Unicode, UnicodeText, DateTime, Boolean, ForeignKey,
    UniqueConstraint)


class ImageData(Base):
    __tablename__ = "image__data"

    id = Column(Integer, primary_key=True)
    width = Column(Integer)
    height = Column(Integer)


DATA_MODEL = ImageData
MODELS = [ImageData]
