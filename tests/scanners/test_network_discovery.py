"""
Network Discovery (Nmap) scanner tests — Phase 04.

All subprocess calls are mocked — no real Nmap execution.
Covers: unavailable, timeout, malformed XML, disabled, IP safety check,
        port list building, XML parsing, security regression, integration.
"""

import subprocess
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

import pytest

from app.scanners.network_discovery import (
    NmapResult,
    PortObservation,
    _build_port_list,
    _parse_nmap_xml,
    scan_network,
)
from app.schemas.scan_result import ScannerErrorCode
from tests.scanners.conftest import make_https_target, make_http_target


# ── Helpers ───────────────────────────────────────────────────────────────────

def _good_xml(ip: str = "93.184.216.34", ports: list[tuple] | None = None) -> bytes:
    """
    Build minimal valid Nmap XML output.
    ports = [(portid, state, service_name), ...]
    """
    if ports is None:
        ports = [(80, "open", "http"), (443, "open", "https")]

    port_elems = ""
    for portid, state, svc in ports:
        port_elems += f"""
        <port protocol="tcp" portid="{portid}">
          <state state="{state}" reason="syn-ack"/>
          <service name="{svc}"/>
        </port>"""

    xml = f"""<?xml version="1.0" ?>
<nmaprun version="7.94" args="nmap -sT -p 80,443 {ip}">
  <host>
    <address addr="{ip}" addrtype="ipv4"/>
    <ports>
      {port_elems}
    </ports>
  </host>
</nmaprun>"""
    return xml.encode()


def _make_proc(stdout: bytes = b"", returncode: int = 0, stderr: bytes = b"") -> MagicMock:
    proc = MagicMock()
    proc.stdout = stdout
    proc.returncode = returncode
    proc.stderr = stderr
    return proc


