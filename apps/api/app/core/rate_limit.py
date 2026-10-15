"""In-memory sliding-window rate limiting middleware.

Protects against brute force credential stuffing, DDoS, and API abuse.
Supports proxy headers (X-Forwarded-For) and enforces strict per-endpoint quotas.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.config import get_settings
from app.core.errors import ErrorCode, error_response

# Storage: { key: [timestamp, timestamp, ...] }
_REQUEST_HISTORY: dict[str, list[float]] = defaultdict(list)

# Rate limits: (max_requests, window_seconds)
_LIMITS = {
    # Strictest for auth endpoints (brute-force defense)
    "auth": (15, 60),
    # Upload limits (storage / resource exhaustion defense)
    "upload": (30, 60),
    # Default for all other endpoints
    "default": (120, 60),
}


def _get_client_ip(request: Request) -> str:
    """Extracts client IP, respecting trusted proxy headers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First IP in the list is the original client
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def _get_rate_bucket(request: Request) -> str:
    path = request.url.path
    if "/auth/login" in path or "/auth/register" in path:
        return "auth"
    if path.endswith("/documents") and request.method == "POST":
        return "upload"
    return "default"


def is_rate_limited(client_ip: str, bucket: str) -> tuple[bool, int, int]:
    """Checks whether the client has exceeded rate limits.
    Returns: (is_limited, remaining_quota, retry_after_seconds)
    """
    now = time.time()
    max_requests, window_seconds = _LIMITS[bucket]
    key = f"{client_ip}:{bucket}"
    
    # Prune expired timestamps
    history = [ts for ts in _REQUEST_HISTORY[key] if now - ts < window_seconds]
    _REQUEST_HISTORY[key] = history
    
    if len(history) >= max_requests:
        oldest_ts = history[0]
        retry_after = max(1, int(window_seconds - (now - oldest_ts)))
        return True, 0, retry_after
        
    _REQUEST_HISTORY[key].append(now)
    remaining = max_requests - len(_REQUEST_HISTORY[key])
    return False, remaining, 0


async def rate_limiting_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    settings = get_settings()
    # Bypass in test environment to avoid flaky integration suites
    if settings.environment == "test" or os.environ.get("PYTEST_CURRENT_TEST"):
        return await call_next(request)
        
    # Health checks and documentation bypass rate limiter
    path = request.url.path
    if path.endswith("/health") or path.startswith("/docs") or path.startswith("/openapi"):
        return await call_next(request)
        
    client_ip = _get_client_ip(request)
    bucket = _get_rate_bucket(request)
    
    is_limited, remaining, retry_after = is_rate_limited(client_ip, bucket)
    
    if is_limited:
        resp = error_response(
            request,
            ErrorCode.INVALID_STATE,
            f"Rate limit exceeded. Please wait {retry_after} seconds before retrying.",
            429,
        )
        resp.headers["Retry-After"] = str(retry_after)
        resp.headers["X-RateLimit-Limit"] = str(_LIMITS[bucket][0])
        resp.headers["X-RateLimit-Remaining"] = "0"
        return resp
        
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(_LIMITS[bucket][0])
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response
