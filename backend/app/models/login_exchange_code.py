from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class LoginExchangeCode(Base):
    """
    A short-lived, single-use code handed to the browser via redirect
    after a successful Google sign-in, so the real JWT never travels in a
    URL (query params end up in browser history, server logs, and the
    Referer header). The frontend immediately exchanges this code for the
    actual access token via POST /auth/google/exchange.
    """

    __tablename__ = "login_exchange_codes"

    id = Column(Integer, primary_key=True, index=True)

    code = Column(String(255), unique=True, nullable=False, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
