from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database.base import Base
from app.models.song_section import SongSection  # noqa: F401  (registers mapper for the lazy "SongSection" relationship string)


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

    # Whether `lyrics` may ever be displayed verbatim: "public_domain" |
    # "licensed" | "restricted". NULL/unrecognized is always treated as
    # restricted by application code -- display rights are never assumed.
    # `lyrics` itself is kept regardless of license for semantic-search
    # embeddings (see app/ai/semantic_search.py:build_song_embedding_text).
    lyrics_license = Column(
        String(30),
        nullable=True
    )

    lyrics_rights_note = Column(
        Text,
        nullable=True
    )

    # Free-text, unresolved against any catalog table (unlike artist/
    # composer/maqam/rhythm) -- a song's lyricist and the specific
    # performed tonic/key, which can differ per song even within the
    # same maqam.
    lyricist_name = Column(
        String(255),
        nullable=True
    )

    musical_key = Column(
        String(100),
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

    sections = relationship(
        "SongSection",
        order_by="SongSection.sequence_order",
        passive_deletes=True,
        back_populates="song"
    )

    sources = relationship(
        "SongSource",
        passive_deletes=True,
        back_populates="song"
    )

    creator = relationship("User")