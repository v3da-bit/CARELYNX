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
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_STATE = "INVALID_STATE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
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


_HTTP_CODE_MAP = {404: ErrorCode.NOT_FOUND, 403: ErrorCode.FORBIDDEN, 401: ErrorCode.FORBIDDEN}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, request))

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
        return JSONResponse(status_code=exc.status_code, content=_body(code, str(exc.detail), request))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error request_id=%s", _request_id(request))
        return JSONResponse(
            status_code=500,
            content=_body(ErrorCode.INTERNAL_ERROR, "An internal error occurred.", request),
        )
