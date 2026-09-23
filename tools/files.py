"""File interaction tools for Sovereign AI Workbench.

Implements SEC-06 and 02_DESIGN_DOC.md section 7.3:
- read_file: strict allowlist confinement via safe_path (incoming, knowledge_base, outputs).
- write_file: restricted to outputs/<run_id>/ directory; prevents overwrite unless explicit.
- Both tools decorated with @audited_tool (omitting document content from audit logs).
"""

import hashlib
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from backend.core.config import get_settings
from backend.core.paths import AccessDenied, safe_path
from tools.registry import ToolContext, audited_tool


class ReadFileArgs(BaseModel):
    """Input parameters for read_file tool."""

    path: str = Field(..., description="Local file path within allowed storage directories.")
    max_bytes: int = Field(default=1_000_000, description="Maximum bytes to read (default 1MB).")


class ReadFileResult(BaseModel):
    """Result returned by read_file tool."""

    path: str
    size_bytes: int
    content: str
    sha256: str


class WriteFileArgs(BaseModel):
    """Input parameters for write_file tool."""

    filename: str = Field(..., description="Name of the file to write inside run output folder.")
    content: str = Field(..., description="Text content to write to file.")
    allow_overwrite: bool = Field(default=False, description="Whether to allow overwriting an existing file.")


class WriteFileResult(BaseModel):
    """Result returned by write_file tool."""

    path: str
    filename: str
    size_bytes: int
    sha256: str


@audited_tool(
    name="read_file",
    side_effects=False,
    needs_role=None,
    description="Read text contents from an authorized file on local disk.",
)
def read_file(args: ReadFileArgs, ctx: ToolContext) -> ReadFileResult:
    """Read a file safely within allowlisted incoming, knowledge_base, or outputs directories."""
    settings = get_settings()
    allowed_roots = settings.input_dirs + settings.output_dirs

    # Enforce path safety and existence
    resolved_path = safe_path(args.path, allowed_roots=allowed_roots, must_exist=True)

    if resolved_path.is_dir():
        raise AccessDenied(f"Path '{resolved_path}' is a directory, not a file.")

    stat = resolved_path.stat()
    if stat.st_size > args.max_bytes:
        raise ValueError(
            f"File size {stat.st_size} bytes exceeds permitted read limit of {args.max_bytes} bytes."
        )

    content_bytes = resolved_path.read_bytes()
    sha256 = hashlib.sha256(content_bytes).hexdigest()

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = content_bytes.decode("latin-1", errors="replace")

    return ReadFileResult(
        path=str(resolved_path),
        size_bytes=len(content_bytes),
        content=content,
        sha256=sha256,
    )


@audited_tool(
    name="write_file",
    side_effects=True,
    needs_role=None,
    description="Write text contents to a file in the task's output directory.",
)
def write_file(args: WriteFileArgs, ctx: ToolContext) -> WriteFileResult:
    """Write content to a file confined to data/outputs/<run_id>/."""
    settings = get_settings()
    output_roots = settings.output_dirs

    # Sanitize run_id component to prevent path traversal via run_id
    safe_run_id = os.path.basename(ctx.run_id or "adhoc")
    safe_filename = os.path.basename(args.filename)
    if not safe_filename or safe_filename != args.filename.replace("/", "").replace("\\", ""):
        raise AccessDenied(f"Invalid or traversing filename: '{args.filename}'")

    # Target directory under primary outputs folder
    primary_output = output_roots[0]
    run_output_dir = primary_output / safe_run_id
    run_output_dir.mkdir(parents=True, exist_ok=True)

    target_path = run_output_dir / safe_filename

    # Validate destination against output roots
    resolved_path = safe_path(target_path, allowed_roots=output_roots, must_exist=False)

    if resolved_path.exists() and not args.allow_overwrite:
        raise FileExistsError(
            f"File '{resolved_path}' already exists and allow_overwrite is False."
        )

    content_bytes = args.content.encode("utf-8")
    resolved_path.write_bytes(content_bytes)

    sha256 = hashlib.sha256(content_bytes).hexdigest()

    return WriteFileResult(
        path=str(resolved_path),
        filename=safe_filename,
        size_bytes=len(content_bytes),
        sha256=sha256,
    )
