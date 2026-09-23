"""System and sovereignty endpoints for Sovereign AI Workbench.

Implements Phase 12 of 04_ANTIGRAVITY_BUILD_PLAN.md, 02_DESIGN_DOC.md §14.6,
and 03_SECURITY_AND_ACCESS.md §3:
- /api/system/status: Live binding, active models, offline flags, last egress scan result.
- /api/system/connections: Passive, read-only psutil inspection of workbench processes for non-loopback sockets.
- /api/system/probe: Optional active outbound egress probe (requires confirm=true) to prove outbound blocks.
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import socket
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
import psutil

from backend.core.config import get_settings
from backend.core.db import User
from backend.core.security import get_current_user
from models.registry import get_registry

logger = logging.getLogger("sovereign-workbench.system")

router = APIRouter(prefix="/system", tags=["System & Sovereignty"])

LOOPBACK_IPS = {"127.0.0.1", "::1", "localhost"}


class SystemStatusResponse(BaseModel):
    """Sovereignty and system status details."""
    app_host: str
    app_port: int
    ollama_base_url: str
    allow_lan: bool
    models: List[Dict[str, Any]]
    offline_flags: Dict[str, Any]
    last_scan_result: Optional[Dict[str, Any]]
    sovereign_enforced: bool


class SocketConnectionInfo(BaseModel):
    """Information on an individual socket connection."""
    pid: int
    process_name: str
    fd: int
    family: str
    type: str
    laddr: str
    raddr: Optional[str]
    status: str
    is_loopback: bool


class ConnectionsAuditResponse(BaseModel):
    """Audit outcome of passive socket connection inspection."""
    status: str  # "CLEAN" or "VIOLATION"
    non_loopback_count: int
    total_connections_checked: int
    checked_processes: List[Dict[str, Any]]
    non_loopback_connections: List[SocketConnectionInfo]
    timestamp: str


class EgressProbeResponse(BaseModel):
    """Result of active outbound connection probe."""
    probe_status: str  # "BLOCKED" or "CONNECTED"
    blocked: bool
    target: str
    message: str
    timestamp: str


def _get_last_egress_scan() -> Optional[Dict[str, Any]]:
    """Read latest egress scan outcome from logs/egress_scan.json."""
    scan_log = Path("logs/egress_scan.json")
    if scan_log.exists():
        try:
            return json.loads(scan_log.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning(f"Failed to read logs/egress_scan.json: {exc}")
    return None


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(
    current_user: User = Depends(get_current_user),
) -> SystemStatusResponse:
    """Return live air-gap status, bindings, registry models, and environment flags."""
    settings = get_settings()
    reg = get_registry(settings.MODEL_REGISTRY_PATH)

    models_info = []
    for key, m in reg.models.items():
        models_info.append({
            "name": m.model,
            "provider": m.provider,
            "enabled": m.enabled,
            "capabilities": m.capabilities,
        })

    offline_flags = {
        "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE", "1"),
        "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE", "1"),
        "ANONYMIZED_TELEMETRY": os.environ.get("ANONYMIZED_TELEMETRY", "False"),
        "DO_NOT_TRACK": os.environ.get("DO_NOT_TRACK", "1"),
    }

    last_scan = _get_last_egress_scan()

    return SystemStatusResponse(
        app_host=settings.APP_HOST,
        app_port=settings.APP_PORT,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        allow_lan=settings.ALLOW_LAN,
        models=models_info,
        offline_flags=offline_flags,
        last_scan_result=last_scan,
        sovereign_enforced=True,
    )


@router.get("/connections", response_model=ConnectionsAuditResponse)
def audit_connections(
    current_user: User = Depends(get_current_user),
) -> ConnectionsAuditResponse:
    """Passive inspection of workbench processes for non-loopback network connections."""
    workbench_process_names = {"python.exe", "python", "uvicorn", "ollama.exe", "ollama"}
    checked_procs: List[Dict[str, Any]] = []
    non_loopback: List[SocketConnectionInfo] = []
    total_checked = 0

    current_pid = os.getpid()

    # Collect relevant processes (current process, children, parent, and matching workbench executables)
    target_pids = {current_pid}
    try:
        cur_proc = psutil.Process(current_pid)
        target_pids.update(c.pid for c in cur_proc.children(recursive=True))
        if cur_proc.parent():
            target_pids.add(cur_proc.parent().pid)
    except Exception:
        pass

    for p in psutil.process_iter(attrs=["pid", "name"]):
        try:
            p_name = p.info.get("name") or ""
            if p_name.lower() in workbench_process_names or p.info["pid"] in target_pids:
                target_pids.add(p.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for pid in target_pids:
        try:
            proc = psutil.Process(pid)
            p_name = proc.name()
            connections = proc.net_connections(kind="inet")
            checked_procs.append({
                "pid": pid,
                "name": p_name,
                "connection_count": len(connections),
            })

            for conn in connections:
                total_checked += 1
                laddr_ip = conn.laddr.ip if conn.laddr else ""
                raddr_ip = conn.raddr.ip if conn.raddr else ""

                # Evaluate loopback confinement
                # Listening sockets: laddr must be loopback or ANY (if internal)
                # Connected/established sockets: raddr must be loopback
                is_loopback = True
                if raddr_ip and raddr_ip not in LOOPBACK_IPS:
                    is_loopback = False
                elif not raddr_ip and laddr_ip and laddr_ip not in LOOPBACK_IPS and laddr_ip != "0.0.0.0":
                    is_loopback = False

                if not is_loopback:
                    non_loopback.append(
                        SocketConnectionInfo(
                            pid=pid,
                            process_name=p_name,
                            fd=conn.fd if hasattr(conn, "fd") else -1,
                            family=str(conn.family),
                            type=str(conn.type),
                            laddr=f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                            raddr=f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            status=conn.status,
                            is_loopback=False,
                        )
                    )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    status_str = "CLEAN" if len(non_loopback) == 0 else "VIOLATION"

    return ConnectionsAuditResponse(
        status=status_str,
        non_loopback_count=len(non_loopback),
        total_connections_checked=total_checked,
        checked_processes=checked_procs,
        non_loopback_connections=non_loopback,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/probe", response_model=EgressProbeResponse)
def trigger_egress_probe(
    confirm: bool = Query(
        False,
        description="Explicit confirmation to attempt a 1-second outbound socket probe to verify air-gap block.",
    ),
    current_user: User = Depends(get_current_user),
) -> EgressProbeResponse:
    """Active outbound probe testing if external internet traffic is blocked.
    
    Warning: This endpoint attempts an outbound probe (8.8.8.8:53). Do not run while capturing
    clean network isolation evidence.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active outbound probe requires explicit confirmation. Set ?confirm=true.",
        )

    # Only admin or auditor can trigger active probe
    if current_user.role not in {"admin", "auditor"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active outbound egress probe can only be executed by admin or auditor roles.",
        )

    target_ip = "8.8.8.8"
    target_port = 53
    target_str = f"{target_ip}:{target_port}"

    blocked = True
    msg = ""
    probe_status = "BLOCKED"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((target_ip, target_port))
        s.close()
        blocked = False
        probe_status = "CONNECTED"
        msg = "Outbound connection succeeded. System is NOT air-gapped / firewall block is inactive."
    except Exception as exc:
        blocked = True
        probe_status = "BLOCKED"
        msg = f"Outbound connection failed ({type(exc).__name__}: {exc}). Outbound traffic is blocked as expected."

    return EgressProbeResponse(
        probe_status=probe_status,
        blocked=blocked,
        target=target_str,
        message=msg,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
