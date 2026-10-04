from fastapi.testclient import TestClient

from demo.fixtures import A_SUMMARY, B_PRESCRIPTION, render_pdf
from tests.integration.test_upload import PNG_1PX


def _upload(client: TestClient, name: str, data: bytes, mime: str = "application/pdf") -> dict:
    r = client.post("/api/v1/documents", files={"file": (name, data, mime)})
    assert r.status_code == 201, r.text
    return r.json()


def test_text_pdf_is_page_aware(client: TestClient) -> None:
    doc = _upload(client, "a.pdf", render_pdf(A_SUMMARY))
    r = client.post(f"/api/v1/documents/{doc['id']}/process")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "PROCESSED"

    meta = client.get(f"/api/v1/documents/{doc['id']}").json()
    assert meta["page_count"] == 2
    assert meta["document_kind"] == "discharge_summary"
    assert [p["page_number"] for p in meta["pages"]] == [1, 2]
    assert all(p["extraction_method"] == "pdf_text" for p in meta["pages"])

    p2 = client.get(f"/api/v1/documents/{doc['id']}/pages/2").json()
    assert "14 Oct 2026" in p2["text"]  # follow-up lives on page 2
    p1 = client.get(f"/api/v1/documents/{doc['id']}/pages/1").json()
    assert "14 Oct 2026" not in p1["text"]


def test_bad_ocr_text_is_flagged(client: TestClient) -> None:
    doc = _upload(client, "b.pdf", render_pdf(B_PRESCRIPTION))
    r = client.post(f"/api/v1/documents/{doc['id']}/process")
    assert r.json()["status"] == "PROCESSED_WITH_WARNINGS"
    page = client.get(f"/api/v1/documents/{doc['id']}").json()["pages"][0]
    assert "SUSPECTED_OCR_ERRORS" in page["quality_flags"]
    assert page["text_quality"] < 0.85


def test_image_without_ocr_engine_is_explicit(client: TestClient, monkeypatch) -> None:
    from app.services import ocr

    monkeypatch.setattr(ocr.TesseractOcr, "available", property(lambda self: False))
    doc = _upload(client, "scan.png", PNG_1PX, "image/png")
    r = client.post(f"/api/v1/documents/{doc['id']}/process")
    assert r.json()["status"] == "PROCESSED_WITH_WARNINGS"
    page = client.get(f"/api/v1/documents/{doc['id']}").json()["pages"][0]
    assert page["extraction_method"] == "ocr_unavailable"
    assert "OCR_UNAVAILABLE" in page["quality_flags"]


def test_corrupt_pdf_fails_explicitly(client: TestClient) -> None:
    doc = _upload(client, "broken.pdf", b"%PDF-1.4\n garbage garbage")
    r = client.post(f"/api/v1/documents/{doc['id']}/process")
    assert r.status_code == 200
    assert r.json()["status"] == "FAILED"
    meta = client.get(f"/api/v1/documents/{doc['id']}").json()
    assert meta["error_code"] == "PDF_PARSE_ERROR"


def test_unknown_document_404(client: TestClient) -> None:
    r = client.post("/api/v1/documents/00000000-0000-0000-0000-000000000000/process")
    assert r.status_code == 404
