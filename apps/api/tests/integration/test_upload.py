from fastapi.testclient import TestClient

from demo.fixtures import A_SUMMARY, render_pdf

PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_upload_pdf_creates_case_and_metadata(client: TestClient) -> None:
    r = client.post("/api/v1/documents", files={"file": ("summary.pdf", render_pdf(A_SUMMARY), "application/pdf")})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "UPLOADED"
    doc = client.get(f"/api/v1/documents/{body['id']}").json()
    assert doc["mime_type"] == "application/pdf"
    assert doc["size_bytes"] > 0
    case = client.get(f"/api/v1/cases/{body['case_id']}").json()
    assert len(case["documents"]) == 1


def test_upload_to_existing_case(client: TestClient) -> None:
    case_id = client.post("/api/v1/cases").json()["id"]
    r = client.post(
        "/api/v1/documents",
        data={"case_id": case_id},
        files={"file": ("scan.png", PNG_1PX, "image/png")},
    )
    assert r.status_code == 201
    assert r.json()["case_id"] == case_id


def test_rejects_spoofed_type(client: TestClient) -> None:
    r = client.post(
        "/api/v1/documents", files={"file": ("evil.pdf", b"MZ\x90\x00 not a pdf", "application/pdf")}
    )
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_rejects_empty_and_oversize(client: TestClient, monkeypatch) -> None:
    r = client.post("/api/v1/documents", files={"file": ("e.pdf", b"", "application/pdf")})
    assert r.status_code == 400
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    big = b"%PDF-" + b"0" * (1024 * 1024 + 10)
    r = client.post("/api/v1/documents", files={"file": ("big.pdf", big, "application/pdf")})
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_filename_is_sanitized(client: TestClient) -> None:
    r = client.post(
        "/api/v1/documents", files={"file": ("../../etc/<pass>wd.pdf", render_pdf(A_SUMMARY), "application/pdf")}
    )
    assert r.json()["filename"] == "_pass_wd.pdf"


def test_original_file_is_served_privately_and_audited(client: TestClient, db) -> None:
    from app.models import AuditLog

    doc_id = client.post(
        "/api/v1/documents", files={"file": ("s.pdf", render_pdf(A_SUMMARY), "application/pdf")}
    ).json()["id"]
    r = client.get(f"/api/v1/documents/{doc_id}/file")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF-")
    assert "no-store" in r.headers["Cache-Control"]
    events = [a.event_type for a in db.query(AuditLog).all()]
    assert "DOCUMENT_ACCESSED" in events
    # upload audit must not contain content
    for a in db.query(AuditLog).all():
        assert "text" not in a.event_metadata


def test_storage_rejects_traversal_keys() -> None:
    import pytest

    from app.storage.local import get_storage

    with pytest.raises(ValueError):
        get_storage().get("../../secret.pdf")
