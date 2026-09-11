"""
Cookie Scanner tests — Phase 04.

Verifies cookie attribute extraction and value redaction.
No network connections.
"""

import pytest

from app.scanners.cookie_scanner import (
    scan_cookies,
    _parse_cookie,
    _split_set_cookie_header,
)
from app.schemas.scan_result import ScannerErrorCode
from tests.scanners.conftest import make_response


# ── Cookie value redaction (critical security invariant) ──────────────────────

def test_cookie_value_always_redacted():
    """Cookie values must NEVER be stored — value_redacted must always be True."""
    response = make_response(headers={"set-cookie": "session=abc123; Secure; HttpOnly"})
    result = scan_cookies(response)
    assert len(result.cookies) == 1
    assert result.cookies[0].value_redacted is True


def test_cookie_value_not_in_json():
    """Sensitive cookie values must not appear in serialized output."""
    response = make_response(headers={"set-cookie": "auth_token=super_secret_value; HttpOnly"})
    result = scan_cookies(response)
    result_json = result.model_dump_json()
    assert "super_secret_value" not in result_json


# ── Secure attribute ──────────────────────────────────────────────────────────

def test_cookie_secure_present():
    obs = _parse_cookie("session=abc; Secure; HttpOnly")
    assert obs.secure is True


def test_cookie_secure_missing():
    obs = _parse_cookie("session=abc; HttpOnly")
    assert obs.secure is False


def test_cookie_secure_case_insensitive():
    obs = _parse_cookie("session=abc; SECURE")
    assert obs.secure is True


# ── HttpOnly attribute ────────────────────────────────────────────────────────

def test_cookie_httponly_present():
    obs = _parse_cookie("session=abc; HttpOnly")
    assert obs.http_only is True


def test_cookie_httponly_missing():
    obs = _parse_cookie("session=abc; Secure")
    assert obs.http_only is False


def test_cookie_httponly_case_insensitive():
    obs = _parse_cookie("session=abc; HTTPONLY")
    assert obs.http_only is True


# ── SameSite attribute ────────────────────────────────────────────────────────

def test_cookie_samesite_strict():
    obs = _parse_cookie("session=abc; SameSite=Strict")
    assert obs.same_site == "Strict"


def test_cookie_samesite_lax():
    obs = _parse_cookie("session=abc; SameSite=Lax")
    assert obs.same_site == "Lax"


def test_cookie_samesite_none():
    obs = _parse_cookie("session=abc; SameSite=None; Secure")
    assert obs.same_site == "None"
    assert obs.secure is True


def test_cookie_samesite_missing():
    obs = _parse_cookie("session=abc; Secure")
    assert obs.same_site is None


# ── Domain and Path ───────────────────────────────────────────────────────────

def test_cookie_domain():
    obs = _parse_cookie("pref=1; Domain=.example.com")
    assert obs.domain == ".example.com"


def test_cookie_path():
    obs = _parse_cookie("pref=1; Path=/app")
    assert obs.path == "/app"


# ── Max-Age and Expires ───────────────────────────────────────────────────────

def test_cookie_max_age():
    obs = _parse_cookie("pref=1; Max-Age=3600")
    assert obs.max_age == 3600


def test_cookie_max_age_invalid_does_not_crash():
    obs = _parse_cookie("pref=1; Max-Age=abc")
    assert obs.max_age is None
    assert obs.parse_error is not None


def test_cookie_expires():
    obs = _parse_cookie("pref=1; Expires=Wed, 21 Oct 2026 07:28:00 GMT")
    assert obs.expires is not None


# ── Multiple cookies ──────────────────────────────────────────────────────────

def test_multiple_cookies_via_newline():
    """httpx joins multiple Set-Cookie with newline."""
    header_val = "session=abc; Secure; HttpOnly\npref=1; Path=/"
    response = make_response(headers={"set-cookie": header_val})
    result = scan_cookies(response)
    assert len(result.cookies) == 2
    names = [c.name for c in result.cookies]
    assert "session" in names
    assert "pref" in names


def test_all_cookie_values_redacted_in_multiple():
    header_val = "session=secret123; Secure\ntoken=abcdef; HttpOnly"
    response = make_response(headers={"set-cookie": header_val})
    result = scan_cookies(response)
    result_json = result.model_dump_json()
    assert "secret123" not in result_json
    assert "abcdef" not in result_json


# ── No cookies ────────────────────────────────────────────────────────────────

def test_no_set_cookie_header():
    response = make_response(headers={})
    result = scan_cookies(response)
    assert result.available is True
    assert result.cookies == []


# ── Malformed cookie ──────────────────────────────────────────────────────────

def test_malformed_cookie_does_not_crash():
    obs = _parse_cookie(";;;")
    # Should return something or None — no crash
    # An empty/malformed string may return None
    # Either outcome is acceptable as long as no exception is raised


def test_empty_cookie_string_returns_none():
    obs = _parse_cookie("")
    assert obs is None


# ── None response ─────────────────────────────────────────────────────────────

def test_scan_cookies_none_response():
    result = scan_cookies(None)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.HTTP_ERROR


# ── Split function ────────────────────────────────────────────────────────────

def test_split_single_cookie():
    parts = _split_set_cookie_header("session=abc; Secure")
    assert len(parts) == 1


def test_split_multiple_cookies_newline():
    parts = _split_set_cookie_header("session=abc; Secure\npref=1; Path=/")
    assert len(parts) == 2


def test_split_empty_string():
    parts = _split_set_cookie_header("")
    assert len(parts) == 1  # returns [""] which is fine


# ── Security: no severity in output ──────────────────────────────────────────

def test_no_severity_in_cookie_output():
    response = make_response(headers={"set-cookie": "pref=1"})
    result = scan_cookies(response)
    result_json = result.model_dump_json()
    assert "severity" not in result_json.lower()
