"""
Google sign-in business logic: who a verified Google identity maps to in
our database, and the account-linking rules.

Security rule this module enforces throughout: a matching email address is
NEVER sufficient on its own to attach a Google identity to an existing
local account. Email addresses can be recycled/reassigned over time, and
auto-linking on email match alone is a known account-takeover vector.
Linking an existing account always requires one of:
  (a) the user was already authenticated (JWT) when they started the
      Google flow (explicit, in-session linking from their profile), or
  (b) the user proves control of the existing account by logging into it
      with its password, then confirms the link in a second explicit step.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.google_oauth import (
    GoogleIdentity,
    GoogleOAuthNotConfigured,
    GoogleTokenError,
    build_google_authorize_url,
    exchange_code_for_id_token,
    generate_nonce,
    generate_pkce_pair,
    generate_state,
    verify_google_id_token,
)
from app.models.login_exchange_code import LoginExchangeCode
from app.models.oauth_state import OAuthState
from app.models.pending_google_link import PendingGoogleLink
from app.models.user import User

STATE_TTL = timedelta(minutes=10)
LINK_TTL = timedelta(minutes=10)
EXCHANGE_CODE_TTL = timedelta(minutes=2)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def start_login(db: Session) -> str:
    """Begin a fresh (unauthenticated) Google sign-in attempt. Returns the
    URL to redirect the user's browser to."""

    return _start(db, purpose="login", linking_user_id=None)


def start_link(db: Session, current_user: User) -> str:
    """Begin an explicit, already-authenticated Google linking attempt
    (e.g. a "Connect Google" button in account settings)."""

    return _start(db, purpose="link", linking_user_id=current_user.id)


def _start(db: Session, purpose: str, linking_user_id: int | None) -> str:
    state = generate_state()
    nonce = generate_nonce()
    code_verifier, code_challenge = generate_pkce_pair()

    db.add(OAuthState(
        state=state,
        nonce=nonce,
        code_verifier=code_verifier,
        purpose=purpose,
        linking_user_id=linking_user_id,
        expires_at=_utcnow() + STATE_TTL,
        is_used=False,
    ))
    db.commit()

    return build_google_authorize_url(state=state, nonce=nonce, code_challenge=code_challenge)


class GoogleCallbackError(Exception):
    """Safe-to-display error for the callback endpoint to surface."""


@dataclass(frozen=True)
class LoggedIn:
    exchange_code: str


@dataclass(frozen=True)
class LinkRequired:
    link_token: str


@dataclass(frozen=True)
class Linked:
    user: User


CallbackResult = LoggedIn | LinkRequired | Linked


def handle_callback(db: Session, code: str, state: str) -> CallbackResult:
    oauth_state = (
        db.query(OAuthState)
        .filter(OAuthState.state == state)
        .first()
    )

    if oauth_state is None:
        raise GoogleCallbackError("This sign-in attempt is invalid. Please try again.")

    # Mark used immediately (before any further processing) so the same
    # state can never be replayed, even if something below fails.
    already_used = oauth_state.is_used
    oauth_state.is_used = True
    db.commit()

    if already_used:
        raise GoogleCallbackError("This sign-in attempt has already been used. Please try again.")

    if oauth_state.expires_at < _utcnow():
        raise GoogleCallbackError("This sign-in attempt has expired. Please try again.")

    try:
        id_token_str = exchange_code_for_id_token(code, oauth_state.code_verifier)
        identity = verify_google_id_token(id_token_str, expected_nonce=oauth_state.nonce)
    except (GoogleTokenError, GoogleOAuthNotConfigured) as exc:
        # These already carry safe, user-facing messages.
        raise GoogleCallbackError(str(exc)) from exc
    except Exception as exc:
        # Anything else is unexpected -- never surface raw internal
        # exception text in a redirect URL the browser will show/log.
        raise GoogleCallbackError(
            "Something went wrong completing Google sign-in. Please try again."
        ) from exc

    if oauth_state.purpose == "link":
        return _handle_link_callback(db, oauth_state.linking_user_id, identity)

    return _handle_login_callback(db, identity)


