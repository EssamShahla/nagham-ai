from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class SongSource(Base):
    __tablename__ = "song_sources"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    song_id = Column(
        Integer,
        ForeignKey("songs.id", ondelete="CASCADE"),
        nullable=False
    )

    source_type = Column(
        String(50),
        nullable=False
    )

    source_url = Column(
        String(500),
        nullable=True
    )

    title = Column(
        String(255),
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    song = relationship("Song", back_populates="sources")

    creator = relationship("User")