"""Authentication routes: registration, login, and current user profile."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import (
    create_token,
    hash_password,
    require_authenticated_user,
    validate_email,
    validate_password_strength,
    verify_password,
)
from app.core.captcha import generate_captcha_challenge, verify_captcha_solution
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.sanitizer import sanitize_html_free
from app.db.session import get_db
from app.models import User
from app.schemas.auth import AuthResponse, CaptchaChallengeOut, LoginRequest, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/captcha", response_model=CaptchaChallengeOut)
def get_captcha() -> CaptchaChallengeOut:
    """Generates a cryptographic arithmetic challenge for bot defense."""
    challenge = generate_captcha_challenge()
    return CaptchaChallengeOut(**challenge)


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    settings = get_settings()
    # If captcha is provided or if required in production
    if body.captcha_token or settings.environment == "production":
        if not body.captcha_token or not body.captcha_answer or not verify_captcha_solution(body.captcha_token, body.captcha_answer):
            raise AppError(ErrorCode.VALIDATION_ERROR, "Invalid or expired security CAPTCHA answer.", 400)

    clean_email = validate_email(body.email)
    validate_password_strength(body.password)

    existing = db.scalar(select(User).where(User.email == clean_email))
    if existing is not None:
        raise AppError(ErrorCode.VALIDATION_ERROR, "An account with this email already exists.", 409)

    hashed = hash_password(body.password)
    user = User(
        email=clean_email,
        hashed_password=hashed,
        full_name=sanitize_html_free(body.full_name) if body.full_name else None,
        role="patient",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.email, user.role)
    response.set_cookie(
        key="carelynx_auth_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=86400 * 7,
    )
    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    settings = get_settings()
    if body.captcha_token:
        if not body.captcha_answer or not verify_captcha_solution(body.captcha_token, body.captcha_answer):
            raise AppError(ErrorCode.VALIDATION_ERROR, "Invalid or expired security CAPTCHA answer.", 400)

    clean_email = body.email.strip().lower()
    user = db.scalar(select(User).where(User.email == clean_email))
    
    if user is None or not verify_password(body.password, user.hashed_password):
        raise AppError(ErrorCode.FORBIDDEN, "Invalid email or password.", 401)

    if not user.is_active:
        raise AppError(ErrorCode.FORBIDDEN, "Account is disabled.", 403)

    token = create_token(user.id, user.email, user.role)
    response.set_cookie(
        key="carelynx_auth_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=86400 * 7,
    )
    return AuthResponse(token=token, user=UserOut.model_validate(user))



@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(require_authenticated_user)) -> UserOut:
    return UserOut.model_validate(user)
