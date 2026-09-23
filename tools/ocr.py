"""OCR and document image extraction tools for Sovereign AI Workbench.

Implements 02_DESIGN_DOC.md §7.3 and 04_ANTIGRAVITY_BUILD_PLAN.md Phase 5:
- PyMuPDF native text extraction with scanned-page threshold detection.
- High-fidelity page rendering (200-300 DPI) for scanned document pages.
- Offline OCR engine: PaddleOCR on CPU with automated Tesseract fallback.
- Structured page results with page references, confidence scores, and line breakdown.
- Raster embedded-image extraction (for downstream Gemma vision analysis).
- Hash-based caching to avoid redundant OCR computation.
- Conforms to @audited_tool contract with strict path safety.
"""

from dataclasses import dataclass
import hashlib
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import fitz  # PyMuPDF
from PIL import Image
from pydantic import BaseModel, Field

from backend.core.config import get_settings
from backend.core.paths import AccessDenied, PathTraversalError, safe_path
from tools.registry import ToolContext, audited_tool

logger = logging.getLogger("sovereign-workbench.ocr")

# Singleton OCR engine instances
_PADDLE_OCR_INSTANCE: Optional[Any] = None
_PADDLE_AVAILABLE: Optional[bool] = None

# In-memory result cache keyed by (file_sha256, dpi, min_chars)
_OCR_RESULT_CACHE: Dict[Tuple[str, int, int], "OCRDocumentResult"] = {}


class OCRLine(BaseModel):
    """Individual recognized text line with confidence and bounding box."""
    text: str
    confidence: float
    bbox: Optional[List[List[float]]] = None  # [[x1, y1], [x2, y2], ...]


class OCRPageResult(BaseModel):
    """Structured extraction result for a single document page."""
    page: int
    text: str
    is_scanned: bool
    engine: str = "native"  # "native", "paddleocr", "tesseract"
    confidence: float = 1.0
    lines: List[OCRLine] = Field(default_factory=list)
    extracted_images: List[str] = Field(default_factory=list)


class OCRDocumentArgs(BaseModel):
    """Arguments for ocr_document tool."""
    file_path: str = Field(description="Path to local PDF or image document (within allowed roots)")
    pages: Optional[List[int]] = Field(default=None, description="1-indexed list of pages to process. If None, processes all.")
    dpi: int = Field(default=200, ge=72, le=600, description="Rendering DPI for scanned pages (default 200)")
    min_chars_threshold: int = Field(default=50, ge=0, description="Minimum characters for native text; below this triggers OCR")
    force_ocr: bool = Field(default=False, description="Force OCR execution even if native text is present")
    extract_images: bool = Field(default=True, description="Whether to extract embedded raster images for vision analysis")
    output_dir: Optional[str] = Field(default=None, description="Directory for extracted images (defaults to data/incoming/extracted_images/<hash>)")


class OCRDocumentResult(BaseModel):
    """Structured document OCR result with page references and image citations."""
    file_path: str
    sha256: str
    total_pages: int
    processed_pages: List[OCRPageResult]
    cached: bool = False


def _get_paddle_ocr() -> Optional[Any]:
    """Initialize or retrieve singleton PaddleOCR CPU instance with oneDNN/mkldnn disabled."""
    global _PADDLE_OCR_INSTANCE, _PADDLE_AVAILABLE
    if _PADDLE_AVAILABLE is False:
        return None

    if _PADDLE_OCR_INSTANCE is None:
        try:
            from paddleocr import PaddleOCR
            # Run on CPU with enable_mkldnn=False to bypass Windows PIR oneDNN attribute issue
            _PADDLE_OCR_INSTANCE = PaddleOCR(use_textline_orientation=True, lang="en", enable_mkldnn=False)
            _PADDLE_AVAILABLE = True
            logger.info("PaddleOCR engine initialized successfully on CPU (enable_mkldnn=False).")
        except Exception as exc:
            logger.warning(f"PaddleOCR initialization failed: {exc}. Will use Tesseract fallback.")
            _PADDLE_AVAILABLE = False
            return None
    return _PADDLE_OCR_INSTANCE


