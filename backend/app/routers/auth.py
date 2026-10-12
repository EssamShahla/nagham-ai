import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.google_oauth import GoogleOAuthNotConfigured
from app.core.security import create_access_token, get_current_user
from app.models.user import User
from app.database.connection import get_db

from app.schemas.google_auth import GoogleExchangeRequest, GoogleLinkRequest
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserUpdate,
    OTPVerify,
    UserResponse,
    ResendOTPRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

from app.services.auth_service import (
    register_user,
    verify_user_otp,
    login_user,
    resend_verification_otp,
    request_password_reset,
    reset_password,
)
from app.services.google_auth_service import (
    GoogleCallbackError,
    LinkRequired,
    Linked,
    LoggedIn,
    confirm_pending_link,
    consume_exchange_code,
    handle_callback,
    start_link,
    start_login,
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
# UPDATE CURRENT USER
# PATCH /auth/me
# Protected endpoint that lets the authenticated user update
# their own profile fields.
# ============================================================
@router.patch(
    "/me",
    response_model=UserResponse
)
def update_me(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updates = user_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

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


# ============================================================
# FORGOT / RESET PASSWORD
#
# POST /auth/forgot-password always returns the same generic message,
# whether or not the email belongs to an account -- this endpoint is a
# common account-enumeration target, so unlike /auth/resend-otp above it
# never reveals that distinction.
# ============================================================
@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    request_password_reset(db, request.email)

    return {
        "message": "If an account exists with that email, a password reset code has been sent."
    }


@router.post("/reset-password")
def reset_password_endpoint(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    result = reset_password(
        db,
        email=request.email,
        otp=request.otp,
        new_password=request.new_password,
    )

    if result == "invalid_or_expired":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset code is invalid or has expired. Please request a new one.",
        )

    return {
        "message": "Your password has been reset. You can now sign in with your new password."
    }


# ============================================================
# GOOGLE SIGN-IN
#
# Authorization Code flow + PKCE, handled server-side:
#   1. GET  /auth/google/login       -> redirect to Google
#   2. GET  /auth/google/callback    -> Google redirects back here
#   3. POST /auth/google/exchange    -> frontend trades the one-time
#                                        exchange code for a real JWT
#   4. POST /auth/google/link        -> confirm a proposed account link
#
# The real JWT is NEVER placed in a URL. Step 2 instead redirects the
# browser to the frontend with a short-lived, single-use, narrowly-scoped
# opaque code that only a POST request can turn into an access token.
# ============================================================

def _frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


def _redirect_to_frontend_error(message: str) -> RedirectResponse:
    return RedirectResponse(
        f"{_frontend_url()}/login?google_error={quote(message)}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/google/login")
def google_login(db: Session = Depends(get_db)):
    try:
        authorize_url = start_login(db)
    except GoogleOAuthNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return RedirectResponse(authorize_url, status_code=status.HTTP_302_FOUND)


@router.get("/google/link/start")
def google_link_start(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Explicit, already-authenticated linking -- e.g. a "Connect Google"
    action in account settings. Distinct from the implicit-collision path
    in the callback, which instead requires a password re-login to confirm.

    Returns the authorize URL as JSON rather than redirecting directly:
    this endpoint requires an Authorization header (our JWT lives in
    localStorage, not a cookie), which only an authenticated `fetch` can
    send -- a plain browser navigation can't. The frontend fetches this,
    then performs the actual top-level redirect to the URL in the
    response.
    """

    try:
        authorize_url = start_link(db, current_user)
    except GoogleOAuthNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return {"authorize_url": authorize_url}


@router.get("/google/callback")
def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    # The user cancelled consent, or Google reported some other error --
    # handle gracefully instead of crashing on a missing `code`.
    if error:
        return _redirect_to_frontend_error(f"Google sign-in was cancelled ({error}).")

    if not code or not state:
        return _redirect_to_frontend_error("Google sign-in response was incomplete.")

    try:
        result = handle_callback(db, code=code, state=state)
    except GoogleCallbackError as exc:
        return _redirect_to_frontend_error(str(exc))
    except GoogleOAuthNotConfigured as exc:
        return _redirect_to_frontend_error(str(exc))

    if isinstance(result, LoggedIn):
        return RedirectResponse(
            f"{_frontend_url()}/auth/google/callback?code={quote(result.exchange_code)}",
            status_code=status.HTTP_302_FOUND,
        )

    if isinstance(result, LinkRequired):
        return RedirectResponse(
            f"{_frontend_url()}/login?google_link_token={quote(result.link_token)}",
            status_code=status.HTTP_302_FOUND,
        )

    if isinstance(result, Linked):
        return RedirectResponse(
            f"{_frontend_url()}/profile?google_linked=1",
            status_code=status.HTTP_302_FOUND,
        )

    return _redirect_to_frontend_error("Unexpected Google sign-in result.")


@router.post("/google/exchange")
def google_exchange(
    body: GoogleExchangeRequest,
    db: Session = Depends(get_db),
):
    user = consume_exchange_code(db, body.code)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This sign-in code is invalid or has expired. Please try again.",
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/google/link", response_model=UserResponse)
def google_link(
    body: GoogleLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Second half of the explicit account-linking flow: called after the
    user has proven ownership of the existing local account (by logging
    in with their password) to confirm linking the Google identity we
    proposed earlier.
    """

    try:
        return confirm_pending_link(db, current_user, body.link_token)
    except GoogleCallbackError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )