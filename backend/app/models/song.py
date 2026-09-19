from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database.base import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(255),
        nullable=False
    )

    lyrics = Column(
        Text,
        nullable=True
    )
    description = Column(
        Text,
        nullable=True
    )

    moods = Column(
        JSON,
        nullable=True
    )

    topics = Column(
        JSON,
        nullable=True
    )
    embedding = Column(
        Vector(384),
        nullable=True
    )

    year = Column(
        Integer,
        nullable=True
    )

    difficulty = Column(
        String(50),
        nullable=True
    )

    artist_id = Column(
        Integer,
        ForeignKey("artists.id"),
        nullable=False
    )

    composer_id = Column(
        Integer,
        ForeignKey("composers.id"),
        nullable=True
    )

    rhythm_id = Column(
        Integer,
        ForeignKey("rhythms.id"),
        nullable=True
    )

    maqam_id = Column(
        Integer,
        ForeignKey("maqamat.id"),
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

    artist = relationship("Artist")

    composer = relationship("Composer")

    rhythm = relationship("Rhythm")

    maqam = relationship("Maqam")

    sources = relationship(
        "SongSource",
        passive_deletes=True,
        back_populates="song"
    )

    creator = relationship("User")