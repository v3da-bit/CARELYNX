"""Security middleware and demo access control.

MVP access control (decision D11): a role header `X-Carelynx-Role: patient|reviewer`.
This is a demo boundary only — production must replace it with real authentication.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from enum import StrEnum

from fastapi import Header, Request, Response

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode, error_response

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
}

# Allowance for multipart boundaries/headers on top of the file-size limit.
MULTIPART_OVERHEAD_BYTES = 64 * 1024


def _declared_body_too_large(request: Request) -> bool:
    """Reject before Starlette spools the body. Chunked bodies (no Content-Length) fall through to the
    bounded read in the upload endpoint."""
    try:
        length = int(request.headers.get("content-length", "0"))
    except ValueError:
        return False
    return length > get_settings().max_upload_bytes + MULTIPART_OVERHEAD_BYTES


async def security_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.request_id = str(uuid.uuid4())
    if _declared_body_too_large(request):
        limit_mb = get_settings().max_upload_mb
        response: Response = error_response(
            request, ErrorCode.UPLOAD_ERROR, f"File exceeds maximum upload size of {limit_mb}MB.", 400
        )
    else:
        response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


class Role(StrEnum):
    PATIENT = "patient"
    REVIEWER = "reviewer"


def current_role(x_carelynx_role: str | None = Header(default=None)) -> Role:
    if x_carelynx_role is None:
        return Role.PATIENT
    try:
        return Role(x_carelynx_role.lower())
    except ValueError as exc:
        raise AppError(ErrorCode.FORBIDDEN, "Unknown role.", 403) from exc


def require_reviewer(x_carelynx_role: str | None = Header(default=None)) -> Role:
    role = current_role(x_carelynx_role)
    if role is not Role.REVIEWER:
        raise AppError(ErrorCode.FORBIDDEN, "Reviewer role required.", 403)
    return role
