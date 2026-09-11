"""
Scanner Orchestrator — Phase 04.

Central entry point: receives a ValidatedTarget and runs all scanner
modules in deterministic order, returning a single ScanResult.

Execution order (PHASE_04_SCANNER.md §8):
  1. TLS
  2. Certificate
  3. HTTP  (response passed to 4 + 5)
  4. Headers
  5. Cookies
  6. Redirects

INVARIANTS:
  - One module failing does NOT abort subsequent modules (partial failure)
  - No severity, no risk score, no AI anywhere in this file
  - All network I/O goes through Phase 03 boundary (ValidatedTarget + SafeHTTPClient)
  - No raw URL is ever passed to a network client here

DOES NOT:
  - Accept raw user URLs directly (caller must run validate_target first)
  - Calculate findings/severity (Phase 05)
  - Generate AI explanations (Phase 08)
"""

import datetime
import logging

from app.scanners.certificate_scanner import scan_certificate
from app.scanners.cookie_scanner import scan_cookies
from app.scanners.header_scanner import scan_headers
from app.scanners.http_scanner import scan_http
from app.scanners.network_discovery import NmapResult, scan_network
from app.scanners.redirect_scanner import scan_redirects
from app.scanners.tls_scanner import scan_tls
from app.schemas.scan_result import (
    ModuleResult,
    ModuleStatus,
    ScanResult,
    ScanStatus,
    ScannerError,
    ScannerErrorCode,
    ScannerModule,
)
from app.security.target_validator import ValidatedTarget
from app.services.safe_http_client import SafeHTTPClient

logger = logging.getLogger(__name__)

SCANNER_VERSION = "0.4.0"


