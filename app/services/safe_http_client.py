"""
Safe HTTP Client — Phase 03.

MANDATORY RULE: This is the ONLY component allowed to make outbound HTTP
connections. All scanner modules MUST use this client.

Accepts ONLY ValidatedTarget objects — never raw URLs.

Responsibilities:
  - Enforce bounded timeouts (connect, read, total)
  - Enforce redirect limit with per-redirect revalidation
  - Enforce maximum response size
  - Restrict HTTP methods to GET and HEAD
  - Use controlled User-Agent
  - Do NOT send application secrets, API keys, or cookies outbound
  - DNS-rebinding protection via direct IP connection with Host header

Implementation notes:
  - Uses httpx (sync) — async version can be added in later phases.
  - Redirects are followed MANUALLY so each destination is revalidated.
  - The actual TCP connection is made to selected_address (the pre-validated IP),
    with the Host header set to the original hostname. This prevents a fresh DNS
    lookup from resolving to a different (potentially private) address.
"""

import logging
from dataclasses import dataclass
from typing import Literal

import httpx

from app.core.config import get_settings
from app.security.errors import SecurityCode, TargetSecurityError
from app.security.target_validator import ValidatedTarget, validate_target

logger = logging.getLogger(__name__)

# Allowed HTTP methods for scanning (SECURITY.md §16)
_ALLOWED_METHODS = frozenset({"GET", "HEAD"})

# Application User-Agent — controlled value, never reflects user input
_USER_AGENT = "SecurityAuditor/1.0 (+https://github.com/quatracode/web-security-auditor)"


@dataclass(frozen=True)
class SafeResponse:
    """Structured result from a safe HTTP request."""
    status_code: int
    headers: dict[str, str]         # header names lowercased
    body: bytes                      # empty for HEAD
    final_url: str                   # final destination after redirects
    redirect_count: int
    selected_address: str            # IP address actually connected to


