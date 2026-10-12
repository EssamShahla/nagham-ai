"""
Tests for the forgot/reset password flow. Covers the enumeration-resistant
design (same response for known/unknown email), OTP correctness, and that
a Google-only account can use this flow to add a password.
"""

from app.models.otp_verification import OTPVerification
from app.models.user import User
from app.core.security import hash_otp

from tests.conftest import unique_email


def register_and_verify(client, db_session, email: str, password: str = "OriginalPass1!"):
    client.post(
        "/auth/register",
        json={"name": "Reset Tester", "email": email, "password": password, "instrument": "Oud"},
    )
    user = db_session.query(User).filter(User.email == email).first()
    user.is_verified = True
    db_session.commit()
    return user


def test_forgot_password_gives_the_same_response_for_unknown_email(client):
    response = client.post("/auth/forgot-password", json={"email": unique_email()})
    assert response.status_code == 200
    assert "If an account exists" in response.json()["message"]


def test_forgot_password_sends_an_otp_for_a_real_account(client, db_session):
    email = unique_email()
    register_and_verify(client, db_session, email)

    response = client.post("/auth/forgot-password", json={"email": email})
    assert response.status_code == 200

    user = db_session.query(User).filter(User.email == email).first()
    otp_record = (
        db_session.query(OTPVerification)
        .filter(OTPVerification.user_id == user.id, OTPVerification.purpose == "password_reset")
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    assert otp_record is not None
    assert otp_record.is_used is False


def test_reset_password_with_wrong_otp_is_rejected(client, db_session):
    email = unique_email()
    register_and_verify(client, db_session, email)
    client.post("/auth/forgot-password", json={"email": email})

    response = client.post(
        "/auth/reset-password",
        json={"email": email, "otp": "000000", "new_password": "BrandNewPass1!"},
    )
    assert response.status_code == 400


def test_reset_password_with_unknown_email_is_rejected_generically(client):
    response = client.post(
        "/auth/reset-password",
        json={"email": unique_email(), "otp": "123456", "new_password": "BrandNewPass1!"},
    )
    assert response.status_code == 400


def test_full_reset_flow_allows_login_with_new_password_and_invalidates_old(client, db_session):
    email = unique_email()
    register_and_verify(client, db_session, email, password="OriginalPass1!")

    client.post("/auth/forgot-password", json={"email": email})

    user = db_session.query(User).filter(User.email == email).first()
    otp_record = (
        db_session.query(OTPVerification)
        .filter(OTPVerification.user_id == user.id, OTPVerification.purpose == "password_reset")
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    # Known plaintext for a deterministic test (can't recover it from the hash).
    otp_record.otp_hash = hash_otp("654321")
    db_session.commit()

    reset_response = client.post(
        "/auth/reset-password",
        json={"email": email, "otp": "654321", "new_password": "BrandNewPass1!"},
    )
    assert reset_response.status_code == 200

    # Old password no longer works.
    old_login = client.post("/auth/login", json={"email": email, "password": "OriginalPass1!"})
    assert old_login.status_code == 401

    # New password works.
    new_login = client.post("/auth/login", json={"email": email, "password": "BrandNewPass1!"})
    assert new_login.status_code == 200

    # The reset code is single-use.
    reused = client.post(
        "/auth/reset-password",
        json={"email": email, "otp": "654321", "new_password": "AnotherPass2!"},
    )
    assert reused.status_code == 400


def test_google_only_account_can_set_a_password_via_reset(client, db_session):
    """A Google-created account has no password -- the reset flow should
    still let them set one (effectively adding password login)."""

    from app.core.google_oauth import GoogleIdentity
    from app.services.google_auth_service import _handle_login_callback

    identity = GoogleIdentity(
        google_id="google-reset-test", email=unique_email(), name="Google User", picture=None,
    )
    _handle_login_callback(db_session, identity)

    user = db_session.query(User).filter(User.email == identity.email).first()
    assert user.password_hash is None

    client.post("/auth/forgot-password", json={"email": identity.email})
    otp_record = (
        db_session.query(OTPVerification)
        .filter(OTPVerification.user_id == user.id, OTPVerification.purpose == "password_reset")
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    otp_record.otp_hash = hash_otp("111222")
    db_session.commit()

    response = client.post(
        "/auth/reset-password",
        json={"email": identity.email, "otp": "111222", "new_password": "NewPasswordForGoogleUser1!"},
    )
    assert response.status_code == 200

    login_response = client.post(
        "/auth/login", json={"email": identity.email, "password": "NewPasswordForGoogleUser1!"}
    )
    assert login_response.status_code == 200
