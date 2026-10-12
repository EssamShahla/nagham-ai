"""
Unit tests for app/core/google_oauth.py: PKCE/state/nonce generation and
ID token verification. These never contact the real Google servers --
`verify_google_id_token`'s signature/issuer/audience/expiry checks are
delegated entirely to the `google-auth` library, so what's tested here is
(a) that a token NOT signed by a real Google key is rejected (proves the
signature check is actually wired up and not bypassed), and (b) our own
post-verification checks (nonce match, email_verified) given claims that
would otherwise pass -- by monkeypatching the one call that would
otherwise require real network access to Google's JWKS endpoint.
"""

import base64
import hashlib

import pytest
from jose import jwt as jose_jwt

from app.core.google_oauth import (
    GoogleTokenError,
    generate_nonce,
    generate_pkce_pair,
    generate_state,
    build_google_authorize_url,
    verify_google_id_token,
)


def test_state_and_nonce_are_unique_and_unguessable():
    values = {generate_state() for _ in range(50)}
    assert len(values) == 50
    assert all(len(v) >= 32 for v in values)


def test_pkce_pair_challenge_matches_verifier():
    code_verifier, code_challenge = generate_pkce_pair()

    expected_digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_digest).rstrip(b"=").decode("ascii")

    assert code_challenge == expected_challenge
    assert 43 <= len(code_verifier) <= 128


def test_authorize_url_contains_pkce_state_and_nonce():
    state = generate_state()
    nonce = generate_nonce()
    _verifier, challenge = generate_pkce_pair()

    url = build_google_authorize_url(state=state, nonce=nonce, code_challenge=challenge)

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert f"state={state}" in url
    assert f"nonce={nonce}" in url
    assert "code_challenge_method=S256" in url
    assert "response_type=code" in url
    assert "client_secret" not in url  # never leak the secret into a redirect URL


def test_forged_id_token_is_rejected_by_signature_check():
    """A token not signed by Google's real private key must never verify,
    no matter what claims it carries."""

    forged_claims = {
        "iss": "https://accounts.google.com",
        "aud": "test-client-id.apps.googleusercontent.com",
        "sub": "attacker-controlled-subject",
        "email": "attacker@example.com",
        "email_verified": True,
        "nonce": "expected-nonce",
        "exp": 9999999999,
    }
    forged_token = jose_jwt.encode(forged_claims, "attacker-controlled-secret", algorithm="HS256")

    with pytest.raises(GoogleTokenError):
        verify_google_id_token(forged_token, expected_nonce="expected-nonce")


def test_nonce_mismatch_is_rejected(monkeypatch):
    """Even if signature/issuer/audience/expiry all checked out, a nonce
    that doesn't match this sign-in attempt must be rejected (replay
    protection)."""

    import app.core.google_oauth as google_oauth_module

    monkeypatch.setattr(
        google_oauth_module.google_id_token,
        "verify_oauth2_token",
        lambda *a, **k: {
            "sub": "some-google-id",
            "email": "user@example.com",
            "email_verified": True,
            "nonce": "nonce-from-a-DIFFERENT-attempt",
        },
    )

    with pytest.raises(GoogleTokenError, match="nonce"):
        verify_google_id_token("irrelevant-with-mock", expected_nonce="expected-nonce")


def test_unverified_email_is_rejected(monkeypatch):
    import app.core.google_oauth as google_oauth_module

    monkeypatch.setattr(
        google_oauth_module.google_id_token,
        "verify_oauth2_token",
        lambda *a, **k: {
            "sub": "some-google-id",
            "email": "user@example.com",
            "email_verified": False,
            "nonce": "expected-nonce",
        },
    )

    with pytest.raises(GoogleTokenError, match="verified"):
        verify_google_id_token("irrelevant-with-mock", expected_nonce="expected-nonce")


def test_valid_claims_produce_identity(monkeypatch):
    import app.core.google_oauth as google_oauth_module

    monkeypatch.setattr(
        google_oauth_module.google_id_token,
        "verify_oauth2_token",
        lambda *a, **k: {
            "sub": "some-google-id-123",
            "email": "user@example.com",
            "email_verified": True,
            "nonce": "expected-nonce",
            "name": "Some User",
            "picture": "https://example.com/pic.jpg",
        },
    )

    identity = verify_google_id_token("irrelevant-with-mock", expected_nonce="expected-nonce")

    assert identity.google_id == "some-google-id-123"
    assert identity.email == "user@example.com"
    assert identity.name == "Some User"