def _run_paddle_ocr(pil_img: Image.Image) -> Tuple[str, float, List[OCRLine]]:
    """Run PaddleOCR predict on a numpy array from PIL image and return (combined_text, avg_confidence, lines)."""
    import numpy as np
    ocr = _get_paddle_ocr()
    if ocr is None:
        raise RuntimeError("PaddleOCR engine not available.")

    img_np = np.array(pil_img)
    results = list(ocr.predict(img_np))

    lines: List[OCRLine] = []
    text_chunks: List[str] = []
    confidences: List[float] = []

    for item in results:
        rec_texts = item.get("rec_texts", []) if isinstance(item, dict) else getattr(item, "rec_texts", [])
        rec_scores = item.get("rec_scores", []) if isinstance(item, dict) else getattr(item, "rec_scores", [])
        rec_polys = item.get("rec_polys", []) if isinstance(item, dict) else getattr(item, "rec_polys", [])

        for idx, text in enumerate(rec_texts):
            text_str = str(text).strip()
            if not text_str:
                continue
            conf = float(rec_scores[idx]) if idx < len(rec_scores) else 1.0
            poly = rec_polys[idx].tolist() if idx < len(rec_polys) and hasattr(rec_polys[idx], "tolist") else None
            lines.append(OCRLine(text=text_str, confidence=round(conf, 4), bbox=poly))
            text_chunks.append(text_str)
            confidences.append(conf)

    combined_text = "\n".join(text_chunks)
    avg_conf = float(sum(confidences) / len(confidences)) if confidences else 0.0
    return combined_text, round(avg_conf, 4), lines


def _run_tesseract_ocr(pil_img: Image.Image) -> Tuple[str, float, List[OCRLine]]:
    """Run pytesseract on a PIL image as secondary fallback."""
    import pytesseract
    from pytesseract import Output

    data = pytesseract.image_to_data(pil_img, output_type=Output.DICT)
    n_boxes = len(data["text"])
    lines: List[OCRLine] = []
    text_chunks: List[str] = []
    confidences: List[float] = []

    for i in range(n_boxes):
        text = data["text"][i].strip()
        conf = float(data["conf"][i])
        if text and conf >= 0:
            norm_conf = round(conf / 100.0, 4)
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
            lines.append(OCRLine(text=text, confidence=norm_conf, bbox=bbox))
            text_chunks.append(text)
            confidences.append(norm_conf)

    combined_text = " ".join(text_chunks)
    avg_conf = float(sum(confidences) / len(confidences)) if confidences else 0.0
    return combined_text, round(avg_conf, 4), lines


def ocr_image(pil_img: Image.Image) -> Tuple[str, float, str, List[OCRLine]]:
    """Run OCR on a PIL Image using PaddleOCR with Tesseract fallback."""
    try:
        text, conf, lines = _run_paddle_ocr(pil_img)
        return text, conf, "paddleocr", lines
    except Exception as exc:
        logger.warning(f"PaddleOCR run failed: {exc}. Attempting Tesseract fallback.")
        try:
            text, conf, lines = _run_tesseract_ocr(pil_img)
            return text, conf, "tesseract", lines
        except Exception as tess_exc:
            logger.error(f"Tesseract OCR fallback also failed: {tess_exc}")
            return "", 0.0, "failed", []


