"""File upload and metadata management endpoints for Sovereign AI Workbench.

Implements SEC-07 and 03_SECURITY_AND_ACCESS.md §7.2:
- Strict extension allowlist and denylist enforcement.
- Magic-byte verification via filetype library (rejects renamed executables, archives).
- Decompression bomb mitigation via PIL.Image.MAX_IMAGE_PIXELS.
- Maximum PDF page count and total file size limits.
- Safe random UUID storage in data/incoming/ with path confinement.
- SHA-256 fingerprinting and SQLite FileRecord persistence.
- Cryptographic hash-chained audit logging without file content leakage.
"""

from datetime import datetime, timezone
import hashlib
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import filetype
import fitz  # PyMuPDF
from PIL import Image
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.audit import log_event
from backend.core.config import get_settings
from backend.core.db import FileRecord, User, get_db
from backend.core.paths import AccessDenied, safe_path
from backend.core.rbac import Role, require_role
from backend.core.security import get_current_user

logger = logging.getLogger("sovereign-workbench.files")

router = APIRouter(prefix="/files", tags=["Files"])

# Strictly allowed extensions (lowercase)
ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp",
    ".docx", ".xlsx", ".pptx", ".txt", ".csv", ".md", ".py",
}

# Forbidden extensions (executables, archives, macro-enabled documents)
FORBIDDEN_EXTENSIONS = {
    ".exe", ".dll", ".so", ".bin", ".bat", ".cmd", ".sh", ".ps1", ".elf",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".docm", ".xlsm", ".pptm", ".dotm", ".xltm", ".potm",
}

# Magic byte signatures to detect binary executables regardless of extension
EXECUTABLE_MAGIC_PREFIXES = [
    b"MZ",            # DOS / Windows PE Executable
    b"\x7fELF",       # Linux / Unix ELF Executable
    b"\xca\xfe\xba\xbe", # Java Class / Mach-O Fat Binary
    b"\xfe\xed\xfa\xce", # Mach-O 32-bit
    b"\xfe\xed\xfa\xcf", # Mach-O 64-bit
]

# Max image pixels limit to prevent decompression bombs (50 megapixels)
Image.MAX_IMAGE_PIXELS = 50_000_000


class FileRecordResponse(BaseModel):
    """File metadata response model."""
    id: str
    owner_id: str
    original_name: str
    stored_path: str
    sha256: str
    mime: str
    modality: str
    pages: Optional[int] = None
    size_bytes: int
    created_at: datetime


def _detect_modality(ext: str, mime: str) -> str:
    """Classify file modality."""
    if ext == ".pdf":
        return "pdf"
    if ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        return "image"
    if ext in {".docx", ".xlsx", ".pptx"}:
        return "office"
    if ext in {".py", ".sh"}:
        return "code"
    return "text"


def _validate_content(content: bytes, ext: str, original_filename: str) -> Tuple[str, Optional[int]]:
    """Validate magic bytes, executable detection, image bomb limits, and PDF pages.

    Returns:
        Tuple of (detected_mime, page_count)
    """
    settings = get_settings()

    # 1. Direct executable magic bytes check
    for prefix in EXECUTABLE_MAGIC_PREFIXES:
        if content.startswith(prefix):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security violation (SEC-07): File '{original_filename}' contains executable machine code headers and is strictly forbidden.",
            )

    # 2. Filetype inspection
    kind = filetype.guess(content[:4096])
    detected_mime = kind.mime if kind else "application/octet-stream"

    # Reject if filetype library identifies executable or archive
    if kind is not None:
        if "executable" in kind.mime or "x-msdownload" in kind.mime or "x-elf" in kind.mime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security violation (SEC-07): Executable payload detected in file '{original_filename}'.",
            )
        if kind.mime in {"application/zip", "application/x-tar", "application/x-7z-compressed", "application/x-rar"}:
            if ext not in {".docx", ".xlsx", ".pptx"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Security violation: Archive payload ({kind.mime}) is not permitted.",
                )

    # 3. Format-specific verification
    page_count: Optional[int] = None

    if ext == ".pdf":
        # PDF must start with %PDF
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security violation (SEC-07): File '{original_filename}' has .pdf extension but lacks valid PDF magic header.",
            )
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            page_count = len(doc)
            doc.close()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or corrupted PDF file: {exc}",
            )
        if page_count > settings.MAX_PDF_PAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF page limit exceeded: Document contains {page_count} pages (maximum allowed is {settings.MAX_PDF_PAGES}).",
            )
        detected_mime = "application/pdf"

    elif ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
            if width * height > Image.MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Decompression bomb detected: Image resolution exceeds safety limit (50 megapixels).",
                )
            img.verify()
        except Image.DecompressionBombError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security violation (SEC-07): Image triggers PIL decompression bomb threshold.",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or corrupted image format: {exc}",
            )
        detected_mime = f"image/{ext.lstrip('.')}"
        page_count = 1

    elif ext in {".txt", ".csv", ".md", ".py"}:
        # Check text encoding and ensure no null bytes or binary gibberish
        if b"\x00" in content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security violation: Text file '{original_filename}' contains forbidden null bytes.",
            )
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Text file '{original_filename}' is not valid UTF-8 text.",
            )
        detected_mime = "text/plain"
        page_count = 1

    elif ext in {".docx", ".xlsx", ".pptx"}:
        # Must be valid zip-based OpenXML container without macros
        if not content.startswith(b"PK"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{original_filename}' lacks valid Office OpenXML container signature.",
            )
        detected_mime = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if ext == ".docx" else
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if ext == ".xlsx" else
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

    return detected_mime, page_count


