"""Unit and integration tests for Firebase Auth token verification, deterministic user mapping,
and prevention of database case leakage (open Postgres fix).
"""

from __future__ import annotations

import base64
import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import (
    decode_firebase_token_payload,
    get_or_create_firebase_user,
)
from app.core.config import get_settings
from app.models import Case, Patient, User
from app.services import documents as doc_service


def _make_mock_firebase_jwt(
    uid: str = "firebase_user_123",
    project_id: str = "buttler-8e847",
    email: str = "patient@example.com",
    name: str = "Jane Doe",
    expired: bool = False,
) -> str:
    header = {"alg": "RS256", "typ": "JWT", "kid": "mock_kid"}
    now = int(time.time())
    payload = {
        "iss": f"https://securetoken.google.com/{project_id}",
        "aud": project_id,
        "auth_time": now - 60,
        "user_id": uid,
        "sub": uid,
        "iat": now - 60,
        "exp": (now - 300) if expired else (now + 3600),
        "email": email,
        "email_verified": True,
        "name": name,
    }
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig_b64 = "mock_sig_content"
    return f"{h_b64}.{p_b64}.{sig_b64}"


def test_decode_firebase_token_payload_valid() -> None:
    token = _make_mock_firebase_jwt(uid="uid_alpha", project_id="buttler-8e847")
    payload = decode_firebase_token_payload(token)
    assert payload is not None
    assert payload["sub"] == "uid_alpha"
    assert payload["email"] == "patient@example.com"


def test_decode_firebase_token_payload_expired() -> None:
    token = _make_mock_firebase_jwt(uid="uid_expired", expired=True)
    payload = decode_firebase_token_payload(token)
    assert payload is None


def test_decode_firebase_token_payload_wrong_project() -> None:
    token = _make_mock_firebase_jwt(uid="uid_wrong", project_id="other-project-999")
    payload = decode_firebase_token_payload(token)
    assert payload is None


def test_get_or_create_firebase_user_deterministic_uuid(db: Session) -> None:
    token = _make_mock_firebase_jwt(uid="deterministic_uid_456", email="alice@carelynx.local", name="Alice")
    payload = decode_firebase_token_payload(token)
    assert payload is not None

    user1 = get_or_create_firebase_user(payload, db)
    assert user1 is not None
    expected_uuid = uuid.uuid5(uuid.NAMESPACE_URL, "firebase:deterministic_uid_456")
    assert user1.id == expected_uuid
    assert user1.email == "alice@carelynx.local"
    assert user1.full_name == "Alice"

    # Subsequent resolution should yield the identical user record without error
    user2 = get_or_create_firebase_user(payload, db)
    assert user2 is not None
    assert user2.id == user1.id


def test_unauthenticated_cannot_list_cases_open_postgres_fixed(client: TestClient, db: Session) -> None:
    """Verifies that unauthenticated requests to /api/v1/cases return an empty list,
    preventing open database leakage across users.
    """
    # Create an owned case directly in DB
    patient = Patient(preferred_language="en")
    db.add(patient)
    db.flush()
    case = Case(patient_id=patient.id)
    db.add(case)
    db.commit()

    # Unauthenticated request must return []
    res = client.get("/api/v1/cases")
    assert res.status_code == 200
    assert res.json() == []


def test_firebase_authenticated_case_flow(client: TestClient, db: Session) -> None:
    """End-to-end test of Firebase ID token in Authorization header."""
    fb_token = _make_mock_firebase_jwt(uid="fb_patient_flow_777", email="flow@carelynx.local")
    headers = {"Authorization": f"Bearer {fb_token}"}

    # 1. Create a case with Firebase token
    res_create = client.post("/api/v1/cases", headers=headers)
    assert res_create.status_code == 201
    created_case_id = res_create.json()["id"]

    # 2. Verify case in DB is associated with the auto-provisioned user
    expected_uuid = uuid.uuid5(uuid.NAMESPACE_URL, "firebase:fb_patient_flow_777")
    db_case = db.get(Case, uuid.UUID(created_case_id))
    assert db_case is not None
    assert db_case.user_id == expected_uuid

    # 3. List cases with the same token -> returns the created case
    res_list = client.get("/api/v1/cases", headers=headers)
    assert res_list.status_code == 200
    cases = res_list.json()
    assert any(c["id"] == created_case_id for c in cases)

    # 4. Another Firebase user cannot see this case in their list
    other_token = _make_mock_firebase_jwt(uid="other_fb_user_888", email="other@carelynx.local")
    res_other = client.get("/api/v1/cases", headers={"Authorization": f"Bearer {other_token}"})
    assert res_other.status_code == 200
    other_cases = res_other.json()
    assert not any(c["id"] == created_case_id for c in other_cases)
