"""Declarative base + portable column types (PostgreSQL target, SQLite fallback)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, MetaData, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# JSONB on Postgres, JSON elsewhere.
JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(UTC)


def enum_col(enum_cls: type[StrEnum]) -> Enum:
    """Store enum *values* as VARCHAR(32) (DATABASE.md), no native DB enum."""
    return Enum(
        enum_cls,
        native_enum=False,
        length=32 if max(len(m.value) for m in enum_cls) <= 32 else 100,
        values_callable=lambda e: [m.value for m in e],
        create_constraint=False,
        validate_strings=True,
    )


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)
    type_annotation_map: dict[Any, Any] = {
        uuid.UUID: Uuid(),
        datetime: DateTime(timezone=True),
        dict[str, Any]: JSONType,
        list[Any]: JSONType,
    }


class UUIDPk:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow, nullable=False)
