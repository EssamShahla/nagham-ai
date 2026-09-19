from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Maqam(Base):
    __tablename__ = "maqamat"

    id = Column(Integer, primary_key=True, index=True)

    name_ar = Column(
        String(100),
        nullable=False,
        unique=True
    )

    name_en = Column(
        String(100),
        nullable=True
    )

    # Reference tonic of the maqam
    tonic = Column(
        String(50),
        nullable=True
    )

    accidentals = Column(
        String(255),
        nullable=True
    )

    # Example:
    # [0.75, 0.75, 1.0, 1.0, 0.5, 1.0, 1.0]
    scale_pattern = Column(
        JSON,
        nullable=True
    )

    root_jins_id = Column(
        Integer,
        ForeignKey("ajnas.id"),
        nullable=True
    )

    branch_jins_id = Column(
        Integer,
        ForeignKey("ajnas.id"),
        nullable=True
    )

    ghammaz = Column(
        String(50),
        nullable=True
    )

    mood = Column(
        String(255),
        nullable=True
    )

    notation_format = Column(
        String(50),
        nullable=False,
        default="musicxml"
    )

    musicxml_data = Column(
        Text,
        nullable=True
    )

    audio_sample_url = Column(
        String(500),
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    root_jins = relationship(
        "Jins",
        foreign_keys=[root_jins_id]
    )

    branch_jins = relationship(
        "Jins",
        foreign_keys=[branch_jins_id]
    )