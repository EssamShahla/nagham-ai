from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user
from app.models.user import User
from app.database.connection import get_db

from app.schemas.user import (
    UserRegister,
    UserLogin,
    OTPVerify,
    UserResponse,
    ResendOTPRequest
)

from app.services.auth_service import (
    register_user,
    verify_user_otp,
    login_user,
    resend_verification_otp
)


# All endpoints in this router will start with /auth
router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# ============================================================
# REGISTER
# POST /auth/register
# Creates a new local user account.
# The service also generates an OTP and sends it to the user's
# email address for account verification.
# ============================================================
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    new_user = register_user(db, user_data)

    # Prevent registration if the email is already in use
    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return new_user


# ============================================================
# VERIFY EMAIL OTP
# POST /auth/verify-otp
# Verifies the OTP sent to the user's email.
# If the OTP is valid and has not expired, the user's account
# becomes verified.
# ============================================================
@router.post(
    "/verify-otp",
    response_model=UserResponse
)
def verify_otp_endpoint(
    otp_data: OTPVerify,
    db: Session = Depends(get_db)
):
    result = verify_user_otp(
        db,
        otp_data.email,
        otp_data.otp
    )

    # No account exists with the provided email
    if result == "user_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # No active OTP exists, or it has already been used
    if result == "otp_not_found":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found or already used"
        )

    # OTP exists but its expiration time has passed
    if result == "otp_expired":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )

    # The submitted OTP does not match the stored OTP
    if result == "invalid_otp":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    return result


# ============================================================
# LOGIN
# POST /auth/login
# Authenticates a verified local user using email and password.
# If authentication succeeds, a JWT access token is returned.
# ============================================================
@router.post("/login")
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    result = login_user(
        db,
        login_data.email,
        login_data.password
    )

    # Email or password is incorrect
    if result == "invalid_credentials":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # User exists but has not completed email verification
    if result == "not_verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email is not verified"
        )

    # Generate a JWT access token for the authenticated user
    access_token = create_access_token(result.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============================================================
# GET CURRENT USER
# GET /auth/me
# Protected endpoint that returns the currently authenticated
# user's profile based on the JWT access token.
# ============================================================
@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


# ============================================================
# RESEND EMAIL OTP
# POST /auth/resend-otp
# Generates and sends a new verification OTP to an unverified
# user. A cooldown prevents users from requesting OTP codes
# repeatedly within a short period of time.
# ============================================================
@router.post("/resend-otp")
def resend_otp(
    request: ResendOTPRequest,
    db: Session = Depends(get_db)
):
    result = resend_verification_otp(
        db,
        request.email
    )

    # No account exists with the provided email
    if result == "user_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # No verification code is needed for an already verified account
    if result == "already_verified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    # Prevent repeated OTP requests during the cooldown period
    if isinstance(result, dict) and result.get("status") == "cooldown":
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Please wait {result['remaining_seconds']} seconds "
                "before requesting another OTP"
            )
        )

    return {
        "message": "A new verification code has been sent to your email"
    }