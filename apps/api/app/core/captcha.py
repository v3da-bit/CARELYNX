"""Cryptographic CAPTCHA & bot defense utilities.

Zero external dependencies: generates HMAC-signed arithmetic challenges
with expiration and timing-attack protection. Works offline and in air-gapped environments.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import random
import time
import uuid
from typing import Any

from app.core.config import get_settings


def _get_signing_key() -> bytes:
    settings = get_settings()
    key = getattr(settings, "auth_secret_key", "") or "carelynx-captcha-signing-key"
    return key.encode("utf-8")


def generate_captcha_challenge() -> dict[str, Any]:
    """Generates a secure HMAC-signed arithmetic challenge."""
    a = random.randint(3, 19)
    b = random.randint(2, 15)
    operation = random.choice(["+", "-"])
    
    if operation == "+":
        question = f"What is {a} + {b}?"
        answer = a + b
    else:
        # Keep positive
        if a < b:
            a, b = b, a
        question = f"What is {a} - {b}?"
        answer = a - b

    challenge_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    # Sign challenge_id:answer:timestamp
    msg = f"{challenge_id}:{answer}:{timestamp}".encode("utf-8")
    sig = hmac.new(_get_signing_key(), msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii")

    return {
        "challenge_id": challenge_id,
        "question": question,
        "timestamp": timestamp,
        "token": f"{challenge_id}.{timestamp}.{sig_b64}",
    }


def verify_captcha_solution(token: str, user_answer: str | int, max_age_seconds: int = 300) -> bool:
    """Verifies that the user answer satisfies the signed challenge token within the valid time window."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return False
            
        challenge_id, ts_str, sig_b64 = parts
        timestamp = int(ts_str)
        now = int(time.time())
        
        # Check expiry
        if now - timestamp > max_age_seconds or timestamp > now + 30:
            return False
            
        clean_answer = str(user_answer).strip()
        msg = f"{challenge_id}:{clean_answer}:{timestamp}".encode("utf-8")
        expected_sig = hmac.new(_get_signing_key(), msg, hashlib.sha256).digest()
        
        rem = len(sig_b64) % 4
        padded = sig_b64 + ("=" * (4 - rem) if rem else "")
        provided_sig = base64.urlsafe_b64decode(padded.encode("ascii"))
        
        return hmac.compare_digest(expected_sig, provided_sig)
    except Exception:
        return False
