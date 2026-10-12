"""OCR-read and OCR-unavailable pages never yield VERIFIED facts; unreadable scans reach a reviewer."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.ocr import OcrResult, UnavailableOcr, get_ocr_engine
from demo.fixtures import A_SUMMARY
from tests.integration.test_upload import PNG_1PX

REVIEWER = {"X-Carelynx-Role": "reviewer"}


def _process_png(client: TestClient, monkeypatch, engine) -> dict:
    monkeypatch.setattr("app.api.v1.documents.get_ocr_engine", lambda: engine)
    r = client.post("/api/v1/documents", files={"file": ("scan.png", PNG_1PX, "image/png")})
    assert r.status_code == 201, r.text
    doc = r.json()
    assert client.post(f"/api/v1/documents/{doc['id']}/process").status_code == 200
    return doc


@pytest.mark.parametrize("confidence", [0.99, 0.40])
def test_ocr_text_is_never_verified(client: TestClient, monkeypatch, confidence: float) -> None:
    class FakeTesseract:
        name, available = "fake", True

        def recognize(self, image_bytes: bytes) -> OcrResult:
            return OcrResult("\n".join(A_SUMMARY.pages[0] + A_SUMMARY.pages[1]), confidence)

    doc = _process_png(client, monkeypatch, FakeTesseract())
    facts = client.get(f"/api/v1/cases/{doc['case_id']}/facts").json()
    assert facts, "OCR text should still be extracted"
    assert all(f["status"] != "VERIFIED" for f in facts)
    reviews = client.get("/api/v1/reviews", headers=REVIEWER).json()
    assert len(reviews) >= len(facts)


def test_unavailable_ocr_opens_review_and_no_facts(client: TestClient, monkeypatch) -> None:
    doc = _process_png(client, monkeypatch, UnavailableOcr())
    assert client.get(f"/api/v1/cases/{doc['case_id']}/facts").json() == []
    reviews = client.get("/api/v1/reviews", headers=REVIEWER).json()
    assert [r["reason_code"] for r in reviews] == ["OCR_UNAVAILABLE"]


def test_get_ocr_engine_never_crashes_without_binary(monkeypatch) -> None:
    monkeypatch.setattr("app.services.ocr._find_tesseract_binary", lambda: None)
    assert get_ocr_engine().available is False
