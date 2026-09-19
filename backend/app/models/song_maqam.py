from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class SongMaqam(Base):
    __tablename__ = "song_maqams"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    song_id = Column(
        Integer,
        ForeignKey("songs.id"),
        nullable=False
    )

    maqam_id = Column(
        Integer,
        ForeignKey("maqamat.id"),
        nullable=False
    )

    tonic = Column(
        String(50),
        nullable=True
    )

    is_primary = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    song = relationship("Song")

    maqam = relationship("Maqam")