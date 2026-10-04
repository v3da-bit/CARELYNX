"""Security middleware and demo access control.

MVP access control (decision D11): a role header `X-Carelynx-Role: patient|reviewer`.
This is a demo boundary only — production must replace it with real authentication.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from enum import StrEnum

from fastapi import Header, Request, Response

from app.core.errors import AppError, ErrorCode

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


async def security_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.request_id = str(uuid.uuid4())
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
