from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class SongSection(Base):
    """
    An ordered section of a song.

    A song can be divided into distinct musical sections such as
    intro, main theme, improvisation, mawwal, or a modulation that
    moves to a different maqam.

    Sections are the honest way to represent maqam changes within
    a single song (e.g. a song that starts in Bayati then modulates
    to Saba). The primary maqam of the whole song remains stored on
    the Song itself and/or in SongMaqam with is_primary=True.
    """

    __tablename__ = "song_sections"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    song_id = Column(
        Integer,
        ForeignKey("songs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(
        String(255),
        nullable=True,
    )

    sequence_order = Column(
        Integer,
        nullable=False,
        default=0,
    )

    section_type = Column(
        String(50),
        nullable=True,
    )

    maqam_id = Column(
        Integer,
        ForeignKey("maqamat.id"),
        nullable=True,
    )

    rhythm_id = Column(
        Integer,
        ForeignKey("rhythms.id"),
        nullable=True,
    )

    tonic = Column(
        String(50),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    song = relationship(
        "Song",
        back_populates="sections",
    )

    maqam = relationship("Maqam")

    rhythm = relationship("Rhythm")
