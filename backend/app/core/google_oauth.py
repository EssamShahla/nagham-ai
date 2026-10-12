"""
Google OAuth 2.0 / OpenID Connect -- Authorization Code flow with PKCE.

This is a confidential-client (server-side) flow: the backend holds
GOOGLE_CLIENT_SECRET and performs the authorization-code exchange itself.
PKCE is layered on top anyway (per the project's security requirements) as
defense-in-depth against authorization-code interception -- it is not
required for a confidential client, but it costs little and closes one
more attack path.

Nothing here decides *who* a Google identity maps to in our database --
that's `app/services/google_auth_service.py`. This module only talks to
Google and verifies what Google says.
"""

import base64
import hashlib
import os
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import requests
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token


# Google's stable, documented endpoints (https://developers.google.com/identity/protocols/oauth2/web-server).
# Not fetched from the OIDC discovery document on every request: that
# document itself would need to be fetched over HTTPS and (for real
# security) pinned/verified too, and Google has not changed these URLs in
# over a decade. Hardcoding them avoids an extra network round trip and an
# extra thing that can fail at runtime.
GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

GOOGLE_SCOPES = "openid email profile"


class GoogleOAuthNotConfigured(Exception):
    """Raised when GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / the redirect
    URI are not set. The app must still start without them (Google sign-in
    is an optional feature) -- this is only raised when a Google-auth
    endpoint is actually invoked."""


class GoogleTokenError(Exception):
    """Raised when Google's response or ID token fails any verification
    check. The message is safe to show to the end user (never includes
    secrets)."""


def _get_config() -> tuple[str, str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if not client_id or not client_secret or not redirect_uri:
        raise GoogleOAuthNotConfigured(
            "Google sign-in is not configured on this server. Set "
            "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and "
            "GOOGLE_REDIRECT_URI in the backend .env file."
        )

    return client_id, client_secret, redirect_uri


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def generate_pkce_pair() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge) per RFC 7636 (S256)."""

    code_verifier = secrets.token_urlsafe(64)  # 86 chars, within the 43-128 range

    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    return code_verifier, code_challenge


def build_google_authorize_url(state: str, nonce: str, code_challenge: str) -> str:
    client_id, _client_secret, redirect_uri = _get_config()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        # Only ask for what we need; no offline/refresh access to Google.
        "access_type": "online",
        "include_granted_scopes": "false",
        "prompt": "select_account",
    }

    return f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def exchange_code_for_id_token(code: str, code_verifier: str) -> str:
    """
    Exchanges an authorization code for tokens at Google's token endpoint
    and returns the raw (still-unverified) id_token JWT string.
    """

    client_id, client_secret, redirect_uri = _get_config()

    try:
        response = requests.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        raise GoogleTokenError("Could not reach Google's token endpoint.") from exc

    if response.status_code != 200:
        raise GoogleTokenError(
            "Google rejected the authorization code (it may have expired, "
            "already been used, or the redirect URI doesn't match)."
        )

    payload = response.json()
    id_token_str = payload.get("id_token")

    if not id_token_str:
        raise GoogleTokenError("Google's token response did not include an ID token.")

    return id_token_str


@dataclass(frozen=True)
class GoogleIdentity:
    google_id: str
    email: str
    name: str | None
    picture: str | None


def verify_google_id_token(id_token_str: str, expected_nonce: str) -> GoogleIdentity:
    """
    Full verification per the project's security requirements:
    signature (via Google's published JWKS), issuer, audience, expiration
    -- all performed by google-auth's `verify_oauth2_token` -- plus nonce
    match and verified-email status, checked here.
    """

    client_id, _client_secret, _redirect_uri = _get_config()

    try:
        claims = google_id_token.verify_oauth2_token(
            id_token_str,
            GoogleAuthRequest(),
            audience=client_id,
        )
    except Exception as exc:
        raise GoogleTokenError("Google's ID token failed verification.") from exc

    if claims.get("nonce") != expected_nonce:
        raise GoogleTokenError("Google's ID token nonce did not match this sign-in attempt.")

    if not claims.get("email_verified"):
        raise GoogleTokenError("Google has not verified this account's email address.")

    email = claims.get("email")
    google_id = claims.get("sub")

    if not email or not google_id:
        raise GoogleTokenError("Google's ID token is missing required claims.")

    return GoogleIdentity(
        google_id=google_id,
        email=email,
        name=claims.get("name"),
        picture=claims.get("picture"),
    )
