"""Shared test fixtures: isolated SQLite DB + temp storage per test."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Configure env BEFORE importing app modules.
_TMP = Path(tempfile.mkdtemp(prefix="carelynx-test-"))
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'test.db'}"
os.environ["STORAGE_LOCAL_DIR"] = str(_TMP / "storage")
os.environ["INFERENCE_PROVIDER"] = "rule_based"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402

try:
    from app.db.base import Base  # noqa: E402
except ImportError:  # before models exist
    Base = None  # type: ignore[assignment,misc]


@pytest.fixture(autouse=True)
def _fresh_db() -> Iterator[None]:
    if Base is not None:
        import app.models  # noqa: F401  (register models)

        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def db() -> Iterator[Session]:
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


REVIEWER = {"X-Carelynx-Role": "reviewer"}