class CoreScanner:
    """
    Orchestrates all Phase 04 scanner modules.

    Usage:
        validated = validate_target(user_url)
        scanner   = CoreScanner()
        result    = scanner.scan(validated)
    """

    def __init__(self, http_client: SafeHTTPClient | None = None) -> None:
        # Injectable SafeHTTPClient for testing
        self._http_client = http_client or SafeHTTPClient()

    def scan(self, target: ValidatedTarget) -> ScanResult:
        """
        Run all scanner modules against a Phase 03 validated target.

        Parameters
        ----------
        target : ValidatedTarget
            Must come from validate_target(). Never pass raw URLs here.

        Returns
        -------
        ScanResult
            Complete raw observations from all modules.
            Partial failures are represented in module_statuses.
        """
        started_at = datetime.datetime.now(tz=datetime.timezone.utc)

        logger.info(
            "Scan started: hostname=%r scheme=%r version=%s",
            target.hostname, target.scheme, SCANNER_VERSION,
        )

        result = ScanResult(
            target_url=target.normalized_url,
            target_hostname=target.hostname,
            target_scheme=target.scheme,
            scanner_version=SCANNER_VERSION,
            started_at=started_at,
        )

        module_statuses: list[ModuleResult] = []
        any_failed = False
        any_completed = False

        # ── 1. TLS ────────────────────────────────────────────────────────────
        try:
            tls_result = scan_tls(target)
            result.tls = tls_result
            status = ModuleStatus.FAILED if tls_result.error else ModuleStatus.COMPLETED
            if status == ModuleStatus.COMPLETED:
                any_completed = True
            else:
                any_failed = True
            module_statuses.append(ModuleResult(
                module=ScannerModule.TLS,
                status=status,
                error=tls_result.error,
            ))
        except Exception as exc:
            any_failed = True
            logger.exception("TLS module unexpected error: %s", type(exc).__name__)
            module_statuses.append(ModuleResult(
                module=ScannerModule.TLS,
                status=ModuleStatus.FAILED,
                error=ScannerError(
                    code=ScannerErrorCode.SCAN_MODULE_ERROR,
                    message="TLS scanner encountered an unexpected error.",
                ),
            ))

        # ── 2. Certificate ────────────────────────────────────────────────────
        try:
            cert_result = scan_certificate(target)
            result.certificate = cert_result
            status = ModuleStatus.FAILED if cert_result.error else ModuleStatus.COMPLETED
            if status == ModuleStatus.COMPLETED:
                any_completed = True
            else:
                any_failed = True
            module_statuses.append(ModuleResult(
                module=ScannerModule.CERTIFICATE,
                status=status,
                error=cert_result.error,
            ))
        except Exception as exc:
            any_failed = True
            logger.exception("Certificate module unexpected error: %s", type(exc).__name__)
            module_statuses.append(ModuleResult(
                module=ScannerModule.CERTIFICATE,
                status=ModuleStatus.FAILED,
                error=ScannerError(
                    code=ScannerErrorCode.SCAN_MODULE_ERROR,
                    message="Certificate scanner encountered an unexpected error.",
                ),
            ))

        # ── 3. HTTP (shared response for Headers + Cookies) ───────────────────
        raw_response = None
        try:
            http_result, raw_response = scan_http(target, client=self._http_client)
            result.http = http_result
            status = ModuleStatus.FAILED if http_result.error else ModuleStatus.COMPLETED
            if status == ModuleStatus.COMPLETED:
                any_completed = True
            else:
                any_failed = True
            module_statuses.append(ModuleResult(
                module=ScannerModule.HTTP,
                status=status,
                error=http_result.error,
            ))
        except Exception as exc:
            any_failed = True
            logger.exception("HTTP module unexpected error: %s", type(exc).__name__)
            module_statuses.append(ModuleResult(
                module=ScannerModule.HTTP,
                status=ModuleStatus.FAILED,
                error=ScannerError(
                    code=ScannerErrorCode.SCAN_MODULE_ERROR,
                    message="HTTP scanner encountered an unexpected error.",
                ),
            ))

        # ── 4. Headers (depends on raw_response from HTTP) ────────────────────
        try:
            if raw_response is not None:
                headers_result = scan_headers(raw_response)
            else:
                from app.schemas.scan_result import HeadersResult
                headers_result = HeadersResult(
                    available=False,
                    error=ScannerError(
                        code=ScannerErrorCode.HTTP_ERROR,
                        message="No HTTP response available.",
                    ),
                )
            result.headers = headers_result
            status = ModuleStatus.FAILED if headers_result.error else ModuleStatus.COMPLETED
            if status == ModuleStatus.COMPLETED:
                any_completed = True
            else:
                any_failed = True
            module_statuses.append(ModuleResult(
                module=ScannerModule.HEADERS,
                status=status,
                error=headers_result.error,
            ))
        except Exception as exc:
            any_failed = True
            logger.exception("Headers module unexpected error: %s", type(exc).__name__)
            module_statuses.append(ModuleResult(
                module=ScannerModule.HEADERS,
                status=ModuleStatus.FAILED,
                error=ScannerError(
                    code=ScannerErrorCode.SCAN_MODULE_ERROR,
                    message="Header scanner encountered an unexpected error.",
                ),
            ))

        # ── 5. Cookies (depends on raw_response from HTTP) ────────────────────
        try:
            if raw_response is not None:
                cookies_result = scan_cookies(raw_response)
            else:
                from app.schemas.scan_result import CookiesResult
                cookies_result = CookiesResult(
                    available=False,
                    error=ScannerError(
                        code=ScannerErrorCode.HTTP_ERROR,
                        message="No HTTP response available.",
                    ),
                )
            result.cookies = cookies_result
            status = ModuleStatus.FAILED if cookies_result.error else ModuleStatus.COMPLETED
            if status == ModuleStatus.COMPLETED:
                any_completed = True
            else:
                any_failed = True
            module_statuses.append(ModuleResult(
                module=ScannerModule.COOKIES,
                status=status,
                error=cookies_result.error,
            ))
        except Exception as exc:
            any_failed = True
            logger.exception("Cookies module unexpected error: %s", type(exc).__name__)
            module_statuses.append(ModuleResult(
                module=ScannerModule.COOKIES,
                status=ModuleStatus.FAILED,
                error=ScannerError(
                    code=ScannerErrorCode.SCAN_MODULE_ERROR,
                    message="Cookie scanner encountered an unexpected error.",
                ),
            ))

        # ── 6. Redirects ──────────────────────────────────────────────────────
        try:
            redirects_result = scan_redirects(target, client=self._http_client)
            result.redirects = redirects_result
            status = ModuleStatus.FAILED if redirects_result.error else ModuleStatus.COMPLETED
            if status == ModuleStatus.COMPLETED:
                any_completed = True
            else:
                any_failed = True
            module_statuses.append(ModuleResult(
                module=ScannerModule.REDIRECTS,
                status=status,
                error=redirects_result.error,
            ))
        except Exception as exc:
            any_failed = True
            logger.exception("Redirects module unexpected error: %s", type(exc).__name__)
            module_statuses.append(ModuleResult(
                module=ScannerModule.REDIRECTS,
                status=ModuleStatus.FAILED,
                error=ScannerError(
                    code=ScannerErrorCode.SCAN_MODULE_ERROR,
                    message="Redirect scanner encountered an unexpected error.",
                ),
            ))

        # ── 7. Network Discovery (Nmap) ───────────────────────────────────────
        try:
            nmap_result = scan_network(target)
            result.network = nmap_result
            # available=False + no error = disabled/skipped (not a failure)
            # available=False + error     = actual failure
            # available=True              = completed
            if not nmap_result.available and nmap_result.error is None:
                nmap_status = ModuleStatus.SKIPPED
            elif nmap_result.error:
                nmap_status = ModuleStatus.FAILED
                any_failed = True
            else:
                nmap_status = ModuleStatus.COMPLETED
                any_completed = True
            module_statuses.append(ModuleResult(
                module=ScannerModule.NETWORK,
                status=nmap_status,
                error=nmap_result.error,
            ))
        except Exception as exc:
            any_failed = True
            logger.exception("Network discovery unexpected error: %s", type(exc).__name__)
            module_statuses.append(ModuleResult(
                module=ScannerModule.NETWORK,
                status=ModuleStatus.FAILED,
                error=ScannerError(
                    code=ScannerErrorCode.SCAN_MODULE_ERROR,
                    message="Network discovery encountered an unexpected error.",
                ),
            ))

        # ── Finalize ──────────────────────────────────────────────────────────
        completed_at = datetime.datetime.now(tz=datetime.timezone.utc)
        result.completed_at = completed_at
        result.module_statuses = module_statuses

        if any_failed and any_completed:
            result.status = ScanStatus.PARTIAL
        elif any_failed and not any_completed:
            result.status = ScanStatus.FAILED
        else:
            result.status = ScanStatus.COMPLETED

        elapsed = (completed_at - started_at).total_seconds()
        logger.info(
            "Scan completed: hostname=%r status=%s elapsed=%.2fs modules=%d",
            target.hostname, result.status.value, elapsed, len(module_statuses),
        )

        return result
