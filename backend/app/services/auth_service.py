from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.services.email_service import send_password_reset_email, send_verification_email

from app.models.user import User
from app.models.otp_verification import OTPVerification
from app.schemas.user import UserRegister
from app.core.security import (
    hash_password,
    generate_otp,
    hash_otp,
    verify_otp,
    verify_password
)


def register_user(db: Session, user_data: UserRegister):

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        return None

    try:
        hashed_password = hash_password(user_data.password)

        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            instrument=user_data.instrument,
            phone=user_data.phone,
            country=user_data.country,
            city=user_data.city,
            music_role=user_data.music_role,
            years_of_experience=user_data.years_of_experience,
            bio=user_data.bio,
            auth_provider="local",
            is_verified=False,
            profile_completed=True
        )

        db.add(new_user)

        # Send INSERT to PostgreSQL and get the new user's ID
        # without permanently committing the transaction yet
        db.flush()

        otp = generate_otp()

        otp_record = OTPVerification(
            user_id=new_user.id,
            otp_hash=hash_otp(otp),
            purpose="email_verification",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            is_used=False
        )

        db.add(otp_record)

        send_verification_email(
            to_email=new_user.email,
            otp=otp
        )

        db.commit()
        db.refresh(new_user)

        return new_user

    except Exception:
        db.rollback()
        raise



def verify_user_otp(db: Session, email: str, otp: str):

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        return "user_not_found"

    otp_record = db.query(OTPVerification).filter(
        OTPVerification.user_id == user.id,
        OTPVerification.purpose == "email_verification",
        OTPVerification.is_used == False
    ).order_by(
        OTPVerification.created_at.desc()
    ).first()

    if not otp_record:
        return "otp_not_found"

    if datetime.now(timezone.utc) > otp_record.expires_at:
        return "otp_expired"

    if not verify_otp(otp, otp_record.otp_hash):
        return "invalid_otp"

    otp_record.is_used = True
    user.is_verified = True

    db.commit()
    db.refresh(user)

    return user



def login_user(db: Session, email: str, password: str):

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        return "invalid_credentials"

    if not user.password_hash:
        return "invalid_credentials"

    if not verify_password(
        password,
        user.password_hash
    ):
        return "invalid_credentials"

    if not user.is_verified:
        return "not_verified"

    return user


def resend_verification_otp(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return "user_not_found"

    if user.is_verified:
        return "already_verified"

    latest_otp = db.query(OTPVerification).filter(
        OTPVerification.user_id == user.id,
        OTPVerification.purpose == "email_verification"
    ).order_by(OTPVerification.created_at.desc()).first()

    if latest_otp:
        now = datetime.now(timezone.utc)

        # Cooldown: one resend every 60 seconds
        if latest_otp.created_at:
            time_since_last_otp = now - latest_otp.created_at

            if time_since_last_otp.total_seconds() < 60:
                remaining_seconds = 60 - int(time_since_last_otp.total_seconds())

                return {
                    "status": "cooldown",
                    "remaining_seconds": remaining_seconds
                }

    try:
        # Invalidate all previous unused OTPs
        db.query(OTPVerification).filter(
            OTPVerification.user_id == user.id,
            OTPVerification.purpose == "email_verification",
            OTPVerification.is_used == False
        ).update(
            {"is_used": True},
            synchronize_session=False
        )

        otp = generate_otp()

        otp_record = OTPVerification(
            user_id=user.id,
            otp_hash=hash_otp(otp),
            purpose="email_verification",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            is_used=False
        )

        db.add(otp_record)

        send_verification_email(
            to_email=user.email,
            otp=otp
        )

        db.commit()

        return "otp_resent"

    except Exception:
        db.rollback()
        raise


PASSWORD_RESET_PURPOSE = "password_reset"
PASSWORD_RESET_TTL_MINUTES = 15
PASSWORD_RESET_COOLDOWN_SECONDS = 60


def request_password_reset(db: Session, email: str) -> None:
    """
    Enumeration-resistant by design: this always "succeeds" from the
    caller's point of view. An email is only actually sent if the account
    exists, but that distinction is never revealed to the caller --
    unlike /auth/resend-otp (which does reveal it), password reset is a
    more commonly abused target for account enumeration, so it gets the
    stricter treatment here.
    """

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return

    latest = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.user_id == user.id,
            OTPVerification.purpose == PASSWORD_RESET_PURPOSE,
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if latest and latest.created_at:
        elapsed = datetime.now(timezone.utc) - latest.created_at
        if elapsed.total_seconds() < PASSWORD_RESET_COOLDOWN_SECONDS:
            return

    try:
        db.query(OTPVerification).filter(
            OTPVerification.user_id == user.id,
            OTPVerification.purpose == PASSWORD_RESET_PURPOSE,
            OTPVerification.is_used == False,
        ).update({"is_used": True}, synchronize_session=False)

        otp = generate_otp()

        db.add(OTPVerification(
            user_id=user.id,
            otp_hash=hash_otp(otp),
            purpose=PASSWORD_RESET_PURPOSE,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES),
            is_used=False,
        ))

        send_password_reset_email(to_email=user.email, otp=otp)

        db.commit()

    except Exception:
        db.rollback()
        raise


def reset_password(db: Session, email: str, otp: str, new_password: str):
    """
    Collapses every failure mode (unknown email, no active code, expired,
    wrong code) into the same "invalid_or_expired" result -- deliberately
    not distinguishing them, so this endpoint can't be used to enumerate
    which emails have accounts either.
    """

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return "invalid_or_expired"

    otp_record = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.user_id == user.id,
            OTPVerification.purpose == PASSWORD_RESET_PURPOSE,
            OTPVerification.is_used == False,
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if not otp_record:
        return "invalid_or_expired"

    if datetime.now(timezone.utc) > otp_record.expires_at:
        return "invalid_or_expired"

    if not verify_otp(otp, otp_record.otp_hash):
        return "invalid_or_expired"

    otp_record.is_used = True
    user.password_hash = hash_password(new_password)

    db.commit()
    db.refresh(user)

    return user