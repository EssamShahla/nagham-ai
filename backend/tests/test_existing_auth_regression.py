"""
Regression coverage: the existing email/password + OTP flow must keep
working exactly as before the Google auth feature was added.
"""

from app.models.otp_verification import OTPVerification
from app.models.user import User

from tests.conftest import unique_email


def test_register_login_otp_flow_still_works(client, db_session):
    email = unique_email()

    register_response = client.post(
        "/auth/register",
        json={
            "name": "Regression Tester",
            "email": email,
            "password": "S3curePassword!",
            "instrument": "Oud",
        },
    )
    assert register_response.status_code == 201
    body = register_response.json()
    assert body["email"] == email
    assert body["is_verified"] is False
    assert body["google_linked"] is False

    # Cannot log in before verifying.
    unverified_login = client.post("/auth/login", json={"email": email, "password": "S3curePassword!"})
    assert unverified_login.status_code == 403

    # Pull the real OTP out of the DB (no email server in tests).
    user = db_session.query(User).filter(User.email == email).first()
    otp_record = (
        db_session.query(OTPVerification)
        .filter(OTPVerification.user_id == user.id, OTPVerification.is_used.is_(False))
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    assert otp_record is not None

    # Wrong OTP is rejected.
    wrong_otp = client.post("/auth/verify-otp", json={"email": email, "otp": "000000"})
    assert wrong_otp.status_code == 400

    # Need the plaintext OTP to actually verify -- re-derive it isn't
    # possible (it's hashed), so patch in a known one for this test.
    from app.core.security import hash_otp

    otp_record.otp_hash = hash_otp("123456")
    db_session.commit()

    verify_response = client.post("/auth/verify-otp", json={"email": email, "otp": "123456"})
    assert verify_response.status_code == 200
    assert verify_response.json()["is_verified"] is True

    login_response = client.post("/auth/login", json={"email": email, "password": "S3curePassword!"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


def test_wrong_password_is_rejected(client):
    email = unique_email()
    client.post(
        "/auth/register",
        json={
            "name": "Another Tester",
            "email": email,
            "password": "CorrectPassword1!",
            "instrument": "Qanun",
        },
    )

    response = client.post("/auth/login", json={"email": email, "password": "WrongPassword"})
    assert response.status_code == 401


def test_me_requires_a_token(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)


def test_google_only_account_cannot_login_with_password(client, db_session):
    """A Google-created account has no password_hash -- email/password
    login against it must fail cleanly, not crash."""

    from app.services.google_auth_service import _handle_login_callback
    from app.core.google_oauth import GoogleIdentity

    identity = GoogleIdentity(
        google_id="google-no-password-test", email=unique_email(), name="Google Only", picture=None,
    )
    _handle_login_callback(db_session, identity)

    response = client.post("/auth/login", json={"email": identity.email, "password": "anything"})
    assert response.status_code == 401
