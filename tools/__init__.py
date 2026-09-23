"""Tools package for Sovereign AI Workbench.

Importing this package ensures that all audited tools are registered in the central ToolRegistry.
"""

from tools.files import read_file, write_file
from tools.ocr import ocr_document
from tools.vision import vision_analyze, vision_analyze_batch
from tools.rag import search_knowledge
from tools.calculator import calculate
from tools.sandbox import run_code
from tools.documents import (
    create_docx,
    create_xlsx,
    create_pptx,
    create_calculation_report,
)

__all__ = [
    "read_file",
    "write_file",
    "ocr_document",
    "vision_analyze",
    "vision_analyze_batch",
    "search_knowledge",
    "calculate",
    "run_code",
    "create_docx",
    "create_xlsx",
    "create_pptx",
    "create_calculation_report",
]
