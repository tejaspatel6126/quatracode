"""
Security error codes and exception class for Phase 03.

All SSRF/target-validation failures use TargetSecurityError with a
machine-readable code. This integrates with the existing AppError hierarchy.

SECURITY RULE: Error messages MUST NOT contain URL passwords, authorization
headers, API keys, or any credential-bearing URL components.
"""

from fastapi import status

from app.core.exceptions import AppError


# ── Machine-readable error codes (PHASE_03 §20) ───────────────────────────────

class SecurityCode:
    INVALID_URL                 = "INVALID_URL"
    UNSUPPORTED_SCHEME          = "UNSUPPORTED_SCHEME"
    INVALID_HOSTNAME            = "INVALID_HOSTNAME"
    URL_CREDENTIALS_NOT_ALLOWED = "URL_CREDENTIALS_NOT_ALLOWED"
    INVALID_PORT                = "INVALID_PORT"
    DNS_RESOLUTION_FAILED       = "DNS_RESOLUTION_FAILED"
    DNS_EMPTY_RESULT            = "DNS_EMPTY_RESULT"
    DNS_TIMEOUT                 = "DNS_TIMEOUT"
    PRIVATE_IP_BLOCKED          = "PRIVATE_IP_BLOCKED"
    LOOPBACK_BLOCKED            = "LOOPBACK_BLOCKED"
    LINK_LOCAL_BLOCKED          = "LINK_LOCAL_BLOCKED"
    METADATA_IP_BLOCKED         = "METADATA_IP_BLOCKED"
    RESERVED_IP_BLOCKED         = "RESERVED_IP_BLOCKED"
    MULTICAST_IP_BLOCKED        = "MULTICAST_IP_BLOCKED"
    UNSAFE_REDIRECT             = "UNSAFE_REDIRECT"
    DNS_REBINDING_DETECTED      = "DNS_REBINDING_DETECTED"
    NETWORK_POLICY_BLOCKED      = "NETWORK_POLICY_BLOCKED"
    TIMEOUT                     = "TIMEOUT"
    RESPONSE_SIZE_LIMIT_EXCEEDED = "RESPONSE_SIZE_LIMIT_EXCEEDED"
    CONNECTION_ERROR            = "CONNECTION_ERROR"


class TargetSecurityError(AppError):
    """
    Raised when a target URL fails security validation.

    Integrates with the existing AppError/exception-handler infrastructure so
    that API error responses are structured and never expose tracebacks.

    The 'code' field is always a value from SecurityCode — callers must never
    construct free-form codes.
    """

    def __init__(self, code: str, message: str) -> None:
        # 400 Bad Request for client-supplied invalid targets
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
