"""Static egress scanner for Sovereign AI Workbench.

Implements SEC-03 and 03_SECURITY_AND_ACCESS.md §3.6:
Scans code directories (backend, agent, tools, rag, models, scripts, docker, frontend) for:
- Outbound external URLs (non-loopback http/https)
- Cloud AI SDKs and cloud endpoint domains
- Forbidden technology identifiers (Open WebUI, n8n, Streamlit, LangSmith)
- Telemetry trackers and cloud CDN references

Writes results to logs/egress_scan.json and returns non-zero exit code on violation.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Set


# Allowed domains and URL prefixes
ALLOWED_URL_PATTERNS = [
    re.compile(r"^https?://(127\.0\.0\.1|localhost|::1)(:\d+)?(/.*)?$", re.IGNORECASE),
    re.compile(r"^https?://schemas\.openxmlformats\.org(/.*)?$", re.IGNORECASE),  # OpenXML schema URIs
    re.compile(r"^https?://www\.w3\.org(/.*)?$", re.IGNORECASE),  # Standard XML namespace
]

# Cloud endpoints, telemetry hosts, and external SDK markers
FORBIDDEN_HOSTS = [
    "openai",
    "anthropic",
    "googleapis",
    "azure",
    "sentry",
    "posthog",
    "segment.io",
    "segment.com",
    "mixpanel",
    "langsmith",
    "langfuse",
    "cdn.",
    "fonts.googleapis",
    "unpkg",
    "cdnjs",
    "jsdelivr",
]

# Forbidden technologies (assembled without literal occurrences to avoid self-match)
FORBIDDEN_TECHS = [
    "open" + "webui",
    "open-" + "webui",
    "n8" + "n",
    "stream" + "lit",
]

DIRECTORIES_TO_SCAN = [
    "backend",
    "agent",
    "tools",
    "rag",
    "models",
    "scripts",
    "docker",
    "frontend/src",
]

IGNORE_EXTENSIONS = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".db",
    ".sqlite",
}

IGNORE_FILES = {
    "scan_egress.py",  # Exclude self
}


def is_allowed_url(url: str) -> bool:
    """Check if URL is an approved local loopback or standard XML schema."""
    for pattern in ALLOWED_URL_PATTERNS:
        if pattern.match(url):
            return True
    return False


def scan_file(file_path: Path) -> List[Dict[str, Any]]:
    """Scan an individual file for forbidden egress markers."""
    findings: List[Dict[str, Any]] = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return [{"file": str(file_path), "line": 0, "type": "read_error", "match": str(exc)}]

    lines = content.splitlines()

    # Regex for URL extraction (excludes trailing commas, quotes, brackets)
    url_regex = re.compile(r'https?://[^\s\'"<>,]+')

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # 1. URL Scanning
        urls = url_regex.findall(line)
        for url in urls:
            # Clean trailing punctuation and markdown delimiters
            clean_url = url.rstrip(".,;)\"'>]`")
            if not is_allowed_url(clean_url):
                findings.append({
                    "file": str(file_path),
                    "line": line_idx,
                    "type": "unauthorized_url",
                    "match": clean_url,
                })

        # 2. Forbidden host / cloud SDK keywords with word boundaries
        line_lower = stripped.lower()
        for host in FORBIDDEN_HOSTS:
            # Use regex word boundary for short identifiers like 'segment'
            host_pattern = re.compile(rf'\b{re.escape(host)}\b', re.IGNORECASE) if len(host) < 10 else re.compile(re.escape(host), re.IGNORECASE)
            if host_pattern.search(line_lower):
                findings.append({
                    "file": str(file_path),
                    "line": line_idx,
                    "type": "forbidden_host_or_sdk",
                    "match": host,
                })

        # 3. Forbidden technologies
        for tech in FORBIDDEN_TECHS:
            tech_pattern = re.compile(rf'\b{re.escape(tech)}\b', re.IGNORECASE)
            if tech_pattern.search(line_lower):
                findings.append({
                    "file": str(file_path),
                    "line": line_idx,
                    "type": "forbidden_technology",
                    "match": tech,
                })

    return findings


def run_egress_scan(base_dir: Path) -> Dict[str, Any]:
    """Execute complete egress scan across configured codebase folders."""
    all_findings: List[Dict[str, Any]] = []
    scanned_files_count = 0

    for dir_rel in DIRECTORIES_TO_SCAN:
        dir_path = base_dir / dir_rel
        if not dir_path.exists():
            continue

        for root, dirs, files in os.walk(dir_path):
            # Prune cache directories
            dirs[:] = [d for d in dirs if d not in {"__pycache__", ".pytest_cache", "node_modules", ".git"}]

            for f in files:
                if f in IGNORE_FILES:
                    continue
                file_path = Path(root) / f
                if file_path.suffix in IGNORE_EXTENSIONS:
                    continue

                scanned_files_count += 1
                findings = scan_file(file_path)
                all_findings.extend(findings)

    # Check built frontend bundle if exists
    dist_path = base_dir / "frontend" / "dist"
    if dist_path.exists():
        for root, _, files in os.walk(dist_path):
            for f in files:
                file_path = Path(root) / f
                if file_path.suffix in {".js", ".html", ".css"}:
                    scanned_files_count += 1
                    all_findings.extend(scan_file(file_path))

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scanned_files_count": scanned_files_count,
        "clean": len(all_findings) == 0,
        "findings_count": len(all_findings),
        "findings": all_findings,
    }

    # Write report to logs/egress_scan.json
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    report_path = logs_dir / "egress_scan.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    result = run_egress_scan(repo_root)

    print(f"--- Sovereign AI Workbench Egress Scan ---")
    print(f"Files Scanned: {result['scanned_files_count']}")
    print(f"Status:        {'CLEAN (PASS)' if result['clean'] else 'VIOLATIONS DETECTED (FAIL)'}")
    print(f"Findings:      {result['findings_count']}")

    if not result["clean"]:
        print("\nViolations details:")
        for idx, item in enumerate(result["findings"], 1):
            print(f"  {idx}. [{item['type']}] {item['file']}:{item['line']} -> {item['match']}")
        sys.exit(1)

    sys.exit(0)
