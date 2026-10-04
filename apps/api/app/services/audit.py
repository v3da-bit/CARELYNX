"""Audit logging. Metadata is restricted to identifiers/counts/codes — never document text (SAFETY.md §9)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog
from app.models.enums import ActorType, AuditEvent

_FORBIDDEN_KEYS = {"text", "snippet", "content", "source_text", "document", "value", "raw", "prompt", "output"}
_MAX_STR = 120


def _sanitize(meta: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for k, v in meta.items():
        if k.lower() in _FORBIDDEN_KEYS:
            raise ValueError(f"Audit metadata key '{k}' may contain sensitive content and is not allowed")
        if isinstance(v, uuid.UUID):
            clean[k] = str(v)
        elif isinstance(v, str):
            clean[k] = v[:_MAX_STR]
        elif isinstance(v, (int, float, bool)) or v is None:
            clean[k] = v
        elif isinstance(v, list):
            clean[k] = [str(x)[:_MAX_STR] for x in v[:50]]
        else:
            clean[k] = str(v)[:_MAX_STR]
    return clean


def record(
    db: Session,
    event: AuditEvent,
    *,
    actor_type: ActorType = ActorType.SYSTEM,
    case_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    **metadata: Any,
) -> AuditLog:
    entry = AuditLog(
        case_id=case_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event.value,
        event_metadata=_sanitize(metadata),
    )
    db.add(entry)
    return entry
