"""Incoming webhook endpoint with cryptographic signature verification."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, Request

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.webhooks import verify_webhook_signature

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/incoming")
async def handle_incoming_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_timestamp: str | None = Header(default=None, alias="X-Timestamp"),
) -> dict[str, Any]:
    """Receives and verifies signed external partner / EHR webhooks."""
    if not x_signature:
        raise AppError(ErrorCode.FORBIDDEN, "Missing webhook signature header (X-Signature).", 401)
        
    body = await request.body()
    secret = get_settings().auth_secret_key
    
    is_valid = verify_webhook_signature(
        payload=body,
        signature=x_signature,
        secret=secret,
        timestamp=x_timestamp,
    )
    
    if not is_valid:
        raise AppError(ErrorCode.FORBIDDEN, "Invalid or expired webhook signature.", 403)
        
    logger.info("Verified incoming webhook from %s", request.client.host if request.client else "unknown")
    return {"status": "accepted", "verified": True}