def _extract_images_from_pdf_page(
    doc: fitz.Document,
    page_num: int,  # 1-indexed
    dest_dir: Path,
    min_dimension: int = 32,
) -> List[str]:
    """Extract raster images embedded in a PDF page and save to disk."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    page = doc[page_num - 1]
    image_list = page.get_images(full=True)
    saved_paths: List[str] = []

    for img_idx, img_info in enumerate(image_list, start=1):
        xref = img_info[0]
        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image.get("image")
            image_ext = base_image.get("ext", "png")
            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            # Filter out tiny icons, decorative separators, spacers
            if width < min_dimension or height < min_dimension:
                continue

            filename = f"page_{page_num}_image_{img_idx}.{image_ext}"
            out_file = dest_dir / filename
            out_file.write_bytes(image_bytes)
            saved_paths.append(str(out_file))
        except Exception as exc:
            logger.warning(f"Failed to extract image xref {xref} from page {page_num}: {exc}")

    return saved_paths


@audited_tool(
    name="ocr_document",
    side_effects=False,
    needs_role=None,
    description="Extract text and embedded images from PDF or image documents with page citations and confidence.",
)
def ocr_document(args: Union[OCRDocumentArgs, Dict[str, Any]], ctx: ToolContext) -> OCRDocumentResult:
    """Perform deterministic OCR, text extraction, and raster image extraction."""
    if isinstance(args, dict):
        args = OCRDocumentArgs.model_validate(args)

    settings = get_settings()
    allowed_roots = settings.input_dirs + settings.output_dirs

    # 1. Path confinement
    resolved_path = safe_path(args.file_path, allowed_roots=allowed_roots, must_exist=True)

    # 2. Compute file SHA-256 for caching
    content_bytes = resolved_path.read_bytes()
    file_sha256 = hashlib.sha256(content_bytes).hexdigest()

    cache_key = (file_sha256, args.dpi, args.min_chars_threshold)
    if not args.force_ocr and cache_key in _OCR_RESULT_CACHE:
        cached_result = _OCR_RESULT_CACHE[cache_key].model_copy(deep=True)
        cached_result.cached = True
        return cached_result

    # 3. Determine output directory for extracted images
    if args.output_dir:
        extracted_images_dir = safe_path(args.output_dir, allowed_roots=allowed_roots, must_exist=False)
    else:
        extracted_images_dir = Path("data/incoming/extracted_images") / file_sha256

    # 4. Handle direct image files (.png, .jpg, .jpeg, .tif, .tiff, .bmp)
    ext = resolved_path.suffix.lower()
    image_extensions = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

    if ext in image_extensions:
        pil_img = Image.open(io.BytesIO(content_bytes)).convert("RGB")
        text, conf, engine, lines = ocr_image(pil_img)

        # Save single image as an extracted image reference for downstream vision
        saved_images = []
        if args.extract_images:
            extracted_images_dir.mkdir(parents=True, exist_ok=True)
            img_path = extracted_images_dir / f"page_1_image_1{ext}"
            img_path.write_bytes(content_bytes)
            saved_images.append(str(img_path))

        page_result = OCRPageResult(
            page=1,
            text=text,
            is_scanned=True,
            engine=engine,
            confidence=conf,
            lines=lines,
            extracted_images=saved_images,
        )

        res = OCRDocumentResult(
            file_path=str(resolved_path),
            sha256=file_sha256,
            total_pages=1,
            processed_pages=[page_result],
            cached=False,
        )
        _OCR_RESULT_CACHE[cache_key] = res
        return res

    # 5. Handle PDF documents via PyMuPDF
    doc = fitz.open(str(resolved_path))
    total_pages = len(doc)

    pages_to_process = args.pages if args.pages is not None else list(range(1, total_pages + 1))
    processed_results: List[OCRPageResult] = []

    for page_num in pages_to_process:
        if page_num < 1 or page_num > total_pages:
            continue

        page = doc[page_num - 1]
        native_text = page.get_text("text").strip()

        # Check for embedded raster images
        extracted_images = []
        if args.extract_images:
            extracted_images = _extract_images_from_pdf_page(doc, page_num, extracted_images_dir)

        # Decide whether to use native text or OCR
        if len(native_text) >= args.min_chars_threshold and not args.force_ocr:
            processed_results.append(
                OCRPageResult(
                    page=page_num,
                    text=native_text,
                    is_scanned=False,
                    engine="native",
                    confidence=1.0,
                    lines=[],
                    extracted_images=extracted_images,
                )
            )
        else:
            # Scanned page detected -> render to image pixmap at requested DPI
            pix = page.get_pixmap(dpi=args.dpi)
            pil_page_img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            ocr_text, conf, engine, lines = ocr_image(pil_page_img)

            # Fallback text if OCR produced content, otherwise preserve native_text
            final_text = ocr_text if ocr_text.strip() else native_text

            processed_results.append(
                OCRPageResult(
                    page=page_num,
                    text=final_text,
                    is_scanned=True,
                    engine=engine,
                    confidence=conf,
                    lines=lines,
                    extracted_images=extracted_images,
                )
            )

    doc.close()

    result = OCRDocumentResult(
        file_path=str(resolved_path),
        sha256=file_sha256,
        total_pages=total_pages,
        processed_pages=processed_results,
        cached=False,
    )

    _OCR_RESULT_CACHE[cache_key] = result
    return result
