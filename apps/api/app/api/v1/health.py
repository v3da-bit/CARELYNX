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
    database: Literal["ok", "unavailable"]
    database_backend: str
    inference_provider: str
    inference_hardware_label: str


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        db_status: Literal["ok", "unavailable"] = "ok"
    except Exception:  # noqa: BLE001 — health must never raise
        db_status = "unavailable"
    backend = db.get_bind().dialect.name
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        database_backend=backend,
        inference_provider=settings.inference_provider,
        inference_hardware_label=settings.inference_hardware_label,
    )
