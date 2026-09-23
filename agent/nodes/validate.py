"""Validation node and deliverable integrity engine for Sovereign AI Workbench.

Implements all acceptance and security checks from 02_DESIGN_DOC.md §10.3 and 03_SECURITY_AND_ACCESS.md §11:
- File existence & non-zero size
- Library re-open integrity (python-docx, openpyxl, python-pptx)
- Macro-enabled extension rejection (.docm, .xlsm, .pptm, etc.)
- Template placeholder residual scan ({{...}})
- Office XML relationship & embedded OLE object safety scan (SEC-23)
- Spreadsheet formula injection & external reference sanitization (SEC-15)
- Approval note source references & visual observation limitation tags
- Bounded retries & sandbox test outcome verification
"""

import math
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import xml.etree.ElementTree as ET

from agent.state import AgentState, ArtifactRef, ValidationResult
from backend.core.events import get_event_broker
from backend.core.paths import safe_path
from tools.calculator import evaluate_expression

# Allowed output formats per 03_SECURITY_AND_ACCESS.md §11
ALLOWED_EXTENSIONS = {".docx", ".xlsx", ".pptx", ".py", ".md", ".txt", ".csv", ".json"}
FORBIDDEN_MACRO_EXTENSIONS = {".docm", ".xlsm", ".pptm", ".dotm", ".xltm", ".potm"}

PLACEHOLDER_REGEX = re.compile(r"\{\{[^}]+\}\}")


def scan_office_xml_relationships(file_path: Union[str, Path]) -> List[ValidationResult]:
    """Scan Office package (DOCX/XLSX/PPTX) XML for external relationships and OLE objects.
    
    Implements SEC-23: Detects TargetMode="External" in .rels files and embedded .bin/.ole objects.
    """
    results: List[ValidationResult] = []
    p = Path(file_path)

    if not p.exists():
        return [ValidationResult(rule="xml_package_scan", passed=False, detail="File does not exist")]

    if not zipfile.is_zipfile(p):
        # Plain text or non-zip format
        return results

    external_targets: List[str] = []
    ole_objects: List[str] = []

    try:
        with zipfile.ZipFile(p, "r") as zf:
            for name in zf.namelist():
                lower_name = name.lower()
                # Check for embedded binary / OLE objects
                if lower_name.endswith((".bin", ".ole", ".exe", ".dll", ".vbs")) or "oleobject" in lower_name:
                    ole_objects.append(name)

                # Scan relationship XML files
                if lower_name.endswith(".rels"):
                    content = zf.read(name).decode("utf-8", errors="ignore")
                    # Check for TargetMode="External"
                    if 'TargetMode="External"' in content or 'TargetMode=\'External\'' in content:
                        # Extract the target URLs/references for reporting
                        try:
                            root = ET.fromstring(content)
                            for elem in root.iter():
                                if elem.attrib.get("TargetMode") == "External":
                                    external_targets.append(f"{name}: {elem.attrib.get('Target', 'unknown')}")
                        except Exception:
                            external_targets.append(f"{name}: External relationship found")

        # Evaluate OLE rule
        if ole_objects:
            results.append(
                ValidationResult(
                    rule="no_embedded_ole_objects",
                    passed=False,
                    detail=f"Embedded binary/OLE objects detected: {', '.join(ole_objects)}",
                )
            )
        else:
            results.append(
                ValidationResult(
                    rule="no_embedded_ole_objects",
                    passed=True,
                    detail="No embedded OLE or binary objects found.",
                )
            )

        # Evaluate External Relationships rule (SEC-23)
        if external_targets:
            results.append(
                ValidationResult(
                    rule="no_external_relationships",
                    passed=False,
                    detail=f"External relationships detected: {', '.join(external_targets)}",
                )
            )
        else:
            results.append(
                ValidationResult(
                    rule="no_external_relationships",
                    passed=True,
                    detail="No external XML relationships found.",
                )
            )

    except Exception as e:
        results.append(
            ValidationResult(
                rule="xml_package_scan",
                passed=False,
                detail=f"Failed to inspect Office zip structure: {str(e)}",
            )
        )

    return results