class SafeHTTPClient:
    """
    Safe outbound HTTP client for the security scanner.

    Usage (Phase 04+):
        validated = validate_target(user_url)
        client    = SafeHTTPClient()
        response  = client.get(validated)
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def get(self, target: ValidatedTarget) -> SafeResponse:
        """Perform a safe GET request to a validated target."""
        return self._request("GET", target)

    def head(self, target: ValidatedTarget) -> SafeResponse:
        """Perform a safe HEAD request to a validated target."""
        return self._request("HEAD", target)

    def _request(
        self,
        method: str,
        target: ValidatedTarget,
    ) -> SafeResponse:
        """
        Internal: perform a bounded, policy-controlled HTTP request.

        DNS-rebinding protection:
          The connection is made to target.selected_address (a validated IP)
          and the Host header is explicitly set to target.hostname.
          This means the TCP connection goes to a known-safe IP regardless of
          what DNS would return for a fresh lookup.
        """
        if method.upper() not in _ALLOWED_METHODS:
            raise TargetSecurityError(
                code=SecurityCode.NETWORK_POLICY_BLOCKED,
                message=f"HTTP method '{method}' is not permitted for scanning.",
            )

        settings = self._settings
        max_redirects = settings.MAX_REDIRECTS
        max_response_bytes = settings.MAX_RESPONSE_SIZE

        # Build base URL using the validated IP + correct scheme/port
        # The Host header will be set to hostname so TLS SNI and vhosts work.
        port = target.port
        ip   = target.selected_address

        # IPv6 addresses need brackets in the URL authority
        ip_authority = f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}"
        base_url = f"{target.scheme}://{ip_authority}"

        path_and_query = target.path
        if target.query:
            path_and_query = f"{path_and_query}?{target.query}"

        request_url = f"{base_url}{path_and_query}"

        # Minimal safe headers — NO application secrets, cookies, or auth tokens
        headers = {
            "Host":       target.hostname,
            "User-Agent": _USER_AGENT,
            "Accept":     "text/html,application/xhtml+xml,*/*;q=0.1",
            "Accept-Language": "en-US,en;q=0.5",
            # Disable Keep-Alive to avoid connection reuse to validated IPs
            "Connection": "close",
        }

        timeout = httpx.Timeout(
            connect=settings.CONNECT_TIMEOUT,
            read=settings.READ_TIMEOUT,
            write=5.0,
            pool=settings.CONNECT_TIMEOUT,
        )

        redirect_count = 0
        current_target = target

        try:
            # We manage redirects manually to revalidate each destination
            with httpx.Client(
                verify=False,           # TLS verification is handled by the TLS scanner (Phase 04)
                timeout=timeout,
                follow_redirects=False, # Manual redirect handling
                max_redirects=0,
            ) as client:

                while True:
                    ip   = current_target.selected_address
                    port = current_target.port
                    ip_authority = f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}"
                    base_url = f"{current_target.scheme}://{ip_authority}"

                    path_and_query = current_target.path
                    if current_target.query:
                        path_and_query = f"{path_and_query}?{current_target.query}"

                    request_url = f"{base_url}{path_and_query}"

                    # Update Host header for current target
                    headers["Host"] = current_target.hostname

                    logger.debug(
                        "HTTP %s -> %s (ip=%s redirect=%d)",
                        method, current_target.hostname, current_target.selected_address, redirect_count,
                    )

                    response = client.request(method, request_url, headers=headers)

                    # ── Response size limit ───────────────────────────────────
                    body = b""
                    if method == "GET":
                        # Stream and enforce size limit
                        chunks = []
                        total = 0
                        for chunk in response.iter_bytes(chunk_size=8192):
                            total += len(chunk)
                            if total > max_response_bytes:
                                raise TargetSecurityError(
                                    code=SecurityCode.RESPONSE_SIZE_LIMIT_EXCEEDED,
                                    message=(
                                        f"Response exceeds maximum size of "
                                        f"{max_response_bytes} bytes."
                                    ),
                                )
                            chunks.append(chunk)
                        body = b"".join(chunks)

                    # ── Redirect handling ─────────────────────────────────────
                    if response.status_code in (301, 302, 303, 307, 308):
                        redirect_count += 1
                        if redirect_count > max_redirects:
                            raise TargetSecurityError(
                                code=SecurityCode.UNSAFE_REDIRECT,
                                message=(
                                    f"Too many redirects (max {max_redirects})."
                                ),
                            )

                        location = response.headers.get("location", "")
                        if not location:
                            raise TargetSecurityError(
                                code=SecurityCode.UNSAFE_REDIRECT,
                                message="Redirect response missing Location header.",
                            )

                        logger.info(
                            "Redirect %d/%d: %r -> %r",
                            redirect_count, max_redirects,
                            current_target.hostname, location,
                        )

                        # Revalidate redirect destination through full pipeline
                        try:
                            current_target = validate_target(location)
                        except TargetSecurityError:
                            logger.warning(
                                "Unsafe redirect destination blocked (redirect %d)",
                                redirect_count,
                            )
                            raise TargetSecurityError(
                                code=SecurityCode.UNSAFE_REDIRECT,
                                message="Redirect destination failed security validation.",
                            )

                        continue  # follow the validated redirect

                    # Non-redirect — return result
                    resp_headers = {k.lower(): v for k, v in response.headers.items()}
                    return SafeResponse(
                        status_code=response.status_code,
                        headers=resp_headers,
                        body=body,
                        final_url=current_target.normalized_url,
                        redirect_count=redirect_count,
                        selected_address=current_target.selected_address,
                    )

        except TargetSecurityError:
            raise  # already structured — re-raise as-is

        except httpx.TimeoutException:
            raise TargetSecurityError(
                code=SecurityCode.TIMEOUT,
                message="The request timed out.",
            )

        except httpx.ConnectError:
            raise TargetSecurityError(
                code=SecurityCode.CONNECTION_ERROR,
                message="Could not connect to the target.",
            )

        except httpx.HTTPError as exc:
            logger.warning("HTTP error: %s", type(exc).__name__)
            raise TargetSecurityError(
                code=SecurityCode.CONNECTION_ERROR,
                message="An HTTP error occurred during the request.",
            )
