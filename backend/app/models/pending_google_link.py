from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class PendingGoogleLink(Base):
    """
    A verified Google identity whose email matched an EXISTING local
    account during a fresh sign-in attempt.

    We never auto-link in that situation (a matching email is not proof
    of account ownership -- e.g. a recycled/reassigned email address).
    This row holds the verified Google identity just long enough for the
    rightful owner to prove they control the existing account (by logging
    in with their password) and then explicitly confirm the link via
    POST /auth/google/link. Single-use, short-lived.
    """

    __tablename__ = "pending_google_links"

    id = Column(Integer, primary_key=True, index=True)

    link_token = Column(String(255), unique=True, nullable=False, index=True)

    google_id = Column(String(255), nullable=False)
    google_email = Column(String(255), nullable=False)
    google_name = Column(String(255), nullable=True)

    existing_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    existing_user = relationship("User")
