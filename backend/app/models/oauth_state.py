from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class OAuthState(Base):
    """
    One in-flight Google OAuth attempt (Authorization Code + PKCE).

    Created when we redirect the user to Google, looked up and immediately
    marked used when Google redirects back -- this is what lets the
    callback validate `state`, recover the PKCE `code_verifier` and the
    `nonce` without needing a client-side cookie to survive the
    cross-site round trip to Google and back.
    """

    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)

    state = Column(String(255), unique=True, nullable=False, index=True)
    nonce = Column(String(255), nullable=False)
    code_verifier = Column(String(255), nullable=False)

    # "login": a fresh sign-in/sign-up attempt (not yet authenticated).
    # "link": the user is already authenticated and explicitly asked to
    # link their Google identity from their profile -- in this case
    # `linking_user_id` identifies them, and the callback can link
    # directly without requiring a second password re-entry.
    purpose = Column(String(20), nullable=False, default="login")

    linking_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
