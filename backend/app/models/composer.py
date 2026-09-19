from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database.base import Base


class Composer(Base):
    __tablename__ = "composers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name_ar = Column(
        String(255),
        nullable=False
    )

    name_en = Column(
        String(255),
        nullable=True
    )

    bio = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )