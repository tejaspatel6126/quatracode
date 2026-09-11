"""
Safe HTTP Client tests — Phase 03.

All network I/O is mocked via httpx mock transport.
No real network connections are made.

Coverage:
  - GET / HEAD accepted
  - POST/PUT/PATCH/DELETE rejected
  - Redirect revalidation (public→public allowed, public→private blocked)
  - Redirect limit enforced
  - Response size limit enforced
  - Timeout handling
  - Connection error handling
  - DNS-rebinding: client connects to selected_address, not re-resolved address
"""

import pytest
import httpx
from unittest.mock import MagicMock, patch

from app.security.dns_resolver import DNSResult
from app.security.errors import SecurityCode, TargetSecurityError
from app.security.target_validator import ValidatedTarget
from app.services.safe_http_client import SafeHTTPClient, SafeResponse


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_target(
    hostname="example.com",
    scheme="https",
    port=443,
    ip="93.184.216.34",
    path="/",
    query="",
) -> ValidatedTarget:
    """Build a ValidatedTarget without going through validate_target()."""
    dns = DNSResult(hostname=hostname, addresses=(ip,), success=True)
    return ValidatedTarget(
        normalized_url=f"{scheme}://{hostname}{path}",
        scheme=scheme,
        hostname=hostname,
        port=port,
        path=path,
        query=query,
        dns_result=dns,
        selected_address=ip,
    )


def _mock_transport(status_code: int, body: bytes = b"", headers: dict = None):
    """Create an httpx MockTransport that returns a fixed response."""
    headers = headers or {}
    return httpx.MockTransport(
        lambda request: httpx.Response(status_code, content=body, headers=headers)
    )


# ── Method restrictions ───────────────────────────────────────────────────────

def test_get_method_accepted():
    target = _make_target()
    client = SafeHTTPClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.iter_bytes = MagicMock(return_value=iter([b"Hello"]))

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(return_value=mock_response)
        mock_cls.return_value = mock_instance

        response = client.get(target)
    assert response.status_code == 200


def test_head_method_accepted():
    target = _make_target()
    client = SafeHTTPClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    # HEAD response has no body — iter_bytes not called

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(return_value=mock_response)
        mock_cls.return_value = mock_instance

        response = client.head(target)
    assert response.status_code == 200


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_unsafe_methods_rejected(method):
    target = _make_target()
    client = SafeHTTPClient()
    with pytest.raises(TargetSecurityError) as exc:
        client._request(method, target)
    assert exc.value.code == SecurityCode.NETWORK_POLICY_BLOCKED


# ── Timeout handling ──────────────────────────────────────────────────────────

def test_connect_timeout_raises_structured_error():
    target = _make_target()
    client = SafeHTTPClient()

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(side_effect=httpx.TimeoutException("timeout"))
        mock_cls.return_value = mock_instance

        with pytest.raises(TargetSecurityError) as exc:
            client.get(target)
        assert exc.value.code == SecurityCode.TIMEOUT


def test_connection_error_raises_structured_error():
    target = _make_target()
    client = SafeHTTPClient()

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(
            side_effect=httpx.ConnectError("connection refused")
        )
        mock_cls.return_value = mock_instance

        with pytest.raises(TargetSecurityError) as exc:
            client.get(target)
        assert exc.value.code == SecurityCode.CONNECTION_ERROR


# ── Redirect security ─────────────────────────────────────────────────────────

