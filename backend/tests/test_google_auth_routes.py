"""
Endpoint-level tests for the Google auth routes, via FastAPI's TestClient.
Exercises the full HTTP contract: redirects, status codes, and that the
real JWT never appears in a URL at any point.
"""

from urllib.parse import parse_qs, urlparse

from app.core.google_oauth import GoogleIdentity


def test_google_login_redirects_to_google_with_pkce_state_nonce(client):
    response = client.get("/auth/google/login", follow_redirects=False)

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth?")

    query = parse_qs(urlparse(location).query)
    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert "code_challenge" in query
    assert "state" in query
    assert "nonce" in query
    assert "client_secret" not in location


def test_google_login_requires_auth_header_is_not_sent(client):
    """/auth/google/login must NOT require authentication -- it's the
    entry point for both sign-in and sign-up."""

    response = client.get("/auth/google/login", follow_redirects=False)
    assert response.status_code == 302  # not 401/403


def test_google_link_start_requires_authentication(client):
    response = client.get("/auth/google/link/start")
    assert response.status_code in (401, 403)


def test_callback_handles_cancellation_gracefully(client):
    response = client.get(
        "/auth/google/callback",
        params={"error": "access_denied"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("http://localhost:3000/login?google_error=")
    # The real JWT concept doesn't even apply here, but make sure nothing
    # resembling a bearer token leaks into the redirect either way.
    assert "access_token" not in location


def test_callback_handles_missing_parameters_gracefully(client):
    response = client.get("/auth/google/callback", follow_redirects=False)

    assert response.status_code == 302
    assert "google_error=" in response.headers["location"]


def test_callback_rejects_unknown_state(client):
    response = client.get(
        "/auth/google/callback",
        params={"code": "whatever", "state": "never-issued-state"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "google_error=" in response.headers["location"]


def test_exchange_rejects_invalid_code(client):
    response = client.post("/auth/google/exchange", json={"code": "not-a-real-code"})
    assert response.status_code == 400


def test_full_new_user_login_round_trip_never_puts_jwt_in_a_url(client, monkeypatch):
    """End-to-end through the actual router layer: login redirect -> (fake
    Google) -> callback -> frontend redirect with an opaque exchange code
    -> POST exchange -> real JWT -> /auth/me works with it."""

    # Step 1: start the flow for real, to get a valid state/nonce/verifier
    # recorded server-side exactly like a real browser would trigger.
    start_response = client.get("/auth/google/login", follow_redirects=False)
    state = parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]

    # Step 2: stand in for Google's token endpoint + ID token verification
    # (no real network call to Google in this test).
    fake_identity = GoogleIdentity(
        google_id="google-route-test-id",
        email="route-test-user@example.com",
        name="Route Test User",
        picture=None,
    )

    import app.routers.auth as auth_router_module

    monkeypatch.setattr(
        auth_router_module, "handle_callback",
        lambda db, code, state: auth_router_module.LoggedIn(
            exchange_code=_make_real_exchange_code(fake_identity)
        ),
    )

    callback_response = client.get(
        "/auth/google/callback",
        params={"code": "fake-google-code", "state": state},
        follow_redirects=False,
    )

    assert callback_response.status_code == 302
    redirect_location = callback_response.headers["location"]
    assert redirect_location.startswith("http://localhost:3000/auth/google/callback?code=")

    exchange_code = parse_qs(urlparse(redirect_location).query)["code"][0]

    # Step 3: the frontend's POST exchange -- this is the ONLY place the
    # real JWT is ever transmitted, and it's in a JSON response body, not
    # a URL.
    exchange_response = client.post("/auth/google/exchange", json={"code": exchange_code})
    assert exchange_response.status_code == 200
    token = exchange_response.json()["access_token"]
    assert token  # a real JWT string

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == fake_identity.email
    assert me_response.json()["google_linked"] is True


def _make_real_exchange_code(identity: GoogleIdentity) -> str:
    """Helper: drives the real service logic to produce a genuine,
    database-backed exchange code for `fake_identity`, so step 3 above
    exercises the real consume_exchange_code path end to end."""

    from app.database.connection import SessionLocal
    from app.services.google_auth_service import _handle_login_callback

    db = SessionLocal()
    try:
        result = _handle_login_callback(db, identity)
        return result.exchange_code
    finally:
        db.close()
