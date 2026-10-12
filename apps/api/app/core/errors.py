"""Error contract (docs/API_CONTRACTS.md): {"error": {"code", "message", "request_id"}}. No stack traces."""

from __future__ import annotations

import logging
import uuid
from enum import StrEnum

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("carelynx")


class ErrorCode(StrEnum):
    """API_CONTRACTS.md §1.2. OCR_ERROR / PARSING_ERROR are also stored on documents as `error_code`."""

    UPLOAD_ERROR = "UPLOAD_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    AUTH_ERROR = "AUTH_ERROR"
    FORBIDDEN = "FORBIDDEN"
    INVALID_STATE = "INVALID_STATE"
    CONFLICT_ERROR = "CONFLICT_ERROR"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    OCR_ERROR = "OCR_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    EVIDENCE_ERROR = "EVIDENCE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    return rid if isinstance(rid, str) else str(uuid.uuid4())


def _body(code: str, message: str, request: Request) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message, "request_id": _request_id(request)}}


def error_response(request: Request, code: ErrorCode, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=_body(code, message, request))


_HTTP_CODE_MAP = {
    400: ErrorCode.UPLOAD_ERROR,
    401: ErrorCode.AUTH_ERROR,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.INVALID_STATE,
    413: ErrorCode.UPLOAD_ERROR,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(request, exc.code, exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = ", ".join(".".join(str(p) for p in e.get("loc", ())) for e in exc.errors()[:5])
        return JSONResponse(
            status_code=422,
            content=_body(ErrorCode.VALIDATION_ERROR, f"Invalid request: {fields}", request),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODE_MAP.get(exc.status_code, ErrorCode.VALIDATION_ERROR)
        return error_response(request, code, str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        from app.core.security import SECURITY_HEADERS  # local import: security imports this module

        logger.exception("Unhandled error request_id=%s", _request_id(request))
        # Runs outside the security middleware (ServerErrorMiddleware), so add its headers here.
        resp = error_response(request, ErrorCode.INTERNAL_ERROR, "An internal error occurred.", 500)
        resp.headers.update({**SECURITY_HEADERS, "X-Request-ID": _request_id(request)})
        return resp