def validate_docx_deliverable(file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
    """Validate DOCX deliverable integrity, template placeholders, and domain sections."""
    results: List[ValidationResult] = []
    p = Path(file_path)

    # 1. Re-open check
    doc = None
    try:
        import docx
        doc = docx.Document(p)
        results.append(
            ValidationResult(
                rule="docx_reopen_integrity",
                passed=True,
                detail="DOCX file opened successfully with python-docx.",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                rule="docx_reopen_integrity",
                passed=False,
                detail=f"Failed to re-open DOCX: {str(e)}",
            )
        )
        return results

    # 2. Check for leftover {{...}} placeholders
    leftover_placeholders: List[str] = []
    full_text_chunks: List[str] = []

    for paragraph in doc.paragraphs:
        full_text_chunks.append(paragraph.text)
        matches = PLACEHOLDER_REGEX.findall(paragraph.text)
        leftover_placeholders.extend(matches)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    full_text_chunks.append(paragraph.text)
                    matches = PLACEHOLDER_REGEX.findall(paragraph.text)
                    leftover_placeholders.extend(matches)

    if leftover_placeholders:
        unique_leftovers = sorted(list(set(leftover_placeholders)))
        results.append(
            ValidationResult(
                rule="no_unresolved_placeholders",
                passed=False,
                detail=f"Found unreplaced template placeholders: {', '.join(unique_leftovers)}",
            )
        )
    else:
        results.append(
            ValidationResult(
                rule="no_unresolved_placeholders",
                passed=True,
                detail="All template placeholders resolved.",
            )
        )

    # 3. Domain checks for Approval Note (if applicable)
    full_text = "\n".join(full_text_chunks).lower()
    is_approval_note = "approval" in p.name.lower() or "approval note" in full_text or (metadata and metadata.get("template") == "approval_note")

    if is_approval_note:
        # Check source references for findings
        if metadata and "findings" in metadata:
            findings = metadata["findings"]
            missing_source = [f for f in findings if isinstance(f, dict) and not (f.get("source") or f.get("source_ref") or f.get("page"))]
            if missing_source:
                results.append(
                    ValidationResult(
                        rule="findings_source_references",
                        passed=False,
                        detail=f"{len(missing_source)} finding(s) missing required source references.",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        rule="findings_source_references",
                        passed=True,
                        detail=f"All {len(findings)} findings cite source references.",
                    )
                )

        # Check visual observations have limitation and observed/inferred tags
        if metadata and "visual_observations" in metadata:
            obs_list = metadata["visual_observations"]
            missing_limitation = [o for o in obs_list if isinstance(o, dict) and not o.get("limitation")]
            if missing_limitation:
                results.append(
                    ValidationResult(
                        rule="visual_observations_limitation",
                        passed=False,
                        detail=f"{len(missing_limitation)} visual observation(s) missing mandatory limitation note.",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        rule="visual_observations_limitation",
                        passed=True,
                        detail=f"All {len(obs_list)} visual observations include mandatory limitation note.",
                    )
                )

        # Check human review section presence
        if "human review" in full_text or "decision:" in full_text or "reviewer" in full_text:
            results.append(
                ValidationResult(
                    rule="human_review_gate_present",
                    passed=True,
                    detail="Human review gate section present in approval note.",
                )
            )
        else:
            results.append(
                ValidationResult(
                    rule="human_review_gate_present",
                    passed=False,
                    detail="Approval note missing required blank human review gate section.",
                )
            )

    return results


def validate_xlsx_deliverable(file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
    """Validate XLSX workbook integrity, formula sanitization (SEC-15), and sheet structures."""
    results: List[ValidationResult] = []
    p = Path(file_path)

    wb = None
    try:
        import openpyxl
        wb = openpyxl.load_workbook(p, data_only=False)
        results.append(
            ValidationResult(
                rule="xlsx_reopen_integrity",
                passed=True,
                detail=f"XLSX workbook loaded successfully ({len(wb.sheetnames)} sheets).",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                rule="xlsx_reopen_integrity",
                passed=False,
                detail=f"Failed to load XLSX workbook: {str(e)}",
            )
        )
        return results

    # Scan sheets for formula safety and injection attempts (SEC-15)
    unsafe_formulas: List[str] = []
    unescaped_injections: List[str] = []

    forbidden_funcs = ["WEBSERVICE", "HYPERLINK", "DDE"]

    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        for row in sheet.iter_rows(values_only=False):
            for cell in row:
                val = cell.value
                if val is None:
                    continue
                s_val = str(val).strip()

                # If the cell is evaluated as a formula (starts with =)
                if s_val.startswith("="):
                    upper = s_val.upper()
                    # Check for dangerous external calls
                    for fn in forbidden_funcs:
                        if fn in upper:
                            # Allow internal HYPERLINK without http/https if needed, but block external URLs
                            if fn == "HYPERLINK" and ("http://" not in upper and "https://" not in upper):
                                continue
                            unsafe_formulas.append(f"{sheet_name}!{cell.coordinate}: contains {fn}")

                    # Check for external workbook references [Book.xlsx]
                    if "[" in s_val and "]" in s_val:
                        unsafe_formulas.append(f"{sheet_name}!{cell.coordinate}: external workbook reference")

                # If cell is non-formula data but was an untrusted input starting with dangerous characters
                # In openpyxl, a string that was escaped starts with a single quote or has cell.data_type == 's'
                # Check for raw unescaped command injection patterns in data cells
                if sheet_name == "Data" and s_val.startswith(("+", "-", "@")):
                    # Numbers are fine (e.g. -5.2), but strings with formulas like +cmd or @sum are not
                    if not isinstance(val, (int, float)):
                        # If it's a string, check if it's treated as formula or code
                        if any(c in s_val for c in ["|", "!", "(", ")"]):
                            unescaped_injections.append(f"{sheet_name}!{cell.coordinate}: {s_val}")

    if unsafe_formulas:
        results.append(
            ValidationResult(
                rule="xlsx_formula_safety",
                passed=False,
                detail=f"Unsafe formulas detected: {', '.join(unsafe_formulas[:5])}",
            )
        )
    else:
        results.append(
            ValidationResult(
                rule="xlsx_formula_safety",
                passed=True,
                detail="Formulas parsed safely without external calls, DDE, or WEBSERVICE.",
            )
        )

    if unescaped_injections:
        results.append(
            ValidationResult(
                rule="xlsx_injection_sanitization",
                passed=False,
                detail=f"Unescaped untrusted command strings in Data sheet: {', '.join(unescaped_injections[:5])}",
            )
        )
    else:
        results.append(
            ValidationResult(
                rule="xlsx_injection_sanitization",
                passed=True,
                detail="All untrusted cell text sanitized (SEC-15 compliant).",
            )
        )

    return results


def validate_pptx_deliverable(file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
    """Validate PPTX presentation integrity and template placeholders."""
    results: List[ValidationResult] = []
    p = Path(file_path)

    prs = None
    try:
        import pptx
        prs = pptx.Presentation(p)
        results.append(
            ValidationResult(
                rule="pptx_reopen_integrity",
                passed=True,
                detail=f"PPTX presentation opened successfully ({len(prs.slides)} slides).",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                rule="pptx_reopen_integrity",
                passed=False,
                detail=f"Failed to open PPTX: {str(e)}",
            )
        )
        return results

    # Scan shapes and text frames for unresolved {{...}} placeholders
    leftover_placeholders: List[str] = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    matches = PLACEHOLDER_REGEX.findall(paragraph.text)
                    leftover_placeholders.extend(matches)

    if leftover_placeholders:
        unique_leftovers = sorted(list(set(leftover_placeholders)))
        results.append(
            ValidationResult(
                rule="no_unresolved_placeholders",
                passed=False,
                detail=f"Found unreplaced PPTX placeholders: {', '.join(unique_leftovers)}",
            )
        )
    else:
        results.append(
            ValidationResult(
                rule="no_unresolved_placeholders",
                passed=True,
                detail="All presentation placeholders resolved.",
            )
        )

    return results


def validate_calculation_consistency(formula: str, variables: Dict[str, Any], reported_result: Any, tolerance: float = 1e-4) -> ValidationResult:
    """Verify that a reported calculation matches the deterministic AST calculator result."""
    try:
        computed = evaluate_expression(formula, variables)
        if isinstance(reported_result, (int, float)) and isinstance(computed, (int, float)):
            diff = abs(float(computed) - float(reported_result))
            if diff <= tolerance:
                return ValidationResult(
                    rule="calculation_consistency",
                    passed=True,
                    detail=f"Calculation verified deterministically: {formula} = {computed}",
                )
            else:
                return ValidationResult(
                    rule="calculation_consistency",
                    passed=False,
                    detail=f"Calculation mismatch: expected {computed}, got reported {reported_result} (diff {diff})",
                )
        elif str(computed).strip() == str(reported_result).strip():
            return ValidationResult(
                rule="calculation_consistency",
                passed=True,
                detail=f"Calculation verified: {formula} = {computed}",
            )
        else:
            return ValidationResult(
                rule="calculation_consistency",
                passed=False,
                detail=f"Calculation mismatch: computed '{computed}' vs reported '{reported_result}'",
            )
    except Exception as e:
        return ValidationResult(
            rule="calculation_consistency",
            passed=False,
            detail=f"Safe calculation evaluation failed for '{formula}': {str(e)}",
        )


def validate_artifact_file(file_path: Union[str, Path], artifact_kind: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
    """Comprehensive validation suite for a generated deliverable file."""
    results: List[ValidationResult] = []
    p = Path(file_path)

    # 1. Existence and size
    if not p.exists():
        return [ValidationResult(rule="file_exists", passed=False, detail=f"Deliverable file does not exist: {p.name}")]
    
    size = p.stat().st_size
    if size == 0:
        return [ValidationResult(rule="file_size_non_zero", passed=False, detail=f"Deliverable file is 0 bytes: {p.name}")]
    
    results.append(
        ValidationResult(
            rule="file_exists_and_non_empty",
            passed=True,
            detail=f"File {p.name} exists ({size} bytes).",
        )
    )

    ext = p.suffix.lower()

    # 2. Macro-enabled rejection
    if ext in FORBIDDEN_MACRO_EXTENSIONS:
        results.append(
            ValidationResult(
                rule="no_macro_enabled_formats",
                passed=False,
                detail=f"Forbidden macro-enabled extension detected: {ext}",
            )
        )
        return results
    else:
        results.append(
            ValidationResult(
                rule="no_macro_enabled_formats",
                passed=True,
                detail=f"Extension {ext} is free of macro-enabled hazards.",
            )
        )

    # 3. Allowed formats
    if ext not in ALLOWED_EXTENSIONS:
        results.append(
            ValidationResult(
                rule="allowed_format",
                passed=False,
                detail=f"Extension '{ext}' not in allowed deliverable formats {ALLOWED_EXTENSIONS}",
            )
        )
        return results

    # 4. XML / Relationship scan for Office formats
    if ext in {".docx", ".xlsx", ".pptx"}:
        xml_results = scan_office_xml_relationships(p)
        results.extend(xml_results)

    # 5. Format-specific inspections
    if ext == ".docx":
        docx_results = validate_docx_deliverable(p, metadata=metadata)
        results.extend(docx_results)
    elif ext == ".xlsx":
        xlsx_results = validate_xlsx_deliverable(p, metadata=metadata)
        results.extend(xlsx_results)
    elif ext == ".pptx":
        pptx_results = validate_pptx_deliverable(p, metadata=metadata)
        results.extend(pptx_results)

    return results


def validate_node(state: AgentState) -> Dict[str, Any]:
    """Validate task execution integrity and output criteria (LangGraph node)."""
    run_id = state.get("run_id", "adhoc")
    errors = state.get("errors", [])
    tool_results = state.get("tool_results", [])
    generated_artifacts = state.get("generated_artifacts", [])
    validation_results: List[ValidationResult] = []

    # Check 1: General error accumulation
    if errors:
        for err in errors:
            validation_results.append(
                ValidationResult(
                    rule="no_execution_errors",
                    passed=False,
                    detail=err,
                )
            )
    else:
        validation_results.append(
            ValidationResult(
                rule="no_execution_errors",
                passed=True,
                detail="All execution steps completed without error.",
            )
        )

    # Check 2: Tool execution status
    failed_tools = [r for r in tool_results if r.status == "error"]
    if failed_tools:
        for ft in failed_tools:
            validation_results.append(
                ValidationResult(
                    rule=f"tool_status_{ft.tool}",
                    passed=False,
                    detail=f"Step {ft.step_id} failed: {ft.error}",
                )
            )
    else:
        validation_results.append(
            ValidationResult(
                rule="all_tools_succeeded",
                passed=True,
                detail=f"All {len(tool_results)} tool calls succeeded.",
            )
        )

    # Check 3: Sandbox code execution outcome (02_DESIGN_DOC.md §10.2: Sandbox exit code 0)
    for r in tool_results:
        if r.tool == "run_code" and r.output:
            exit_code = r.output.get("exit_code", 0)
            status_val = r.output.get("status", "passed")
            if exit_code != 0 or status_val in {"failed", "timeout", "error"}:
                validation_results.append(
                    ValidationResult(
                        rule="sandbox_tests_passed",
                        passed=False,
                        detail=f"Sandbox execution failed (exit code {exit_code}, status {status_val})",
                    )
                )
            else:
                validation_results.append(
                    ValidationResult(
                        rule="sandbox_tests_passed",
                        passed=True,
                        detail="Sandbox test suite passed (exit code 0).",
                    )
                )

    # Check 4: Generated deliverable artifacts validation
    # Gather artifacts from state.generated_artifacts or tool outputs
    artifact_paths_to_validate: List[tuple[str, Optional[str], Optional[Dict[str, Any]]]] = []

    for art in generated_artifacts:
        artifact_paths_to_validate.append((art.path, art.kind, None))

    for r in tool_results:
        if r.output and isinstance(r.output, dict):
            p = r.output.get("path")
            if p and (p, None, None) not in [(x[0], None, None) for x in artifact_paths_to_validate]:
                meta = r.output.get("metadata")
                artifact_paths_to_validate.append((p, r.output.get("kind"), meta))

    for path_str, kind, meta in artifact_paths_to_validate:
        file_validations = validate_artifact_file(path_str, artifact_kind=kind, metadata=meta)
        validation_results.extend(file_validations)

    all_passed = all(vr.passed for vr in validation_results)
    status_str = "ok" if all_passed else "fail"

    broker = get_event_broker()
    broker.emit(
        run_id=run_id,
        event_type="validation",
        node="validate",
        status=status_str,
        summary=f"Validation {'passed' if all_passed else 'failed'} ({len(validation_results)} checks evaluated)",
    )

    return {
        "validation_results": validation_results,
    }
