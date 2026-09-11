"""
Network Discovery Scanner — Phase 04 (Nmap integration).

Performs safe, bounded TCP port discovery using Nmap via subprocess.

═══════════════════════════════════════════════════════════════════════════════
SECURITY CONTRACT — READ BEFORE MODIFYING
═══════════════════════════════════════════════════════════════════════════════

1. ONLY ValidatedTarget is accepted — never raw user URLs or hostnames.
2. Nmap is invoked against selected_address (the pre-validated IP address
   from Phase 03 DNS resolution) — NOT the hostname. This prevents:
     - DNS re-resolution during scan (TOCTOU / DNS rebinding)
     - Nmap independently resolving to a different, unsafe IP
3. shell=False always — prevents shell injection.
4. Fixed argument list — no user-controlled Nmap flags.
5. Only ALLOWED_PORTS from settings are passed to Nmap (-p flag).
   NMAP_MAX_PORTS setting caps the absolute maximum.
6. No NSE scripts, no UDP, no OS detection, no stealth scanning,
   no version probing that sends exploit payloads.
7. Explicit timeout (NMAP_TIMEOUT) — Nmap process is killed on expiry.
8. XML output parsed into clean structured model — no raw stdout to API.
9. If Nmap is unavailable, missing, or disabled: returns graceful
   NmapResult(available=False) — does NOT crash the scan pipeline.

ALLOWED NMAP FLAGS:
  -sT   TCP connect scan (non-privileged, safe)
  -p    port list (derived from ALLOWED_PORTS + validation)
  -oX - XML output to stdout
  -n    no DNS resolution (we already have the IP)
  -Pn   skip host discovery (treat as up — we already validated it)
  --open show only open ports
  --host-timeout <N>s  per-host wall-clock limit

NEVER ADD:
  -A    (aggressive — enables OS detection, version probe, NSE, traceroute)
  -sV   (version detection can trigger exploitable service banners)
  --script=* (NSE — can execute active checks/exploits)
  -O    (OS detection)
  -sU   (UDP scan)
  -sS   (SYN/stealth scan — requires root, causes IDS alerts)
  --open combined with -sV (probes open ports aggressively)
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

from app.core.config import get_settings
from app.schemas.scan_result import ScannerError, ScannerErrorCode
from app.security.ip_classifier import is_safe_for_scanning
from app.security.target_validator import ValidatedTarget

logger = logging.getLogger(__name__)

# ── Observation models ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PortObservation:
    """
    Raw observation for a single scanned TCP port.
    No severity — Phase 05 interprets this.
    """
    port: int
    protocol: str                   # always "tcp" in Phase 04
    state: str                      # "open" | "closed" | "filtered"
    service_name: str | None = None # e.g. "http", "https", "ssh"
    product: str | None = None      # product name from Nmap (if -sV were used — kept for extension)
    version: str | None = None      # version string (if -sV were used)
    reason: str | None = None       # why Nmap classified this state


@dataclass
class NmapResult:
    """
    Raw network discovery observations from Nmap.

    available=False means Nmap could not run (binary missing, timeout,
    disabled by config, etc.). This is NOT a scan finding — the rest of
    the scan continues normally.
    """
    available: bool
    target_ip: str | None = None        # The IP that was scanned
    scanned_ports: list[int] = field(default_factory=list)   # Ports attempted
    ports: list[PortObservation] = field(default_factory=list)
    nmap_version: str | None = None
    scan_type: str = "TCP_CONNECT"      # Always TCP_CONNECT in Phase 04
    error: ScannerError | None = None


# ── Public interface ───────────────────────────────────────────────────────────

def scan_network(
    target: ValidatedTarget,
    nmap_binary: str | None = None,
    timeout: float | None = None,
) -> NmapResult:
    """
    Run a safe, bounded Nmap TCP scan against a ValidatedTarget.

    Scans only the pre-validated IP (target.selected_address) against
    the configured ALLOWED_PORTS list. Never re-resolves DNS.

    Parameters
    ----------
    target : ValidatedTarget
        Phase 03 validated target — provides the safe IP and port.
    nmap_binary : str, optional
        Override nmap executable path (useful for testing).
    timeout : float, optional
        Override scan timeout in seconds.

    Returns
    -------
    NmapResult
        Raw port state observations. Never raises.
    """
    settings = get_settings()

    # ── Disabled by config ────────────────────────────────────────────────────
    if not settings.NMAP_ENABLED:
        logger.info("Nmap scan skipped: NMAP_ENABLED=False")
        return NmapResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.UNSUPPORTED_TARGET,
                message="Network discovery is disabled by configuration.",
            ),
        )

    # ── Double-check IP safety (defence-in-depth) ─────────────────────────────
    # Phase 03 already validated this, but we re-check here because network
    # discovery is a higher-risk operation than HTTP.
    if not is_safe_for_scanning(target.selected_address):
        logger.warning(
            "Nmap refused: selected_address=%r is not safe for scanning",
            target.selected_address,
        )
        return NmapResult(
            available=False,
            target_ip=target.selected_address,
            error=ScannerError(
                code=ScannerErrorCode.UNSUPPORTED_TARGET,
                message="Target IP is not safe for network discovery.",
            ),
        )

    # ── Resolve nmap binary ───────────────────────────────────────────────────
    binary = nmap_binary or settings.NMAP_BINARY or "nmap"
    resolved_binary = shutil.which(binary)
    if resolved_binary is None:
        logger.warning("Nmap not found: binary=%r", binary)
        return NmapResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.SCAN_MODULE_ERROR,
                message="Nmap binary not found. Install nmap to enable network discovery.",
            ),
        )

    # ── Build safe port list ──────────────────────────────────────────────────
    port_list = _build_port_list(settings.ALLOWED_PORTS, settings.NMAP_MAX_PORTS)
    if not port_list:
        logger.warning("Nmap: no valid ports to scan")
        return NmapResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.SCAN_MODULE_ERROR,
                message="No valid ports configured for network discovery.",
            ),
        )

    scan_timeout = timeout if timeout is not None else settings.NMAP_TIMEOUT
    host_timeout_ms = int(scan_timeout * 1000)

    # ── Build fixed argument list (shell=False enforced) ──────────────────────
    # Target is selected_address (validated IP) — NOT the hostname
    cmd = [
        resolved_binary,
        "-sT",                          # TCP connect scan (non-privileged)
        "-n",                           # No DNS resolution (we have the IP)
        "-Pn",                          # Skip host discovery (treat as up)
        "--open",                       # Only show open ports
        f"--host-timeout={host_timeout_ms}ms",  # Per-host timeout
        "-oX", "-",                     # XML output to stdout
        "-p", ",".join(str(p) for p in port_list),  # Explicit port list
        target.selected_address,        # IP only — never hostname
    ]

    logger.info(
        "Nmap scan: ip=%r ports=%r timeout=%.1fs",
        target.selected_address, port_list, scan_timeout,
    )

    # ── Execute ───────────────────────────────────────────────────────────────
    try:
        proc = subprocess.run(
            cmd,
            shell=False,                # NEVER True
            capture_output=True,
            timeout=scan_timeout + 5,   # OS-level timeout slightly wider than --host-timeout
            check=False,                # We inspect returncode ourselves
        )
    except subprocess.TimeoutExpired:
        logger.warning("Nmap timeout: ip=%r after %.1fs", target.selected_address, scan_timeout)
        return NmapResult(
            available=False,
            target_ip=target.selected_address,
            scanned_ports=port_list,
            error=ScannerError(
                code=ScannerErrorCode.TIMEOUT,
                message="Nmap scan timed out.",
            ),
        )
    except FileNotFoundError:
        logger.warning("Nmap binary disappeared: %r", resolved_binary)
        return NmapResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.SCAN_MODULE_ERROR,
                message="Nmap binary not found at execution time.",
            ),
        )
    except OSError as exc:
        logger.warning("Nmap OS error: %s", type(exc).__name__)
        return NmapResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.NETWORK_ERROR,
                message="OS error while executing Nmap.",
            ),
        )

    if proc.returncode not in (0, 1):  # 0=success, 1=some hosts down (still valid)
        logger.warning(
            "Nmap non-zero exit: code=%d stderr=%r",
            proc.returncode, proc.stderr[:200] if proc.stderr else b"",
        )
        return NmapResult(
            available=False,
            target_ip=target.selected_address,
            scanned_ports=port_list,
            error=ScannerError(
                code=ScannerErrorCode.SCAN_MODULE_ERROR,
                message=f"Nmap exited with code {proc.returncode}.",
            ),
        )

    # ── Parse XML output ──────────────────────────────────────────────────────
    try:
        result = _parse_nmap_xml(proc.stdout, target.selected_address, port_list)
        logger.info(
            "Nmap scan complete: ip=%r open_ports=%d",
            target.selected_address,
            sum(1 for p in result.ports if p.state == "open"),
        )
        return result
    except Exception as exc:
        logger.warning("Nmap XML parse error: %s", type(exc).__name__)
        return NmapResult(
            available=False,
            target_ip=target.selected_address,
            scanned_ports=port_list,
            error=ScannerError(
                code=ScannerErrorCode.PARSER_ERROR,
                message="Failed to parse Nmap XML output.",
            ),
        )


# ── XML parser ─────────────────────────────────────────────────────────────────

def _parse_nmap_xml(
    xml_bytes: bytes,
    target_ip: str,
    scanned_ports: list[int],
) -> NmapResult:
    """
    Parse Nmap XML output into a NmapResult.

    Nmap XML structure (simplified):
      <nmaprun version="...">
        <host>
          <ports>
            <port protocol="tcp" portid="80">
              <state state="open" reason="syn-ack"/>
              <service name="http" product="..." version="..."/>
            </port>
          </ports>
        </host>
      </nmaprun>

    Only 'open' ports are returned (--open flag was passed to Nmap).
    """
    if not xml_bytes:
        raise ValueError("Empty Nmap XML output")

    root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))

    nmap_version = root.get("version")
    port_observations: list[PortObservation] = []

    for host_elem in root.findall("host"):
        ports_elem = host_elem.find("ports")
        if ports_elem is None:
            continue

        for port_elem in ports_elem.findall("port"):
            try:
                port_id = int(port_elem.get("portid", "0"))
                protocol = port_elem.get("protocol", "tcp")

                state_elem = port_elem.find("state")
                state = state_elem.get("state", "unknown") if state_elem is not None else "unknown"
                reason = state_elem.get("reason") if state_elem is not None else None

                service_elem = port_elem.find("service")
                service_name = None
                product = None
                version = None
                if service_elem is not None:
                    service_name = service_elem.get("name")
                    product = service_elem.get("product")
                    version = service_elem.get("version")

                port_observations.append(PortObservation(
                    port=port_id,
                    protocol=protocol,
                    state=state,
                    service_name=service_name or None,
                    product=product or None,
                    version=version or None,
                    reason=reason,
                ))
            except (ValueError, TypeError):
                # Skip malformed port entries — don't crash
                continue

    return NmapResult(
        available=True,
        target_ip=target_ip,
        scanned_ports=scanned_ports,
        ports=port_observations,
        nmap_version=nmap_version,
        scan_type="TCP_CONNECT",
    )


# ── Port list builder ─────────────────────────────────────────────────────────

def _build_port_list(allowed_ports_str: str, max_ports: int) -> list[int]:
    """
    Build a validated, bounded list of TCP ports to scan.

    Source: settings.ALLOWED_PORTS (e.g. "80,443")
    Limits: settings.NMAP_MAX_PORTS (absolute cap)

    Rules:
    - Only integers 1–65535 allowed
    - Silently skip invalid entries
    - Cap at max_ports
    - Return sorted, deduplicated list (deterministic)
    """
    ports: set[int] = set()
    for raw in allowed_ports_str.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            port = int(raw)
            if 1 <= port <= 65535:
                ports.add(port)
        except ValueError:
            logger.debug("Nmap: ignoring non-integer port entry %r", raw)

    sorted_ports = sorted(ports)
    if len(sorted_ports) > max_ports:
        logger.warning(
            "Nmap: port list truncated from %d to %d (NMAP_MAX_PORTS)",
            len(sorted_ports), max_ports,
        )
        sorted_ports = sorted_ports[:max_ports]

    return sorted_ports
