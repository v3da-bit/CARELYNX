"""Webhook signature verification and replay attack defense.

Uses constant-time HMAC-SHA256 comparison and unix timestamp verification
to protect against tampering and replay attacks.
"""

from __future__ import annotations

import hashlib
import hmac
import time


def verify_webhook_signature(
    *,
    payload: bytes,
    signature: str,
    secret: str,
    timestamp: str | int | None = None,
    max_age_seconds: int = 300,
) -> bool:
    """Verifies that the incoming webhook payload is signed with the expected secret.
    
    If timestamp is provided, prevents replay attacks by ensuring timestamp is within
    max_age_seconds of the current server time.
    """
    if not signature or not secret:
        return False
        
    now = int(time.time())
    
    # Check timestamp replay if provided
    if timestamp is not None:
        try:
            ts = int(timestamp)
            if abs(now - ts) > max_age_seconds:
                return False
            # If timestamp is part of payload signature (Stripe/GitHub style)
            sign_content = f"{ts}.".encode("utf-8") + payload
        except ValueError:
            return False
    else:
        sign_content = payload

    expected_sig = hmac.new(secret.encode("utf-8"), sign_content, hashlib.sha256).hexdigest()
    
    # Support both "sha256=hash" and raw "hash" formats
    clean_sig = signature.lower()
    if clean_sig.startswith("sha256="):
        clean_sig = clean_sig.split("sha256=", 1)[1].strip()
        
    return hmac.compare_digest(expected_sig, clean_sig)
