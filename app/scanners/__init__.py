"""
app/scanners — Phase 04 Core Security Scanner package.

Public API:
    CoreScanner    — orchestrator
    scan_tls       — TLS inspector
    scan_certificate — certificate metadata
    scan_http      — HTTP response inspector
    scan_headers   — security header parser
    scan_cookies   — cookie attribute parser
    scan_redirects — redirect chain inspector
    scan_network   — Nmap network discovery (gracefully unavailable)
"""

from app.scanners.scanner import CoreScanner
from app.scanners.tls_scanner import scan_tls
from app.scanners.certificate_scanner import scan_certificate
from app.scanners.http_scanner import scan_http
from app.scanners.header_scanner import scan_headers
from app.scanners.cookie_scanner import scan_cookies
from app.scanners.redirect_scanner import scan_redirects
from app.scanners.network_discovery import scan_network, NmapResult

__all__ = [
    "CoreScanner",
    "scan_tls",
    "scan_certificate",
    "scan_http",
    "scan_headers",
    "scan_cookies",
    "scan_redirects",
    "scan_network",
    "NmapResult",
]