# ── Nmap unavailable (binary missing) ─────────────────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value=None)
def test_nmap_binary_not_found(mock_which):
    target = make_https_target()
    result = scan_network(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.SCAN_MODULE_ERROR
    assert "not found" in result.error.message.lower()


@patch("app.scanners.network_discovery.shutil.which", return_value=None)
def test_nmap_unavailable_does_not_crash_other_modules(mock_which):
    """Missing nmap should gracefully return NmapResult(available=False) — never raise."""
    target = make_https_target()
    result = scan_network(target)
    assert isinstance(result, NmapResult)  # returns structured result, no exception


# ── Disabled by config ────────────────────────────────────────────────────────

@patch("app.scanners.network_discovery.get_settings")
def test_nmap_disabled_by_config(mock_settings):
    settings = MagicMock()
    settings.NMAP_ENABLED = False
    mock_settings.return_value = settings

    target = make_https_target()
    result = scan_network(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.UNSUPPORTED_TARGET


# ── Timeout ───────────────────────────────────────────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["nmap"], timeout=30))
def test_nmap_timeout_structured(mock_run, mock_which):
    target = make_https_target()
    result = scan_network(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.TIMEOUT


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["nmap"], timeout=30))
def test_nmap_timeout_does_not_raise(mock_run, mock_which):
    target = make_https_target()
    result = scan_network(target)  # must not propagate
    assert result is not None


# ── Malformed XML ─────────────────────────────────────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_malformed_xml_does_not_crash(mock_run, mock_which):
    mock_run.return_value = _make_proc(stdout=b"NOT XML AT ALL <<<>>>", returncode=0)
    target = make_https_target()
    result = scan_network(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.PARSER_ERROR


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_empty_xml_does_not_crash(mock_run, mock_which):
    mock_run.return_value = _make_proc(stdout=b"", returncode=0)
    target = make_https_target()
    result = scan_network(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.PARSER_ERROR


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_partial_xml_does_not_crash(mock_run, mock_which):
    mock_run.return_value = _make_proc(stdout=b"<?xml version='1.0'?><nmaprun>", returncode=0)
    target = make_https_target()
    result = scan_network(target)
    # May succeed with empty ports or fail gracefully — no exception
    assert isinstance(result, NmapResult)


# ── Non-zero exit code ────────────────────────────────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_nmap_nonzero_exit_structured(mock_run, mock_which):
    mock_run.return_value = _make_proc(stdout=b"", returncode=127, stderr=b"nmap: error")
    target = make_https_target()
    result = scan_network(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.SCAN_MODULE_ERROR


# ── Successful scan ───────────────────────────────────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_successful_scan_open_ports(mock_run, mock_which):
    xml = _good_xml(ports=[(80, "open", "http"), (443, "open", "https")])
    mock_run.return_value = _make_proc(stdout=xml, returncode=0)

    target = make_https_target()
    result = scan_network(target)

    assert result.available is True
    assert len(result.ports) == 2
    port_numbers = [p.port for p in result.ports]
    assert 80 in port_numbers
    assert 443 in port_numbers


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_scan_records_target_ip(mock_run, mock_which):
    xml = _good_xml(ip="93.184.216.34")
    mock_run.return_value = _make_proc(stdout=xml, returncode=0)

    target = make_https_target(ip="93.184.216.34")
    result = scan_network(target)

    assert result.target_ip == "93.184.216.34"


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_scan_no_open_ports(mock_run, mock_which):
    """No open ports → returns empty list, not error."""
    xml = b"""<?xml version="1.0"?>
<nmaprun version="7.94">
  <host><ports></ports></host>
</nmaprun>"""
    mock_run.return_value = _make_proc(stdout=xml, returncode=0)

    target = make_https_target()
    result = scan_network(target)

    assert result.available is True
    assert result.ports == []


# ── Security: scans selected_address not hostname ─────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_nmap_uses_ip_not_hostname(mock_run, mock_which):
    """
    CRITICAL: Nmap must receive the validated IP (selected_address),
    not the hostname — prevents DNS re-resolution / TOCTOU.
    """
    xml = _good_xml(ip="93.184.216.34")
    mock_run.return_value = _make_proc(stdout=xml, returncode=0)

    target = make_https_target(hostname="example.com", ip="93.184.216.34")
    scan_network(target)

    call_args = mock_run.call_args
    cmd = call_args[0][0] if call_args[0] else call_args[1].get("cmd", [])
    # The IP must appear in the command
    assert "93.184.216.34" in cmd
    # The hostname must NOT appear in the command
    assert "example.com" not in cmd


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_nmap_shell_false(mock_run, mock_which):
    """subprocess.run must always be called with shell=False."""
    xml = _good_xml()
    mock_run.return_value = _make_proc(stdout=xml, returncode=0)

    target = make_https_target()
    scan_network(target)

    call_kwargs = mock_run.call_args[1] if mock_run.call_args else {}
    assert call_kwargs.get("shell") is not True, "shell=True is forbidden"


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_nmap_no_dangerous_flags(mock_run, mock_which):
    """
    Nmap must not use dangerous flags:
    -A (aggressive), -sS (stealth), -O (OS detect), -sU (UDP), --script
    """
    xml = _good_xml()
    mock_run.return_value = _make_proc(stdout=xml, returncode=0)

    target = make_https_target()
    scan_network(target)

    cmd = mock_run.call_args[0][0]
    cmd_str = " ".join(str(c) for c in cmd)

    forbidden = ["-A", "-sS", "-O", "-sU", "--script"]
    for flag in forbidden:
        assert flag not in cmd_str, f"Forbidden flag {flag!r} found in Nmap command"


# ── Private/loopback IP blocked ───────────────────────────────────────────────

def test_private_ip_blocked_before_nmap():
    """
    Private IPs must be blocked by is_safe_for_scanning() before nmap runs.
    Phase 03 already blocked it at validate_target time, but we defence-in-depth
    check again inside scan_network.
    """
    from app.security.dns_resolver import DNSResult
    from app.security.target_validator import ValidatedTarget

    # Manually build a ValidatedTarget pointing at private IP
    # (normally Phase 03 would reject this, but we test defence-in-depth)
    dns = DNSResult(hostname="internal.example.com", addresses=("192.168.1.1",), success=True)
    private_target = ValidatedTarget(
        normalized_url="https://internal.example.com/",
        scheme="https",
        hostname="internal.example.com",
        port=443,
        path="/",
        query="",
        dns_result=dns,
        selected_address="192.168.1.1",
    )

    with patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap"):
        result = scan_network(private_target)

    assert result.available is False
    assert result.error.code == ScannerErrorCode.UNSUPPORTED_TARGET


def test_loopback_blocked_before_nmap():
    from app.security.dns_resolver import DNSResult
    from app.security.target_validator import ValidatedTarget

    dns = DNSResult(hostname="localhost", addresses=("127.0.0.1",), success=True)
    loopback_target = ValidatedTarget(
        normalized_url="https://localhost/",
        scheme="https",
        hostname="localhost",
        port=443,
        path="/",
        query="",
        dns_result=dns,
        selected_address="127.0.0.1",
    )
    with patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap"):
        result = scan_network(loopback_target)

    assert result.available is False
    assert result.error.code == ScannerErrorCode.UNSUPPORTED_TARGET


# ── Port list building ─────────────────────────────────────────────────────────

def test_build_port_list_basic():
    assert _build_port_list("80,443", 20) == [80, 443]


def test_build_port_list_sorted():
    assert _build_port_list("443,80", 20) == [80, 443]


def test_build_port_list_deduplicates():
    result = _build_port_list("80,80,443", 20)
    assert result.count(80) == 1


def test_build_port_list_invalid_entry_skipped():
    result = _build_port_list("80,abc,443", 20)
    assert result == [80, 443]


def test_build_port_list_max_ports_enforced():
    ports = ",".join(str(i) for i in range(1, 30))  # 29 ports
    result = _build_port_list(ports, 10)
    assert len(result) == 10


def test_build_port_list_out_of_range_skipped():
    result = _build_port_list("0,80,65536,443", 20)
    assert 0 not in result
    assert 65536 not in result
    assert 80 in result
    assert 443 in result


def test_build_port_list_empty_string():
    assert _build_port_list("", 20) == []


# ── XML parser ────────────────────────────────────────────────────────────────

def test_parse_nmap_xml_basic():
    xml = _good_xml(ports=[(80, "open", "http")])
    result = _parse_nmap_xml(xml, "93.184.216.34", [80, 443])
    assert result.available is True
    assert len(result.ports) == 1
    assert result.ports[0].port == 80
    assert result.ports[0].state == "open"
    assert result.ports[0].service_name == "http"


def test_parse_nmap_xml_extracts_version():
    xml = b"""<?xml version="1.0"?>
<nmaprun version="7.94">
  <host><ports></ports></host>
</nmaprun>"""
    result = _parse_nmap_xml(xml, "1.2.3.4", [80])
    assert result.nmap_version == "7.94"


def test_parse_nmap_xml_no_hosts():
    xml = b"""<?xml version="1.0"?>
<nmaprun version="7.94">
</nmaprun>"""
    result = _parse_nmap_xml(xml, "1.2.3.4", [80])
    assert result.available is True
    assert result.ports == []


def test_parse_nmap_xml_malformed_portid_skipped():
    xml = b"""<?xml version="1.0"?>
<nmaprun version="7.94">
  <host>
    <ports>
      <port protocol="tcp" portid="BAD">
        <state state="open"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="open"/>
        <service name="https"/>
      </port>
    </ports>
  </host>
</nmaprun>"""
    result = _parse_nmap_xml(xml, "1.2.3.4", [443])
    # Malformed portid skipped, valid port still parsed
    assert any(p.port == 443 for p in result.ports)


# ── No severity in output ─────────────────────────────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_no_severity_in_nmap_output(mock_run, mock_which):
    xml = _good_xml()
    mock_run.return_value = _make_proc(stdout=xml, returncode=0)

    target = make_https_target()
    result = scan_network(target)

    import json, dataclasses
    result_dict = dataclasses.asdict(result)
    result_json = json.dumps(result_dict)
    assert "severity" not in result_json.lower()
    assert "risk_score" not in result_json.lower()


# ── OSError / FileNotFoundError ───────────────────────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run", side_effect=FileNotFoundError("nmap not found"))
def test_nmap_file_not_found_at_exec_time(mock_run, mock_which):
    target = make_https_target()
    result = scan_network(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.SCAN_MODULE_ERROR


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run", side_effect=OSError("permission denied"))
def test_nmap_os_error_structured(mock_run, mock_which):
    target = make_https_target()
    result = scan_network(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.NETWORK_ERROR
