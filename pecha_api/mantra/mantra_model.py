from sqlalchemy import Column, String, DateTime, UUID, Text
from ..db.database import Base
from ..plans.plans_enums import LanguageCodeEnum
from uuid import uuid4
import _datetime
from _datetime import datetime


class Mantra(Base):
    __tablename__ = "mantra"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    audio_url = Column(String(1000), nullable=True)
    text = Column(Text, nullable=False)
    meaning = Column(Text, nullable=True)
    language = Column(LanguageCodeEnum, nullable=False, default='EN')

    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))
