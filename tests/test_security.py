"""
Tests for security headers and safe error responses.
"""


SECURITY_HEADERS = [
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "content-security-policy",
    "x-request-id",
]


def test_security_headers_present_on_health(client):
    """Every API response must include the baseline security headers."""
    response = client.get("/api/v1/health")
    for header in SECURITY_HEADERS:
        assert header in response.headers, f"Missing header: {header}"


def test_x_content_type_options_value(client):
    response = client.get("/api/v1/health")
    assert response.headers.get("x-content-type-options") == "nosniff"


def test_x_frame_options_value(client):
    response = client.get("/api/v1/health")
    assert response.headers.get("x-frame-options") == "DENY"


def test_csp_contains_default_src(client):
    response = client.get("/api/v1/health")
    csp = response.headers.get("content-security-policy", "")
    assert "default-src" in csp


def test_csp_no_unsafe_eval(client):
    response = client.get("/api/v1/health")
    csp = response.headers.get("content-security-policy", "")
    assert "'unsafe-eval'" not in csp


def test_error_response_no_traceback(client):
    """Error responses must never expose Python tracebacks."""
    response = client.get("/api/v1/nonexistent-route-xyz")
    assert "Traceback" not in response.text
    assert "File " not in response.text
    assert "line " not in response.text.lower() or "content-security" in response.text.lower()


def test_application_starts(client):
    """Application must start and respond to requests."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
