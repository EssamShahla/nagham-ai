from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from app.database.base import Base


class Jins(Base):
    __tablename__ = "ajnas"

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

    # Reference tonic of the jins
    tonic = Column(
        String(50),
        nullable=True
    )

    # Example:
    # "مي نصف بيمول"
    accidentals = Column(
        String(255),
        nullable=True
    )

    # Stored as JSON array.
    # Example:
    # [0.75, 0.75, 1.0]
    scale_pattern = Column(
        JSON,
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