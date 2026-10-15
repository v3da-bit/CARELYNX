"""Unit and integration tests for security hardening modules.

Covers:
- Input sanitization (XSS, SQLi)
- Rate limiting
- Cryptographic CAPTCHA challenge & verification
- Webhook HMAC-SHA256 signature verification
- Hardened file upload type validation
- IDOR prevention on user-owned clinical cases
"""

from __future__ import annotations

import time
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.captcha import generate_captcha_challenge, verify_captcha_solution
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.rate_limit import is_rate_limited
from app.core.sanitizer import (
    contains_sql_injection,
    sanitize_html_free,
    sanitize_plain_text,
)
from app.core.webhooks import verify_webhook_signature
from app.main import create_app
from app.models import Case, Patient, User
from app.services import documents as doc_service
from app.services.upload_validation import check_size, sanitize_filename, sniff_file_kind


def test_sanitize_plain_text_strips_scripts_and_escapes() -> None:
    raw = "<script>alert('xss')</script>Hello <b>World</b>"
    cleaned = sanitize_plain_text(raw)
    assert "<script>" not in cleaned
    assert "alert('xss')" not in cleaned
    assert "&lt;b&gt;World&lt;/b&gt;" in cleaned


def test_sanitize_html_free_removes_all_tags() -> None:
    raw = "<p>Patient instruction with <a href='javascript:evil()'>link</a></p>"
    cleaned = sanitize_html_free(raw)
    assert "<p>" not in cleaned
    assert "href=" not in cleaned
    assert "javascript:" not in cleaned


def test_contains_sql_injection_detection() -> None:
    assert contains_sql_injection("1' OR '1'='1") is True
    assert contains_sql_injection("admin' --") is True
    assert contains_sql_injection("UNION SELECT * FROM users") is True
    assert contains_sql_injection("Normal patient discharge notes") is False


def test_captcha_challenge_generation_and_verification() -> None:
    challenge = generate_captcha_challenge()
    assert "challenge_id" in challenge
    assert "question" in challenge
    assert "token" in challenge

    # Extract arithmetic from question e.g. "What is 10 + 5?" or "What is 12 - 4?"
    q = challenge["question"].replace("What is", "").replace("?", "").strip()
    parts = q.split()
    a, op, b = int(parts[0]), parts[1], int(parts[2])
    answer = a + b if op == "+" else a - b

    # Valid verification
    assert verify_captcha_solution(challenge["token"], answer) is True
    # Invalid answer
    assert verify_captcha_solution(challenge["token"], answer + 999) is False
    # Malformed token
    assert verify_captcha_solution("invalid.token", answer) is False


def test_webhook_signature_verification() -> None:
    secret = "test-webhook-secret-key-12345"
    payload = b'{"event": "encounter_discharged", "patient_id": "12345"}'

    # Compute valid signature
    import hashlib
    import hmac

    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    # Valid raw hex signature
    assert verify_webhook_signature(payload=payload, signature=sig, secret=secret) is True
    # Valid "sha256=" prefixed signature
    assert verify_webhook_signature(payload=payload, signature=f"sha256={sig}", secret=secret) is True
    # Invalid signature
    assert verify_webhook_signature(payload=payload, signature="wrong-sig", secret=secret) is False

    # Timestamp replay verification
    now = int(time.time())
    ts_sig = hmac.new(secret.encode("utf-8"), f"{now}.".encode("utf-8") + payload, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(payload=payload, signature=ts_sig, secret=secret, timestamp=now) is True

    # Expired timestamp (older than 300 seconds)
    assert verify_webhook_signature(payload=payload, signature=ts_sig, secret=secret, timestamp=now - 500) is False


def test_rate_limiter_buckets() -> None:
    ip = "192.168.1.100"
    # Auth bucket has limit of 15 requests
    for _ in range(15):
        is_limited, _, _ = is_rate_limited(ip, "auth")
        assert is_limited is False

    # 16th request must be rate limited
    is_limited, remaining, retry_after = is_rate_limited(ip, "auth")
    assert is_limited is True
    assert remaining == 0
    assert retry_after > 0


def test_sniff_file_kind_rejects_dangerous_extensions() -> None:
    pdf_bytes = b"%PDF-1.4\nTest document content"
    with pytest.raises(AppError) as exc:
        sniff_file_kind(pdf_bytes, client_filename="malicious.pdf.exe")
    assert "Prohibited executable or script extension" in str(exc.value.message)


def test_sniff_file_kind_rejects_polyglot_payloads() -> None:
    polyglot = b"%PDF-1.4\n<script>eval('malicious')</script>"
    with pytest.raises(AppError) as exc:
        sniff_file_kind(polyglot, client_filename="test.pdf")
    assert "script payload detected" in str(exc.value.message)


def test_sanitize_filename_forces_expected_extension() -> None:
    sanitized = sanitize_filename("my_report.pdf.exe", expected_ext="pdf")
    assert sanitized.endswith(".pdf")
    assert ".exe" not in sanitized


def test_idor_prevention_on_owned_cases(db: Session) -> None:
    owner = User(
        email=f"owner_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_pw",
        role="patient",
    )
    db.add(owner)
    db.flush()

    patient = Patient(preferred_language="en")
    db.add(patient)
    db.flush()

    case = Case(patient_id=patient.id, user_id=owner.id)
    db.add(case)
    db.commit()

    # 1. Access by owner succeeds
    fetched = doc_service.get_case(db, case.id, user=owner)
    assert fetched.id == case.id

    # 2. Access by another patient fails with 403
    other_user = User(
        email=f"other_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_pw",
        role="patient",
    )
    db.add(other_user)
    db.flush()

    with pytest.raises(AppError) as exc:
        doc_service.get_case(db, case.id, user=other_user)
    assert exc.value.status_code == 403

    # 3. Unauthenticated access on owned case fails with 401
    with pytest.raises(AppError) as exc_unauth:
        doc_service.get_case(db, case.id, user=None)
    assert exc_unauth.value.status_code == 401
