"""Authentication, password hashing, and token issuance utilities.

Built with NIST SP 800-132 PBKDF2-HMAC-SHA256 and constant-time HMAC-SHA256 tokens.
Zero external library dependencies (safe for air-gapped / offline environments).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from typing import Any

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.db.session import get_db
from app.models import User

# Password hashing params: 16-byte random salt, 120,000 PBKDF2 iterations
_PBKDF2_ITERATIONS = 120_000
_EMAIL_REGEX = re.compile(r"^[\w.!#$%&'*+/=?^_`{|}~-]+@[\w.-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> str:
    cleaned = email.strip().lower()
    if not _EMAIL_REGEX.match(cleaned) or len(cleaned) > 255:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Invalid email address format.", 422)
    return cleaned


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Password must be at least 8 characters long.", 422)
    if not any(c.isdigit() for c in password) and not any(not c.isalnum() for c in password):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Password must contain at least one digit or special character.",
            422,
        )
    return password


def hash_password(password: str) -> str:
    """Computes PBKDF2-HMAC-SHA256 hash with cryptographic random salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies password using constant-time comparison to prevent timing attacks."""
    try:
        salt_hex, dk_hex = hashed_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_dk = bytes.fromhex(dk_hex)
        actual_dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
        return hmac.compare_digest(expected_dk, actual_dk)
    except Exception:
        return False


def _get_signing_secret() -> bytes:
    settings = get_settings()
    secret = getattr(settings, "auth_secret_key", "") or "carelynx-fallback-token-secret-key-32b"
    return secret.encode("utf-8")


def create_token(
    user_id: uuid.UUID,
    email: str,
    role: str,
    expires_in_seconds: int = 86400 * 7,
) -> str:
    """Creates a URL-safe signed authentication token (HMAC-SHA256)."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("ascii").rstrip("=")
    
    secret = _get_signing_secret()
    signature = hmac.new(secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{payload_b64}.{sig_b64}"


def verify_token(token: str) -> dict[str, Any] | None:
    """Verifies token signature, expiration, and returns decoded payload."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        
        # Verify signature
        secret = _get_signing_secret()
        expected_sig = hmac.new(secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
        
        # Pad base64 for decoding
        rem = len(sig_b64) % 4
        padded_sig = sig_b64 + ("=" * (4 - rem) if rem else "")
        provided_sig = base64.urlsafe_b64decode(padded_sig.encode("ascii"))
        
        if not hmac.compare_digest(expected_sig, provided_sig):
            return None
            
        rem_p = len(payload_b64) % 4
        padded_p = payload_b64 + ("=" * (4 - rem_p) if rem_p else "")
        payload_raw = base64.urlsafe_b64decode(padded_p.encode("ascii"))
        payload = json.loads(payload_raw.decode("utf-8"))
        
        # Verify expiration
        if payload.get("exp", 0) < int(time.time()):
            return None
            
        return payload
    except Exception:
        return None


def get_token_from_header(authorization: str | None = Header(default=None)) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def get_optional_user(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """Resolves authenticated user from Bearer header if present."""
    token = get_token_from_header(authorization)
    if not token:
        # Check Authorization cookie if present
        token = request.cookies.get("carelynx_auth_token")
    if not token:
        return None
    data = verify_token(token)
    if not data or not data.get("sub"):
        return None
    try:
        user_uuid = uuid.UUID(data["sub"])
    except ValueError:
        return None
    user = db.get(User, user_uuid)
    if user and not user.is_active:
        return None
    return user


def require_authenticated_user(
    user: User | None = Depends(get_optional_user),
) -> User:
    """Enforces authentication: raises 401 if user is unauthenticated."""
    if user is None:
        raise AppError(ErrorCode.FORBIDDEN, "Authentication required. Please sign in.", 401)
    return user
