"""Health endpoint. Reports DB connectivity and the truthful inference configuration."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    version: str
    database: Literal["connected", "unavailable"]
    storage: str
    inference_provider: str


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        db_status: Literal["connected", "unavailable"] = "connected"
    except Exception:  # noqa: BLE001 — health must never raise
        db_status = "unavailable"
    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        app="carelynx-api",
        version="0.1.0",
        database=db_status,
        storage="local_private",
        inference_provider=settings.inference_provider,
    )
