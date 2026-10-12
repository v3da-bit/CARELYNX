from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["inference_provider"] == "rule_based"
    assert body["app"] == "carelynx-api"
    assert body["version"] == "0.1.0"
    assert body["storage"] == "local_private"


def test_security_headers_and_request_id(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["X-Request-ID"]


def test_error_contract_no_stack_trace(client: TestClient) -> None:
    r = client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    err = r.json()["error"]
    assert set(err) == {"code", "message", "request_id"}
    assert err["code"] == "NOT_FOUND"
