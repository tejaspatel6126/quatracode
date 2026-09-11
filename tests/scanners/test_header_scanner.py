"""
Header Scanner tests — Phase 04.

Tests all security header parsers.
No network connections — headers are injected via SafeResponse.
"""

import pytest

from app.scanners.header_scanner import (
    scan_headers,
    _parse_hsts,
    _parse_csp,
    _parse_x_content_type_options,
    _parse_frame_protection,
    _parse_referrer_policy,
    _parse_permissions_policy,
)
from app.schemas.scan_result import ScannerErrorCode
from tests.scanners.conftest import make_response


# ── HSTS ──────────────────────────────────────────────────────────────────────

def test_hsts_missing():
    obs = _parse_hsts({})
    assert obs.present is False
    assert obs.max_age is None
    assert obs.include_subdomains is False
    assert obs.preload is False


def test_hsts_full():
    obs = _parse_hsts({"strict-transport-security": "max-age=31536000; includeSubDomains; preload"})
    assert obs.present is True
    assert obs.max_age == 31536000
    assert obs.include_subdomains is True
    assert obs.preload is True
    assert obs.parse_error is None


def test_hsts_max_age_only():
    obs = _parse_hsts({"strict-transport-security": "max-age=86400"})
    assert obs.present is True
    assert obs.max_age == 86400
    assert obs.include_subdomains is False
    assert obs.preload is False


def test_hsts_mixed_casing():
    obs = _parse_hsts({"strict-transport-security": "MAX-AGE=3600; IncludeSubDomains"})
    assert obs.present is True
    assert obs.max_age == 3600
    assert obs.include_subdomains is True


def test_hsts_malformed_max_age_does_not_crash():
    obs = _parse_hsts({"strict-transport-security": "max-age=abc"})
    assert obs.present is True
    assert obs.max_age is None
    assert obs.parse_error is not None


def test_hsts_empty_value_does_not_crash():
    obs = _parse_hsts({"strict-transport-security": ""})
    assert obs.present is True
    assert obs.max_age is None


def test_hsts_unknown_directive_ignored():
    obs = _parse_hsts({"strict-transport-security": "max-age=3600; unknownDirective"})
    assert obs.max_age == 3600
    assert obs.parse_error is None  # Unknown directives silently ignored


# ── CSP ───────────────────────────────────────────────────────────────────────

def test_csp_missing():
    obs = _parse_csp({})
    assert obs.present is False
    assert obs.directive_names == []


def test_csp_basic():
    obs = _parse_csp({"content-security-policy": "default-src 'self'"})
    assert obs.present is True
    assert "default-src" in obs.directive_names


def test_csp_multiple_directives():
    policy = "default-src 'self'; script-src 'self' https://cdn.example.com; img-src *"
    obs = _parse_csp({"content-security-policy": policy})
    assert obs.present is True
    assert "default-src" in obs.directive_names
    assert "script-src" in obs.directive_names
    assert "img-src" in obs.directive_names


def test_csp_directive_names_sorted():
    policy = "z-directive 'self'; a-directive 'none'"
    obs = _parse_csp({"content-security-policy": policy})
    assert obs.directive_names == sorted(obs.directive_names)


def test_csp_duplicate_directives_deduplicated():
    policy = "default-src 'self'; default-src 'none'"
    obs = _parse_csp({"content-security-policy": policy})
    assert obs.directive_names.count("default-src") == 1


def test_csp_empty_policy_does_not_crash():
    obs = _parse_csp({"content-security-policy": ""})
    assert obs.present is True
    assert obs.directive_names == []


def test_csp_malformed_does_not_crash():
    obs = _parse_csp({"content-security-policy": ";;;"})
    assert obs.present is True
    # No crash


# ── X-Content-Type-Options ────────────────────────────────────────────────────

def test_x_content_type_missing():
    obs = _parse_x_content_type_options({})
    assert obs.present is False


def test_x_content_type_nosniff():
    obs = _parse_x_content_type_options({"x-content-type-options": "nosniff"})
    assert obs.present is True
    assert obs.normalized_value == "nosniff"


def test_x_content_type_case_insensitive():
    obs = _parse_x_content_type_options({"x-content-type-options": "NOSNIFF"})
    assert obs.present is True
    assert obs.normalized_value == "nosniff"


def test_x_content_type_unexpected_value_captured():
    obs = _parse_x_content_type_options({"x-content-type-options": "sniff"})
    assert obs.present is True
    assert obs.normalized_value == "sniff"


# ── Frame protection ──────────────────────────────────────────────────────────

def test_frame_protection_none():
    obs = _parse_frame_protection({})
    assert obs.x_frame_options_present is False
    assert obs.csp_frame_ancestors_present is False


def test_frame_protection_xfo_deny():
    obs = _parse_frame_protection({"x-frame-options": "DENY"})
    assert obs.x_frame_options_present is True
    assert obs.x_frame_options_value == "DENY"


def test_frame_protection_xfo_sameorigin():
    obs = _parse_frame_protection({"x-frame-options": "SAMEORIGIN"})
    assert obs.x_frame_options_present is True


def test_frame_protection_csp_frame_ancestors():
    obs = _parse_frame_protection({
        "content-security-policy": "default-src 'self'; frame-ancestors 'none'"
    })
    assert obs.csp_frame_ancestors_present is True
    assert obs.csp_frame_ancestors_value == "'none'"


def test_frame_protection_both_present():
    obs = _parse_frame_protection({
        "x-frame-options": "DENY",
        "content-security-policy": "frame-ancestors 'self'",
    })
    assert obs.x_frame_options_present is True
    assert obs.csp_frame_ancestors_present is True


# ── Referrer-Policy ───────────────────────────────────────────────────────────

def test_referrer_policy_missing():
    obs = _parse_referrer_policy({})
    assert obs.present is False


def test_referrer_policy_known_value():
    obs = _parse_referrer_policy({"referrer-policy": "strict-origin-when-cross-origin"})
    assert obs.present is True
    assert obs.normalized_value == "strict-origin-when-cross-origin"
    assert obs.parse_error is None


def test_referrer_policy_unknown_value_captured():
    obs = _parse_referrer_policy({"referrer-policy": "custom-policy"})
    assert obs.present is True
    assert obs.parse_error is not None  # Unknown value flagged


def test_referrer_policy_case_normalized():
    obs = _parse_referrer_policy({"referrer-policy": "No-Referrer"})
    assert obs.normalized_value == "no-referrer"


# ── Permissions-Policy ────────────────────────────────────────────────────────

def test_permissions_policy_missing():
    obs = _parse_permissions_policy({})
    assert obs.present is False


def test_permissions_policy_present():
    obs = _parse_permissions_policy({"permissions-policy": "camera=(), microphone=()"})
    assert obs.present is True
    assert obs.raw_value == "camera=(), microphone=()"


# ── Full scan_headers ─────────────────────────────────────────────────────────

def test_scan_headers_full_response():
    response = make_response(headers={
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy":   "default-src 'self'",
        "X-Content-Type-Options":    "nosniff",
        "X-Frame-Options":           "DENY",
        "Referrer-Policy":           "strict-origin",
        "Permissions-Policy":        "camera=()",
    })
    result = scan_headers(response)
    assert result.available is True
    assert result.hsts.present is True
    assert result.csp.present is True
    assert result.x_content_type_options.present is True
    assert result.frame_protection.x_frame_options_present is True
    assert result.referrer_policy.present is True
    assert result.permissions_policy.present is True


def test_scan_headers_no_security_headers():
    response = make_response(headers={})
    result = scan_headers(response)
    assert result.available is True
    assert result.hsts.present is False
    assert result.csp.present is False
    assert result.x_content_type_options.present is False
    assert result.frame_protection.x_frame_options_present is False
    assert result.referrer_policy.present is False
    assert result.permissions_policy.present is False


def test_scan_headers_none_response():
    result = scan_headers(None)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.HTTP_ERROR


def test_scan_headers_case_insensitive():
    """Header names from SafeResponse are already lowercased — verify this works."""
    response = make_response(headers={
        "strict-transport-security": "max-age=300",  # lowercase
        "CONTENT-SECURITY-POLICY":   "default-src 'self'",  # uppercase → lowercased by make_response
    })
    result = scan_headers(response)
    assert result.hsts.present is True
    assert result.csp.present is True


def test_scan_headers_no_severity_in_output():
    """Headers result must not contain severity."""
    response = make_response(headers={})
    result = scan_headers(response)
    result_json = result.model_dump_json()
    assert "severity" not in result_json.lower()
