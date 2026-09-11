"""
Tests for health and readiness endpoints.
Verifies liveness, response schema, HTTP status, and request-ID header.
"""


def test_health_returns_200(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_response_schema(client):
    response = client.get("/api/v1/health")
    body = response.json()
    assert body.get("success") is True
    assert body.get("data", {}).get("status") == "healthy"


def test_health_has_request_id_header(client):
    response = client.get("/api/v1/health")
    assert "x-request-id" in response.headers


def test_health_request_id_propagated(client):
    """A client-supplied request ID must be echoed back."""
    custom_id = "test-req-abc-123"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.headers.get("x-request-id") == custom_id


def test_ready_endpoint_exists(client):
    """Readiness endpoint must respond (200 or 503 — DB may not be up in CI)."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)


def test_ready_response_schema(client):
    response = client.get("/api/v1/health/ready")
    body = response.json()
    assert "success" in body
    assert "data" in body
    assert "status" in body["data"]
    assert "database" in body["data"]
    assert "ai" in body["data"]


def test_not_found_is_safe(client):
    """404 responses must not leak internal details."""
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    # Must not contain tracebacks
    text = response.text
    assert "Traceback" not in text
    assert "File " not in text