def _handle_login_callback(db: Session, identity: GoogleIdentity) -> CallbackResult:
    existing_by_google_id = (
        db.query(User).filter(User.google_id == identity.google_id).first()
    )

    if existing_by_google_id is not None:
        return LoggedIn(exchange_code=_create_exchange_code(db, existing_by_google_id))

    existing_by_email = db.query(User).filter(User.email == identity.email).first()

    if existing_by_email is not None:
        # A matching email is NOT proof of ownership -- never auto-link.
        return LinkRequired(link_token=_create_pending_link(db, identity, existing_by_email))

    new_user = User(
        name=identity.name or identity.email.split("@")[0],
        email=identity.email,
        password_hash=None,
        auth_provider="google",
        google_id=identity.google_id,
        is_verified=True,  # Google already verified this email address.
        profile_completed=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return LoggedIn(exchange_code=_create_exchange_code(db, new_user))


def _handle_link_callback(
    db: Session,
    linking_user_id: int | None,
    identity: GoogleIdentity,
) -> CallbackResult:
    if linking_user_id is None:
        raise GoogleCallbackError("This linking attempt is invalid. Please try again.")

    current_user = db.query(User).filter(User.id == linking_user_id).first()
    if current_user is None:
        raise GoogleCallbackError("Your account could not be found. Please log in again.")

    conflicting_user = (
        db.query(User)
        .filter(User.google_id == identity.google_id, User.id != current_user.id)
        .first()
    )
    if conflicting_user is not None:
        raise GoogleCallbackError(
            "This Google account is already linked to a different Nagham AI account."
        )

    other_user_with_email = (
        db.query(User)
        .filter(User.email == identity.email, User.id != current_user.id)
        .first()
    )
    if other_user_with_email is not None:
        raise GoogleCallbackError(
            "This Google account's email belongs to a different Nagham AI account."
        )

    current_user.google_id = identity.google_id
    db.commit()
    db.refresh(current_user)

    return Linked(user=current_user)


def _create_pending_link(db: Session, identity: GoogleIdentity, existing_user: User) -> str:
    link_token = secrets.token_urlsafe(32)

    db.add(PendingGoogleLink(
        link_token=link_token,
        google_id=identity.google_id,
        google_email=identity.email,
        google_name=identity.name,
        existing_user_id=existing_user.id,
        expires_at=_utcnow() + LINK_TTL,
        is_used=False,
    ))
    db.commit()

    return link_token


def confirm_pending_link(db: Session, current_user: User, link_token: str) -> User:
    """
    Second half of the explicit account-linking flow: the user has now
    authenticated (e.g. logged in with their password) and is confirming
    the link we proposed in `_create_pending_link`.
    """

    pending = (
        db.query(PendingGoogleLink)
        .filter(PendingGoogleLink.link_token == link_token)
        .first()
    )

    if pending is None:
        raise GoogleCallbackError("This linking request is invalid.")

    # Validate everything BEFORE marking the token used (and before the
    # final commit). A wrong/unauthorized caller must not be able to burn
    # the legitimate owner's single-use token just by attempting it --
    # only a successful confirmation consumes it.
    if pending.is_used:
        raise GoogleCallbackError("This linking request has already been used.")

    if pending.expires_at < _utcnow():
        raise GoogleCallbackError("This linking request has expired. Please sign in with Google again.")

    # The authenticated user confirming the link MUST be the same account
    # the pending link was created for -- otherwise a different logged-in
    # user could hijack someone else's pending link.
    if pending.existing_user_id != current_user.id:
        raise GoogleCallbackError(
            "This linking request does not belong to the currently signed-in account."
        )

    conflicting_user = (
        db.query(User)
        .filter(User.google_id == pending.google_id, User.id != current_user.id)
        .first()
    )
    if conflicting_user is not None:
        raise GoogleCallbackError(
            "This Google account is already linked to a different Nagham AI account."
        )

    current_user.google_id = pending.google_id
    pending.is_used = True
    db.commit()
    db.refresh(current_user)

    return current_user


def _create_exchange_code(db: Session, user: User) -> str:
    code = secrets.token_urlsafe(32)

    db.add(LoginExchangeCode(
        code=code,
        user_id=user.id,
        expires_at=_utcnow() + EXCHANGE_CODE_TTL,
        is_used=False,
    ))
    db.commit()

    return code


def consume_exchange_code(db: Session, code: str) -> User | None:
    record = db.query(LoginExchangeCode).filter(LoginExchangeCode.code == code).first()

    if record is None:
        return None

    already_used = record.is_used
    record.is_used = True
    db.commit()

    if already_used or record.expires_at < _utcnow():
        return None

    return db.query(User).filter(User.id == record.user_id).first()
