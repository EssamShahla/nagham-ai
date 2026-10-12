from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=True
    )

    phone = Column(
        String(30),
        nullable=True
    )

    country = Column(
        String(100),
        nullable=True
    )

    city = Column(
        String(100),
        nullable=True
    )

    instrument = Column(
        String(100),
        nullable=True
    )
    
    profile_completed = Column(
    Boolean,
    default=False,
    nullable=False
)

    music_role = Column(
        String(100),
        nullable=True
    )

    years_of_experience = Column(
        Integer,
        nullable=True
    )

    bio = Column(
        Text,
        nullable=True
    )

    is_verified = Column(
        Boolean,
        default=False
    )

    auth_provider = Column(
        String(50),
        default="local"
    )

    google_id = Column(
        String(255),
        unique=True,
        nullable=True
    )

    role = Column(
        String(50),
        default="user"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    @property
    def google_linked(self) -> bool:
        return self.google_id is not None