def test_redirect_to_public_allowed():
    """Public → public redirect should be followed."""
    target = _make_target()
    client = SafeHTTPClient()

    call_count = {"n": 0}

    def mock_request(method, url, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return httpx.Response(
                302,
                headers={"location": "https://www.example.com/"},
                content=b"",
            )
        return httpx.Response(200, content=b"OK")

    def public_resolver(hostname, timeout=5.0):
        return DNSResult(hostname=hostname, addresses=("93.184.216.34",), success=True)

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(side_effect=mock_request)
        mock_cls.return_value = mock_instance

        with patch("app.services.safe_http_client.validate_target") as mock_vt:
            # Make redirect validation return a valid target
            mock_vt.return_value = _make_target(hostname="www.example.com")
            response = client.get(target)

    assert response.redirect_count == 1


def test_redirect_to_private_blocked():
    """Public → private redirect must be blocked."""
    target = _make_target()
    client = SafeHTTPClient()

    def mock_request(method, url, **kwargs):
        return httpx.Response(
            302,
            headers={"location": "http://10.0.0.1/"},
            content=b"",
        )

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(side_effect=mock_request)
        mock_cls.return_value = mock_instance

        with patch("app.services.safe_http_client.validate_target") as mock_vt:
            mock_vt.side_effect = TargetSecurityError(
                SecurityCode.PRIVATE_IP_BLOCKED,
                "Private IP blocked"
            )
            with pytest.raises(TargetSecurityError) as exc:
                client.get(target)
        assert exc.value.code == SecurityCode.UNSAFE_REDIRECT


def test_redirect_limit_enforced():
    """Redirects exceeding MAX_REDIRECTS must be rejected."""
    target = _make_target()
    client = SafeHTTPClient()

    # Always return a redirect
    def mock_request(method, url, **kwargs):
        return httpx.Response(
            302,
            headers={"location": "https://example.com/next"},
            content=b"",
        )

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(side_effect=mock_request)
        mock_cls.return_value = mock_instance

        with patch("app.services.safe_http_client.validate_target") as mock_vt:
            mock_vt.return_value = _make_target()
            with pytest.raises(TargetSecurityError) as exc:
                client.get(target)
    assert exc.value.code == SecurityCode.UNSAFE_REDIRECT


def test_redirect_missing_location_blocked():
    """302 without Location header must be blocked."""
    target = _make_target()
    client = SafeHTTPClient()

    def mock_request(method, url, **kwargs):
        return httpx.Response(302, content=b"")  # No Location header

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(side_effect=mock_request)
        mock_cls.return_value = mock_instance

        with pytest.raises(TargetSecurityError) as exc:
            client.get(target)
    assert exc.value.code == SecurityCode.UNSAFE_REDIRECT


# ── Response size limit ────────────────────────────────────────────────────────

def test_response_size_limit_enforced():
    """Response exceeding MAX_RESPONSE_SIZE must raise RESPONSE_SIZE_LIMIT_EXCEEDED."""
    from app.core.config import get_settings
    max_size = get_settings().MAX_RESPONSE_SIZE
    oversized = b"X" * (max_size + 1)

    target = _make_target()
    client = SafeHTTPClient()

    def mock_request(method, url, **kwargs):
        return httpx.Response(200, content=oversized)

    with patch("httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(side_effect=mock_request)
        # iter_bytes must yield chunks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}

        # Simulate iter_bytes yielding oversized data
        def iter_bytes(chunk_size=8192):
            yield oversized

        mock_response.iter_bytes = iter_bytes
        mock_instance.request = MagicMock(return_value=mock_response)
        mock_cls.return_value = mock_instance

        with pytest.raises(TargetSecurityError) as exc:
            client.get(target)
    assert exc.value.code == SecurityCode.RESPONSE_SIZE_LIMIT_EXCEEDED


# ── DNS rebinding protection ───────────────────────────────────────────────────

def test_client_uses_selected_address_not_hostname():
    """
    The client must connect to selected_address (validated IP), not to the
    hostname (which could re-resolve to a different address).
    Verify that the request URL contains the IP, not the hostname.
    """
    target = _make_target(hostname="example.com", ip="93.184.216.34", scheme="https", port=443)
    client = SafeHTTPClient()

    captured_url = {}

    def mock_request(method, url, **kwargs):
        captured_url["url"] = url
        return httpx.Response(200, content=b"OK")

    with patch("httpx.Client") as mock_cls:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_bytes = MagicMock(return_value=iter([b"OK"]))

        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.request = MagicMock(side_effect=mock_request)
        mock_cls.return_value = mock_instance

        client.get(target)

    # The URL used in the actual request must contain the IP, not "example.com"
    url_used = captured_url.get("url", "")
    assert "93.184.216.34" in url_used, (
        f"Expected IP 93.184.216.34 in request URL, got: {url_used}"
    )
    # hostname should appear only in the Host header, not in the connection URL
