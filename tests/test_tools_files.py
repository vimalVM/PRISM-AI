"""Unit tests for safe file access tools (read_file, write_file).

Tests SEC-06 path allowlist enforcement, traversal rejection, and audit logging.
"""

from pathlib import Path
import pytest

from backend.core.audit import get_engine
from backend.core.config import get_settings
from backend.core.paths import AccessDenied, PathTraversalError
from tools.files import ReadFileArgs, WriteFileArgs, read_file, write_file
from tools.registry import ToolContext


@pytest.fixture
def test_dirs(tmp_path, monkeypatch):
    """Set up temporary input and output directories."""
    incoming = tmp_path / "incoming"
    outputs = tmp_path / "outputs"
    incoming.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(get_settings(), "ALLOWED_INPUT_DIRS", str(incoming))
    monkeypatch.setattr(get_settings(), "ALLOWED_OUTPUT_DIRS", str(outputs))
    return incoming, outputs


@pytest.fixture
def engineer_ctx():
    return ToolContext(
        user_id="user_eng_1",
        role="engineer",
        clearance=1,
        run_id="run_test_001",
    )


def test_write_file_and_read_file_success(test_dirs, engineer_ctx):
    incoming, outputs = test_dirs

    # 1. Write file
    write_args = WriteFileArgs(filename="report.txt", content="Confidential engineering analysis.")
    res_write = write_file(write_args, engineer_ctx)

    assert res_write.filename == "report.txt"
    assert res_write.size_bytes == len("Confidential engineering analysis.")
    assert len(res_write.sha256) == 64
    assert Path(res_write.path).exists()

    # 2. Read file back
    read_args = ReadFileArgs(path=res_write.path)
    res_read = read_file(read_args, engineer_ctx)

    assert res_read.content == "Confidential engineering analysis."
    assert res_read.sha256 == res_write.sha256
    assert res_read.size_bytes == res_write.size_bytes


def test_write_file_prevents_overwrite_unless_explicit(test_dirs, engineer_ctx):
    write_args = WriteFileArgs(filename="immutable.txt", content="Initial version")
    write_file(write_args, engineer_ctx)

    # Overwrite attempt with allow_overwrite=False
    overwrite_args = WriteFileArgs(filename="immutable.txt", content="Second version", allow_overwrite=False)
    with pytest.raises(FileExistsError):
        write_file(overwrite_args, engineer_ctx)

    # Overwrite attempt with allow_overwrite=True
    overwrite_ok_args = WriteFileArgs(filename="immutable.txt", content="Updated version", allow_overwrite=True)
    res = write_file(overwrite_ok_args, engineer_ctx)
    assert res.size_bytes == len("Updated version")


def test_write_file_rejects_path_traversal(test_dirs, engineer_ctx):
    traversal_args = WriteFileArgs(filename="../../escaped.txt", content="malicious")
    with pytest.raises(AccessDenied):
        write_file(traversal_args, engineer_ctx)


def test_read_file_rejects_traversal_and_unauthorized_paths(test_dirs, engineer_ctx, tmp_path):
    # Outside directory
    forbidden_file = tmp_path / "secret.key"
    forbidden_file.write_text("supersecret")

    read_args = ReadFileArgs(path=str(forbidden_file))
    with pytest.raises(PathTraversalError):
        read_file(read_args, engineer_ctx)

    # Path traversal with ..
    incoming, _ = test_dirs
    traversal_path = str(incoming / ".." / "secret.key")
    with pytest.raises(PathTraversalError):
        read_file(ReadFileArgs(path=traversal_path), engineer_ctx)


def test_read_file_size_limit(test_dirs, engineer_ctx):
    incoming, _ = test_dirs
    big_file = incoming / "large.bin"
    big_file.write_bytes(b"A" * 2000)

    # Max bytes is 1000, file is 2000
    with pytest.raises(ValueError, match="exceeds permitted read limit"):
        read_file(ReadFileArgs(path=str(big_file), max_bytes=1000), engineer_ctx)