@router.post("/upload", response_model=FileRecordResponse)
async def upload_file(
    file: UploadFile = File(...),
    classification: int = Form(default=2),  # Default 2 (CONFIDENTIAL)
    user: User = Depends(require_role(Role.ADMIN, Role.ENGINEER, Role.REVIEWER)),
    db: Session = Depends(get_db),
) -> FileRecordResponse:
    """Secure file upload endpoint enforcing SEC-07 validation rules."""
    settings = get_settings()
    filename = file.filename or "unnamed_upload"
    ext = Path(filename).suffix.lower()

    # 1. Extension validation
    if ext in FORBIDDEN_EXTENSIONS:
        log_event(
            event_type="file_upload_blocked",
            status="denied",
            user_id=user.id,
            role=user.role,
            details={"filename": filename, "reason": "forbidden_extension", "extension": ext},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension '{ext}' is forbidden by security policy.",
        )

    if ext not in ALLOWED_EXTENSIONS:
        log_event(
            event_type="file_upload_blocked",
            status="denied",
            user_id=user.id,
            role=user.role,
            details={"filename": filename, "reason": "extension_not_allowed", "extension": ext},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension '{ext}' is not in the permitted allowlist.",
        )

    # 2. Size limit check during stream read
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read()
    file_size = len(content)

    if file_size > max_bytes:
        log_event(
            event_type="file_upload_blocked",
            status="denied",
            user_id=user.id,
            role=user.role,
            details={"filename": filename, "reason": "oversize", "size_bytes": file_size, "limit_bytes": max_bytes},
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload limit of {settings.MAX_UPLOAD_MB} MB (received {round(file_size / (1024 * 1024), 2)} MB).",
        )

    # 3. Magic-byte, executable, and decompression bomb validation
    try:
        detected_mime, page_count = _validate_content(content, ext, filename)
    except HTTPException as he:
        log_event(
            event_type="file_upload_blocked",
            status="denied",
            user_id=user.id,
            role=user.role,
            details={"filename": filename, "reason": "content_validation_failed", "detail": he.detail},
        )
        raise he

    # 4. Generate random UUID and target path
    file_id = str(uuid.uuid4())
    incoming_dir = Path("data/incoming")
    incoming_dir.mkdir(parents=True, exist_ok=True)
    target_path = incoming_dir / f"{file_id}{ext}"

    # Verify destination with safe_path
    resolved_target = safe_path(target_path, allowed_roots=[incoming_dir])

    # 5. Compute SHA-256 fingerprint
    sha256 = hashlib.sha256(content).hexdigest()

    # 6. Save file to disk
    resolved_target.write_bytes(content)

    # 7. Record in SQLite DB
    modality = _detect_modality(ext, detected_mime)
    record = FileRecord(
        id=file_id,
        owner_id=user.id,
        original_name=filename,
        stored_path=str(resolved_target),
        sha256=sha256,
        mime=detected_mime,
        modality=modality,
        pages=page_count,
        size_bytes=file_size,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 8. Cryptographic audit log (zero document content)
    log_event(
        event_type="file_uploaded",
        status="success",
        user_id=user.id,
        role=user.role,
        details={
            "file_id": file_id,
            "sha256": sha256,
            "mime": detected_mime,
            "modality": modality,
            "pages": page_count,
            "size_bytes": file_size,
        },
    )

    return FileRecordResponse(
        id=record.id,
        owner_id=record.owner_id,
        original_name=record.original_name,
        stored_path=record.stored_path,
        sha256=record.sha256,
        mime=record.mime,
        modality=record.modality,
        pages=record.pages,
        size_bytes=record.size_bytes,
        created_at=record.created_at,
    )


@router.get("", response_model=List[FileRecordResponse])
def list_files(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[FileRecordResponse]:
    """List uploaded files accessible to current user (own files, or all files for admin)."""
    if user.role == Role.ADMIN:
        stmt = select(FileRecord).order_by(FileRecord.created_at.desc())
    else:
        stmt = select(FileRecord).where(FileRecord.owner_id == user.id).order_by(FileRecord.created_at.desc())

    records = db.scalars(stmt).all()
    return [
        FileRecordResponse(
            id=r.id,
            owner_id=r.owner_id,
            original_name=r.original_name,
            stored_path=r.stored_path,
            sha256=r.sha256,
            mime=r.mime,
            modality=r.modality,
            pages=r.pages,
            size_bytes=r.size_bytes,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/{file_id}", response_model=FileRecordResponse)
def get_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileRecordResponse:
    """Retrieve metadata for a specific uploaded file."""
    record = db.scalar(select(FileRecord).where(FileRecord.id == file_id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if user.role != Role.ADMIN and record.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to requested file")

    return FileRecordResponse(
        id=record.id,
        owner_id=record.owner_id,
        original_name=record.original_name,
        stored_path=record.stored_path,
        sha256=record.sha256,
        mime=record.mime,
        modality=record.modality,
        pages=record.pages,
        size_bytes=record.size_bytes,
        created_at=record.created_at,
    )
