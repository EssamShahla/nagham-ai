"""
Tests for app/services/google_auth_service.py -- the account find/create/
link logic. This is the security-critical core of the Google auth feature:
in particular, that a matching email NEVER auto-links a Google identity to
an existing password account.
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.core.google_oauth import GoogleIdentity
from app.core.security import hash_password
from app.models.oauth_state import OAuthState
from app.models.user import User
from app.services.google_auth_service import (
    GoogleCallbackError,
    Linked,
    LinkRequired,
    LoggedIn,
    confirm_pending_link,
    consume_exchange_code,
    handle_callback,
    _handle_login_callback,
)

from tests.conftest import unique_email, unique_google_id


def make_local_user(db_session, **overrides) -> User:
    defaults = dict(
        name="Local User",
        email=unique_email(),
        password_hash=hash_password("S3curePassword!"),
        auth_provider="local",
        is_verified=True,
        profile_completed=True,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_new_google_identity_creates_a_new_user(db_session):
    identity = GoogleIdentity(
        google_id=unique_google_id(), email=unique_email(), name="Brand New", picture=None
    )

    result = _handle_login_callback(db_session, identity)

    assert isinstance(result, LoggedIn)
    user = consume_exchange_code(db_session, result.exchange_code)
    assert user is not None
    assert user.email == identity.email
    assert user.google_id == identity.google_id
    assert user.auth_provider == "google"
    assert user.password_hash is None
    assert user.is_verified is True  # Google already verified the email


def test_returning_google_user_logs_in_to_the_same_account(db_session):
    identity = GoogleIdentity(
        google_id=unique_google_id(), email=unique_email(), name="Returning", picture=None
    )

    first = _handle_login_callback(db_session, identity)
    first_user = consume_exchange_code(db_session, first.exchange_code)

    second = _handle_login_callback(db_session, identity)
    second_user = consume_exchange_code(db_session, second.exchange_code)

    assert first_user.id == second_user.id


def test_email_collision_does_not_auto_link(db_session):
    """The core security requirement: a Google identity whose email
    matches an existing LOCAL account must never be linked automatically."""

    local_user = make_local_user(db_session)
    identity = GoogleIdentity(
        google_id=unique_google_id(), email=local_user.email, name="Impersonator?", picture=None
    )

    result = _handle_login_callback(db_session, identity)

    assert isinstance(result, LinkRequired)
    db_session.refresh(local_user)
    assert local_user.google_id is None  # NOT auto-linked


def test_exchange_code_is_single_use(db_session):
    identity = GoogleIdentity(
        google_id=unique_google_id(), email=unique_email(), name="X", picture=None
    )
    result = _handle_login_callback(db_session, identity)

    first = consume_exchange_code(db_session, result.exchange_code)
    assert first is not None

    second = consume_exchange_code(db_session, result.exchange_code)
    assert second is None


def test_only_the_matching_account_can_confirm_a_pending_link(db_session):
    local_user = make_local_user(db_session)
    other_user = make_local_user(db_session)

    identity = GoogleIdentity(
        google_id=unique_google_id(), email=local_user.email, name="X", picture=None
    )
    result = _handle_login_callback(db_session, identity)
    assert isinstance(result, LinkRequired)

    with pytest.raises(GoogleCallbackError):
        confirm_pending_link(db_session, other_user, result.link_token)

    # The wrong attempt must not have burned the token for the real owner.
    linked_user = confirm_pending_link(db_session, local_user, result.link_token)
    assert linked_user.google_id == identity.google_id


def test_pending_link_token_is_single_use(db_session):
    local_user = make_local_user(db_session)
    identity = GoogleIdentity(
        google_id=unique_google_id(), email=local_user.email, name="X", picture=None
    )
    result = _handle_login_callback(db_session, identity)

    confirm_pending_link(db_session, local_user, result.link_token)

    with pytest.raises(GoogleCallbackError, match="already been used"):
        confirm_pending_link(db_session, local_user, result.link_token)


def test_login_with_an_already_linked_google_id_logs_into_its_owner(db_session):
    """A returning Google sign-in (not a linking attempt) with a google_id
    that already belongs to some account must just log into THAT account
    -- this is normal returning-user behavior, not a collision."""

    owner = make_local_user(db_session, google_id=unique_google_id())
    identity = GoogleIdentity(
        google_id=owner.google_id, email=unique_email(), name="X", picture=None,
    )

    result = _handle_login_callback(db_session, identity)

    assert isinstance(result, LoggedIn)
    logged_in_user = consume_exchange_code(db_session, result.exchange_code)
    assert logged_in_user.id == owner.id


def test_explicit_link_rejects_a_google_identity_already_linked_elsewhere(db_session, monkeypatch):
    """The proactive "Connect Google" flow: if the Google identity is
    already linked to a DIFFERENT account, the link must be refused."""

    already_linked_owner = make_local_user(db_session, google_id=unique_google_id())
    other_local_user = make_local_user(db_session)

    identity = GoogleIdentity(
        google_id=already_linked_owner.google_id,
        email=unique_email(),
        name="X",
        picture=None,
    )

    db_session.add(OAuthState(
        state="state-conflict-link",
        nonce="nonce-conflict-link",
        code_verifier="verifier",
        purpose="link",
        linking_user_id=other_local_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        is_used=False,
    ))
    db_session.commit()

    from app.services import google_auth_service as service

    monkeypatch.setattr(service, "exchange_code_for_id_token", lambda code, code_verifier: "fake-id-token")
    monkeypatch.setattr(service, "verify_google_id_token", lambda id_token_str, expected_nonce: identity)

    with pytest.raises(GoogleCallbackError, match="already linked"):
        handle_callback(db_session, code="whatever", state="state-conflict-link")

    db_session.refresh(other_local_user)
    assert other_local_user.google_id is None


def test_explicit_authenticated_linking_succeeds(db_session, monkeypatch):
    """The proactive "Connect Google" path: already authenticated, no
    email collision involved at all."""

    user = make_local_user(db_session)
    identity = GoogleIdentity(
        google_id=unique_google_id(), email=unique_email(), name="X", picture=None
    )

    db_session.add(OAuthState(
        state="state-explicit-link",
        nonce="nonce-explicit-link",
        code_verifier="verifier",
        purpose="link",
        linking_user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        is_used=False,
    ))
    db_session.commit()

    from app.services import google_auth_service as service

    monkeypatch.setattr(service, "exchange_code_for_id_token", lambda code, code_verifier: "fake-id-token")
    monkeypatch.setattr(service, "verify_google_id_token", lambda id_token_str, expected_nonce: identity)

    result = handle_callback(db_session, code="whatever", state="state-explicit-link")

    assert isinstance(result, Linked)
    assert result.user.id == user.id
    assert result.user.google_id == identity.google_id


@pytest.mark.parametrize(
    "setup_state,expected_message_fragment",
    [
        ("expired", "expired"),
        ("used", "already been used"),
        ("missing", "invalid"),
    ],
)
def test_callback_rejects_bad_oauth_state(db_session, setup_state, expected_message_fragment):
    state_value = f"state-{setup_state}-{unique_google_id()}"

    if setup_state == "expired":
        db_session.add(OAuthState(
            state=state_value, nonce="n", code_verifier="v", purpose="login",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1), is_used=False,
        ))
        db_session.commit()
    elif setup_state == "used":
        db_session.add(OAuthState(
            state=state_value, nonce="n", code_verifier="v", purpose="login",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5), is_used=True,
        ))
        db_session.commit()
    # "missing": don't insert anything at all

    with pytest.raises(GoogleCallbackError, match=expected_message_fragment):
        handle_callback(db_session, code="whatever", state=state_value)


def test_oauth_state_cannot_be_replayed_even_if_processing_fails_after(db_session, monkeypatch):
    """Once a state is looked up, it must be marked used immediately --
    even if token exchange subsequently fails -- so it can never be
    replayed. Token exchange is monkeypatched to fail deterministically
    (no real network call to Google in this test)."""

    from app.services import google_auth_service as service

    def always_fails(code, code_verifier):
        raise RuntimeError("simulated token-exchange failure")

    monkeypatch.setattr(service, "exchange_code_for_id_token", always_fails)

    state_value = f"state-replay-{unique_google_id()}"
    db_session.add(OAuthState(
        state=state_value, nonce="n", code_verifier="v", purpose="login",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5), is_used=False,
    ))
    db_session.commit()

    with pytest.raises(GoogleCallbackError):
        handle_callback(db_session, code="not-a-real-code", state=state_value)

    # Second call with the same state must be rejected as already-used,
    # not re-attempt the exchange.
    with pytest.raises(GoogleCallbackError, match="already been used"):
        handle_callback(db_session, code="not-a-real-code", state=state_value)
