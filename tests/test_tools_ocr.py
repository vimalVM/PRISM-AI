"""Unit and integration tests for OCR and document image extraction tools.

Tests:
- Native text PDF: verifies native text is directly extracted with is_scanned=False and confidence=1.0.
- Scanned PDF (demo inspection report): verifies OCR engine runs, identifies page 1 as scanned, returns text with correct page refs and confidence.
- Embedded raster image extraction: verifies page_2_image_1.png is extracted and saved to disk.
- Direct image file OCR: verifies direct image files are handled gracefully as 1-page documents.
- Result caching: verifies second invocation with same SHA-256 returns cached=True without re-running.
- Path confinement: verifies path traversal and unallowed paths are strictly blocked.
"""

from pathlib import Path
import pytest
import fitz
from PIL import Image

from backend.core.config import get_settings
from backend.core.paths import AccessDenied, PathTraversalError
from tools.ocr import OCRDocumentArgs, ocr_document
from tools.registry import ToolContext


@pytest.fixture
def engineer_ctx():
    return ToolContext(
        user_id="user_eng_ocr",
        role="engineer",
        clearance=2,
        run_id="run_ocr_test_001",
    )


@pytest.fixture
def native_pdf(tmp_path, monkeypatch):
    """Create a temporary native text PDF."""
    incoming_dir = tmp_path / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(get_settings(), "ALLOWED_INPUT_DIRS", str(incoming_dir))

    pdf_file = incoming_dir / "sample_native.pdf"
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "CONFIDENTIAL ENGINEERING SPECIFICATION FOR HEAT EXCHANGER HX-101.\n"
        "Operating temperature range is 120 C to 240 C under nominal flow conditions.\n"
        "All tubes must be hydrostatically tested at 1.5 times working pressure."
    )
    page.insert_text((50, 72), text)
    doc.save(str(pdf_file))
    doc.close()

    return pdf_file


def test_ocr_native_text_pdf(native_pdf, engineer_ctx):
    """Native text PDF should bypass OCR and return exact text with confidence 1.0."""
    args = OCRDocumentArgs(file_path=str(native_pdf), min_chars_threshold=50)
    result = ocr_document(args, engineer_ctx)

    assert result.total_pages == 1
    assert len(result.processed_pages) == 1
    p1 = result.processed_pages[0]
    assert p1.page == 1
    assert p1.is_scanned is False
    assert p1.engine == "native"
    assert p1.confidence == 1.0
    assert "HEAT EXCHANGER HX-101" in p1.text
    assert "hydrostatically tested" in p1.text


def test_ocr_scanned_pdf_and_image_extraction(engineer_ctx):
    """Scanned PDF demo report triggers OCR on Page 1 and extracts embedded photo on Page 2."""
    demo_pdf = Path("data/incoming/demo_scanned_inspection_report.pdf")
    assert demo_pdf.exists(), "demo_scanned_inspection_report.pdf must be generated first"

    args = OCRDocumentArgs(
        file_path=str(demo_pdf),
        min_chars_threshold=50,
        dpi=150,
        extract_images=True,
    )
    result = ocr_document(args, engineer_ctx)

    assert result.total_pages == 2
    assert len(result.processed_pages) == 2

    # Page 1: Scanned image with typed report text
    p1 = result.processed_pages[0]
    assert p1.page == 1
    assert p1.is_scanned is True
    assert p1.engine in {"paddleocr", "tesseract"}
    assert p1.confidence > 0.0
    # Check that key inspection phrases were recognized by OCR
    upper_p1 = p1.text.upper()
    assert any(term in upper_p1 for term in ["ULTRASONIC", "PV-402", "INSPECTION", "WELD", "SOP-301", "THICKNESS"])

    # Page 2: Visual Evidence with embedded photo
    p2 = result.processed_pages[1]
    assert p2.page == 2
    assert len(p2.extracted_images) >= 1
    img_path = Path(p2.extracted_images[0])
    assert img_path.exists()
    assert "page_2_image_" in img_path.name

    # Validate the extracted image can be opened
    with Image.open(img_path) as im:
        assert im.width >= 32
        assert im.height >= 32


def test_ocr_direct_image_file(engineer_ctx):
    """Direct image file is processed as a single-page document with OCR."""
    photo_path = Path("data/incoming/demo_inspection_photo.png")
    assert photo_path.exists()

    args = OCRDocumentArgs(file_path=str(photo_path))
    result = ocr_document(args, engineer_ctx)

    assert result.total_pages == 1
    p1 = result.processed_pages[0]
    assert p1.page == 1
    assert p1.is_scanned is True
    upper_text = p1.text.upper()
    assert "WELD" in upper_text or "CW-3" in upper_text or "PIT" in upper_text


def test_ocr_result_caching(native_pdf, engineer_ctx):
    """Subsequent call with identical arguments returns cached result."""
    args = OCRDocumentArgs(file_path=str(native_pdf))
    res1 = ocr_document(args, engineer_ctx)
    assert res1.cached is False

    res2 = ocr_document(args, engineer_ctx)
    assert res2.cached is True
    assert res2.sha256 == res1.sha256


def test_ocr_rejects_path_traversal(engineer_ctx):
    """Path traversal outside allowed roots is blocked."""
    args = OCRDocumentArgs(file_path="../../outside.pdf")
    with pytest.raises((AccessDenied, PathTraversalError)):
        ocr_document(args, engineer_ctx)
