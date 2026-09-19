from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database.base import Base


class Rhythm(Base):
    __tablename__ = "rhythms"

    id = Column(Integer, primary_key=True, index=True)

    # Names
    name_ar = Column(String(100), nullable=False, unique=True)
    name_en = Column(String(100), nullable=True)

    # Musical meter
    # Examples: 4/4, 6/8, 10/8
    time_signature = Column(String(20), nullable=True)

    # Human / AI readable rhythm representation
    # Example: D T - T D - T -
    pattern_text = Column(String(255), nullable=True)

    # Musical notation
    notation_format = Column(
        String(50),
        nullable=False,
        default="musicxml"
    )

    # Full MusicXML content
    musicxml_data = Column(Text, nullable=True)

    # Audio example
    audio_sample_url = Column(String(500), nullable=True)

    # BPM of the provided audio sample only
    # NOT a fixed BPM for the rhythm itself
    sample_bpm = Column(Integer, nullable=True)

    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )