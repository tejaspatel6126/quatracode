"""
Shared test fixtures for Phase 04 scanner tests.

No real network connections. All DNS resolution is mocked.
All HTTP responses use MagicMock / controlled data.
"""

import datetime

import pytest

from app.security.dns_resolver import DNSResult
from app.security.target_validator import ValidatedTarget
from app.services.safe_http_client import SafeResponse


# ── ValidatedTarget factories ─────────────────────────────────────────────────

def make_https_target(
    hostname: str = "example.com",
    ip: str = "93.184.216.34",
    path: str = "/",
    query: str = "",
) -> ValidatedTarget:
    dns = DNSResult(hostname=hostname, addresses=(ip,), success=True)
    return ValidatedTarget(
        normalized_url=f"https://{hostname}{path}",
        scheme="https",
        hostname=hostname,
        port=443,
        path=path,
        query=query,
        dns_result=dns,
        selected_address=ip,
    )


def make_http_target(
    hostname: str = "example.com",
    ip: str = "93.184.216.34",
) -> ValidatedTarget:
    dns = DNSResult(hostname=hostname, addresses=(ip,), success=True)
    return ValidatedTarget(
        normalized_url=f"http://{hostname}/",
        scheme="http",
        hostname=hostname,
        port=80,
        path="/",
        query="",
        dns_result=dns,
        selected_address=ip,
    )


# ── SafeResponse factories ────────────────────────────────────────────────────

def make_response(
    status_code: int = 200,
    headers: dict[str, str] | None = None,
    body: bytes = b"",
    final_url: str = "https://example.com/",
    redirect_count: int = 0,
    selected_address: str = "93.184.216.34",
) -> SafeResponse:
    h = {k.lower(): v for k, v in (headers or {}).items()}
    return SafeResponse(
        status_code=status_code,
        headers=h,
        body=body,
        final_url=final_url,
        redirect_count=redirect_count,
        selected_address=selected_address,
    )


# ── Datetime helpers ──────────────────────────────────────────────────────────

UTC = datetime.timezone.utc

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(tz=UTC)

def utc_days_from_now(days: int) -> datetime.datetime:
    return utc_now() + datetime.timedelta(days=days)

def utc_days_ago(days: int) -> datetime.datetime:
    return utc_now() - datetime.timedelta(days=days)
