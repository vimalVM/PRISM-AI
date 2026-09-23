"""Tests for path safety, directory traversal prevention, and allowlists (SEC-06)."""

from pathlib import Path
import pytest

from backend.core.paths import AccessDenied, PathTraversalError, safe_path


@pytest.fixture
def allowed_roots(tmp_path):
    """Create isolated temporary allowed directories."""
    incoming = tmp_path / "incoming"
    kb = tmp_path / "knowledge_base"
    outputs = tmp_path / "outputs"
    incoming.mkdir()
    kb.mkdir()
    outputs.mkdir()
    return [incoming, kb, outputs]


def test_safe_path_valid_paths(allowed_roots):
    """Valid paths within allowlists resolve without error."""
    incoming, kb, outputs = allowed_roots

    valid_file = incoming / "test_document.pdf"
    valid_file.write_text("dummy")

    resolved = safe_path(valid_file, allowed_roots=allowed_roots)
    assert resolved == valid_file.resolve()

    # Relative paths within an allowed root
    sub_dir = kb / "manuals" / "v1"
    sub_dir.mkdir(parents=True)
    sub_file = sub_dir / "pump_spec.docx"
    sub_file.write_text("dummy")

    resolved_sub = safe_path(sub_file, allowed_roots=allowed_roots)
    assert resolved_sub == sub_file.resolve()


def test_safe_path_reject_traversal(allowed_roots):
    """SEC-06: Path traversal attempts must be rejected."""
    incoming, _, _ = allowed_roots

    # Simple ../ traversal
    traversal_path = str(incoming) + "/../../etc/passwd"
    with pytest.raises((PathTraversalError, AccessDenied)):
        safe_path(traversal_path, allowed_roots=allowed_roots)

    # Windows style ..\\ traversal
    win_traversal = str(incoming) + r"\..\..\Windows\win.ini"
    with pytest.raises((PathTraversalError, AccessDenied)):
        safe_path(win_traversal, allowed_roots=allowed_roots)


def test_safe_path_reject_outside_allowlist(allowed_roots, tmp_path):
    """Paths outside allowlists must be rejected even if they don't use '..'."""
    outside_dir = tmp_path / "other_secret_folder"
    outside_dir.mkdir()
    outside_file = outside_dir / "secret.txt"
    outside_file.write_text("secret")

    with pytest.raises(PathTraversalError):
        safe_path(outside_file, allowed_roots=allowed_roots)


def test_safe_path_reject_null_bytes(allowed_roots):
    """Null bytes in paths must be rejected immediately."""
    incoming, _, _ = allowed_roots
    poisoned_path = f"{incoming}/report.pdf\0.exe"

    with pytest.raises(PathTraversalError) as exc_info:
        safe_path(poisoned_path, allowed_roots=allowed_roots)
    assert "Null bytes" in str(exc_info.value)


def test_safe_path_reject_unc_paths(allowed_roots):
    """UNC network paths must be rejected to maintain air-gap boundary."""
    unc_paths = [
        r"\\192.168.1.50\share\data.txt",
        r"\\remote-server\c$\windows\system32",
        "//nas.local/public/file.docx",
    ]
    for unc in unc_paths:
        with pytest.raises(PathTraversalError) as exc_info:
            safe_path(unc, allowed_roots=allowed_roots)
        assert "UNC" in str(exc_info.value) or "air-gap" in str(exc_info.value)


@pytest.mark.parametrize("reserved_name", ["CON", "PRN", "AUX", "NUL", "COM1", "COM9", "LPT1", "LPT9", "nul.txt", "aux.dat"])
def test_safe_path_reject_windows_reserved_device_names(allowed_roots, reserved_name):
    """Windows reserved device names must be rejected to prevent OS hangs or device access."""
    incoming, _, _ = allowed_roots
    reserved_path = incoming / reserved_name

    with pytest.raises(PathTraversalError) as exc_info:
        safe_path(reserved_path, allowed_roots=allowed_roots)
    assert "reserved" in str(exc_info.value).lower()


def test_safe_path_must_exist_flag(allowed_roots):
    """When must_exist=True, missing files must raise AccessDenied."""
    incoming, _, _ = allowed_roots
    missing_file = incoming / "non_existent.pdf"

    with pytest.raises(AccessDenied) as exc_info:
        safe_path(missing_file, allowed_roots=allowed_roots, must_exist=True)
    assert "does not exist" in str(exc_info.value)
