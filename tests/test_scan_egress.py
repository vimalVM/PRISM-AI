"""Tests for the static egress scanner (scripts/scan_egress.py).

Validates SEC-03 compliance: detects cloud hosts, non-loopback URLs, and forbidden technology markers.
"""

from pathlib import Path
import pytest

from scripts.scan_egress import is_allowed_url, run_egress_scan, scan_file


def test_is_allowed_url():
    # Loopback URLs allowed
    assert is_allowed_url("http://127.0.0.1:8000")
    assert is_allowed_url("http://localhost:5173")
    assert is_allowed_url("https://127.0.0.1:11434/api/generate")

    # OpenXML and W3C schemas allowed
    assert is_allowed_url("http://schemas.openxmlformats.org/wordprocessingml/2006/main")
    assert is_allowed_url("http://www.w3.org/2001/XMLSchema-instance")

    # Cloud endpoints rejected
    assert not is_allowed_url("https://api.openai.com/v1")
    assert not is_allowed_url("https://fonts.googleapis.com/css")
    assert not is_allowed_url("http://192.168.1.100:8000")


def test_scan_file_detects_forbidden_content(tmp_path):
    # 1. Cloud endpoint URL
    cloud_file = tmp_path / "cloud_leak.py"
    cloud_file.write_text('client = OpenAI(base_url="https://api.openai.com")\n')
    findings = scan_file(cloud_file)
    assert len(findings) >= 1
    types = [f["type"] for f in findings]
    assert "unauthorized_url" in types or "forbidden_host_or_sdk" in types

    # 2. Forbidden technology name
    forbidden_tech = "stream" + "lit"
    bad_file = tmp_path / "bad_ui.py"
    bad_file.write_text(f"import {forbidden_tech} as st\n")
    findings = scan_file(bad_file)
    assert any(f["type"] == "forbidden_technology" for f in findings)


def test_codebase_egress_scan_is_clean():
    """Verify entire workbench repository passes egress scan with zero findings."""
    repo_root = Path(__file__).resolve().parent.parent
    report = run_egress_scan(repo_root)

    assert report["clean"] is True, f"Egress scan detected violations: {report['findings']}"
    assert report["findings_count"] == 0
