"""CARELYNX FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.security import security_middleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="CARELYNX API",
        version="0.1.0",
        description=(
            "Evidence-linked discharge instruction processing. "
            "Information navigation only — not a diagnosis or treatment system."
        ),
    )
    app.middleware("http")(security_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Carelynx-Role"],
        expose_headers=["X-Request-ID"],
    )
    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
