"""Path validation and safety controls for Sovereign AI Workbench.

Enforces SEC-06 (path traversal rejection, allowlist enforcement, UNC blocking,
null-byte rejection, Windows reserved device names).
"""

import os
from pathlib import Path
import re
from typing import List, Optional

from backend.core.config import get_settings


WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


class AccessDenied(Exception):
    """Raised when a file path or access request violates security policy."""
    pass


class PathTraversalError(AccessDenied):
    """Raised specifically when a path attempts directory traversal or escapes allowlist."""
    pass


def is_windows_reserved_name(name: str) -> bool:
    """Check if a filename or path component matches Windows reserved device names."""
    stem = Path(name).stem.upper()
    return stem in WINDOWS_RESERVED_NAMES or name.upper() in WINDOWS_RESERVED_NAMES


def safe_path(
    p: str | Path,
    allowed_roots: Optional[List[Path]] = None,
    must_exist: bool = False,
) -> Path:
    """Validate and resolve a path against strict air-gap allowlists.

    Args:
        p: Input path as string or Path object.
        allowed_roots: List of allowed root directory Paths. If None, uses
            Settings.input_dirs + Settings.output_dirs.
        must_exist: If True, candidate must already exist on disk.

    Returns:
        Resolved canonical Path within one of the allowed roots.

    Raises:
        PathTraversalError / AccessDenied: If path violates any safety constraint.
    """
    p_str = str(p)

    # 1. Null-byte rejection
    if "\0" in p_str:
        raise PathTraversalError("Null bytes are forbidden in file paths")

    # 2. UNC path rejection (e.g. \\server\share or //server/share)
    stripped = p_str.strip()
    if stripped.startswith(r"\\") or stripped.startswith("//") or stripped.startswith(r"\/\/"):
        raise PathTraversalError("UNC network paths are forbidden by air-gap policy")

    # 3. Traversal string patterns check before resolution
    # Check for raw .. segments in posix or windows style
    parts = re.split(r"[\\/]", p_str)
    for part in parts:
        if is_windows_reserved_name(part):
            raise PathTraversalError(f"Windows reserved device name forbidden: '{part}'")

    raw_path = Path(p_str)

    # 4. Resolve candidate path to canonical form (normalises . and .., resolves symlinks)
    try:
        candidate = raw_path.expanduser().resolve()
    except Exception as exc:
        raise PathTraversalError(f"Failed to resolve path '{p_str}': {exc}") from exc

    # Check components of resolved path for reserved names
    for part in candidate.parts:
        # On Windows, drive letters like 'C:\' have stem 'C:' which is fine, check stem of parts
        if is_windows_reserved_name(part):
            raise PathTraversalError(f"Windows reserved device name forbidden: '{part}'")

    # 5. Resolve allowed roots
    if allowed_roots is None:
        settings = get_settings()
        allowed_roots = settings.input_dirs + settings.output_dirs

    resolved_roots = [r.expanduser().resolve() for r in allowed_roots]

    # 6. Check that candidate is within at least one allowed root
    is_allowed = False
    for root in resolved_roots:
        try:
            if candidate.is_relative_to(root):
                is_allowed = True
                break
        except AttributeError:
            # Fallback for older python if needed, though 3.9+ has is_relative_to
            try:
                candidate.relative_to(root)
                is_allowed = True
                break
            except ValueError:
                continue

    if not is_allowed:
        raise PathTraversalError(
            f"Path '{p_str}' resolves to '{candidate}', which is outside allowed directories: "
            f"{[str(r) for r in resolved_roots]}"
        )

    # 7. Existence check if requested
    if must_exist and not candidate.exists():
        raise AccessDenied(f"Path does not exist: '{candidate}'")

    return candidate
