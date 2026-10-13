"""Processing state rules (API_CONTRACTS §4): 409 re-process, FAILED never stuck, FAILED re-process purges."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Fact, ReviewCase
from app.services.ocr import OcrResult
from demo.fixtures import A_SUMMARY, render_pdf
from tests.conftest import REVIEWER
from tests.integration.test_upload import PNG_1PX


def _upload(client: TestClient, name: str, data: bytes, mime: str = "application/pdf") -> dict[str, Any]:
    r = client.post("/api/v1/documents", files={"file": (name, data, mime)})
    assert r.status_code == 201, r.text
    return r.json()


def test_reprocess_is_409(client: TestClient) -> None:
    doc = _upload(client, "a.pdf", render_pdf(A_SUMMARY))
    assert client.post(f"/api/v1/documents/{doc['id']}/process").status_code == 200
    r = client.post(f"/api/v1/documents/{doc['id']}/process")
    assert r.status_code == 409 and r.json()["error"]["code"] == "INVALID_STATE"


def test_ocr_crash_marks_failed_with_review(client: TestClient, db: Session, monkeypatch) -> None:
    class CrashingOcr:
        name = "crashing"
        available = True

        def recognize(self, image_bytes: bytes) -> OcrResult:
            raise RuntimeError("tesseract segfault")

    monkeypatch.setattr("app.api.v1.documents.get_ocr_engine", lambda: CrashingOcr())
    doc = _upload(client, "scan.png", PNG_1PX, "image/png")
    r = client.post(f"/api/v1/documents/{doc['id']}/process")
    assert r.status_code == 200
    assert r.json() == {"document_id": doc["id"], "status": "FAILED", "error_code": "OCR_ERROR"}
    reviews = client.get("/api/v1/reviews", headers=REVIEWER).json()
    assert [(x["reason_code"], x["document_id"]) for x in reviews] == [("PROCESSING_FAILED", doc["id"])]


def test_provider_failure_is_502_then_failed_reprocess_has_no_duplicates(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services import extraction

    real = extraction.get_inference_provider

    class Down:
        info = real().info

        async def generate_structured(self, request: Any) -> dict[str, Any]:
            raise TimeoutError("vLLM unreachable")

    monkeypatch.setattr(extraction, "get_inference_provider", lambda: Down())
    doc = _upload(client, "a.pdf", render_pdf(A_SUMMARY))
    r = client.post(f"/api/v1/documents/{doc['id']}/process")
    assert r.status_code == 502 and r.json()["error"]["code"] == "MODEL_ERROR"
    meta = client.get(f"/api/v1/documents/{doc['id']}").json()
    assert meta["processing_status"] == "FAILED" and meta["error_code"] == "MODEL_ERROR"
    assert db.query(Fact).count() == 0
    assert db.query(ReviewCase).filter(ReviewCase.reason_code == "PROCESSING_FAILED").count() == 1

    monkeypatch.setattr(extraction, "get_inference_provider", real)
    r = client.post(f"/api/v1/documents/{doc['id']}/process")
    assert r.status_code == 200 and r.json()["status"] == "PROCESSED", r.text
    first = db.query(Fact).count()
    assert first > 0

    # A FAILED document that already has facts is purged before re-processing.
    from app.models import Document
    from app.models.enums import ProcessingStatus

    db.expire_all()
    d = db.get_one(Document, uuid.UUID(doc["id"]))
    d.processing_status = ProcessingStatus.FAILED
    db.commit()
    assert client.post(f"/api/v1/documents/{doc['id']}/process").status_code == 200
    db.expire_all()
    assert db.query(Fact).count() == first
    page = client.get(f"/api/v1/documents/{doc['id']}/pages/1").json()
    assert page["id"] and page["document_id"] == doc["id"]
