"""Synthetic Standard Operating Procedure (SOP) generator and seeder for Sovereign AI Workbench.

Generates 4 realistic industrial SOPs with hierarchical classifications (0..3):
- SOP-101: Site Safety & PPE Guidelines (PUBLIC / 0)
- SOP-201: Turbine Maintenance & Lubrication Schedule (INTERNAL / 1)
- SOP-301: High-Pressure Vessel Inspection Tolerances (CONFIDENTIAL / 2)
- SOP-401: Core Reactor Emergency Scram Actions (RESTRICTED / 3)

Writes files into data/knowledge_base/ and indexes them into ChromaDB and SQLite.
"""

from pathlib import Path
import sys
from typing import Dict, Tuple

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.core.db import init_db
from rag.ingest import ingest_document


SOP_101_PUBLIC = """# SOP-101: Industrial Site Safety and PPE Protocols

## 1. Scope and Objective
This standard operating procedure outlines general site safety rules, visitor guidelines, and mandatory Personal Protective Equipment (PPE) required for all personnel on the facility grounds.

## 2. Mandatory PPE Requirements
All personnel entering zones marked 'Operational Area' must wear:
- High-visibility safety vest (Class 2 minimum)
- Steel-toed protective boots (ASTM F2413 compliant)
- ANSI Z87.1 certified safety glasses with side shields
- Hard hat (Type I, Class E)

## 3. Emergency Evacuation
In the event of an evacuation horn (continuous 3-pulse alarm):
1. Immediately stop all hot work and secure heavy equipment.
2. Evacuate via the marked green egress pathways.
3. Assemble at Assembly Area North (near Gate 3).
4. Await head-count verification from the designated Safety Marshal.
"""

SOP_201_INTERNAL = """# SOP-201: Heavy Turbine Maintenance & Lubrication Standard

## 1. Operating Context
This procedure applies to Model-7 Gas Turbines operating in Unit A and Unit B. Routine servicing is performed every 4,000 equivalent operating hours.

## 2. Lubrication Schedule
- Main Bearing Journal: Inspect oil pressure every 24 hours. Pressure must remain between 180 kPa and 220 kPa.
- Filter Replacement: Dual duplex oil filters must be switched and element replaced when differential pressure exceeds 45 kPa.
- Oil Specification: Use ISO VG 46 synthetic turbine lubricant. Do not mix with mineral-based alternatives.

## 3. Vibration Thresholds
Vibration monitoring sensors are installed on Bearing 1 and Bearing 2:
- Normal Operation: Peak vibration < 2.8 mm/s RMS.
- Warning Threshold: Peak vibration between 2.8 mm/s and 4.5 mm/s RMS. Log incident and schedule borescope inspection within 48 hours.
- Mandatory Shutdown: Peak vibration >= 7.1 mm/s RMS requires emergency trip.
"""

SOP_301_CONFIDENTIAL = """# SOP-301: High-Pressure Vessel Weld Tolerances & Non-Destructive Testing

## 1. Classification
CONFIDENTIAL — PROPRIETARY ENGINEERING DOCUMENT.
Distribution limited to qualified Quality Assurance and Mechanical Integrity Engineers.

## 2. Circumferential Weld Inspection
All Class-1 pressure vessels rated above 15 MPa must undergo ultrasonic thickness and phased array inspection annually:
- Wall Thinning Limit: Maximum allowable general wall loss is 1.5 mm from nominal design thickness (18.0 mm).
- Pitting Corrosion: Localized pits must not exceed 2.2 mm in depth or 10 mm in lateral cluster width.
- Weld Seam Discontinuities: Lack of fusion or root cracking of any length constitutes an immediate rejection and vessel decertification.

## 3. Hydrostatic Proof Testing
Following any weld repair:
- Test pressure must equal 1.5 times the Maximum Allowable Working Pressure (MAWP).
- Hold time at test pressure is exactly 30 minutes with zero observable pressure drop.
- Calibration record for digital test gauges must be filed in the confidential QA vault.
"""

SOP_401_RESTRICTED = """# SOP-401: Core Reactor Emergency Scram & Critical Cooling Actions

## 1. Classification
RESTRICTED — HIGHEST SECURITY CLEARANCE REQUIRED.
Authorized strictly for Senior Reactor Operators and Chief Nuclear Officers.

## 2. Immediate Scram Conditions
Manual scram initiation is mandatory and non-discretionary upon any of the following triggers:
- Reactor coolant outlet temperature exceeds 335.0 °C.
- Primary loop pressurizer pressure drops below 12.2 MPa while thermal output exceeds 15%.
- Unexplained reactivity insertion rate exceeding 0.05 $/s.

## 3. Emergency Core Cooling Injection (ECCI)
1. Verify immediate insertion of all control rod banks within 2.4 seconds.
2. Confirm automatic start of High-Pressure Safety Injection (HPSI) pumps 1A and 1B within 8 seconds.
3. Align Emergency Feedwater to Steam Generators at a minimum rate of 120 kg/s per train.
4. Establish secondary heat sink and maintain hot shutdown margin of >= 3,000 pcm boron equivalent.
5. Notify Nuclear Safety Directorate via Secure Red-Line Channel within 15 minutes of initiation.
"""


def generate_and_ingest_demo_data(ingest_to_kb: bool = True) -> Dict[str, Path]:
    """Generate synthetic SOP text files and optionally index into local Knowledge Base."""
    init_db()

    kb_dir = Path("data/knowledge_base")
    kb_dir.mkdir(parents=True, exist_ok=True)

    sops = [
        ("SOP-101", "SOP-101_Site_Safety.txt", SOP_101_PUBLIC, 0),  # PUBLIC
        ("SOP-201", "SOP-201_Turbine_Maintenance.txt", SOP_201_INTERNAL, 1),  # INTERNAL
        ("SOP-301", "SOP-301_Pressure_Vessel.txt", SOP_301_CONFIDENTIAL, 2),  # CONFIDENTIAL
        ("SOP-401", "SOP-401_Reactor_Scram.txt", SOP_401_RESTRICTED, 3),  # RESTRICTED
    ]

    created_paths = {}

    for doc_id, filename, content, classification in sops:
        file_path = kb_dir / filename
        file_path.write_text(content.strip(), encoding="utf-8")
        created_paths[doc_id] = file_path

        if ingest_to_kb:
            print(f"Ingesting {doc_id} ({filename}) [Classification: {classification}]...")
            ingest_document(
                file_path=file_path,
                doc_id=doc_id,
                classification=classification,
                version=1,
                uploaded_by="system",
            )

    return created_paths


def generate_scanned_inspection_pdf(output_dir: Path | None = None) -> Tuple[Path, Path]:
    """Generate synthetic 2-page scanned-style inspection report PDF with embedded photo."""
    import io
    import fitz
    from PIL import Image, ImageDraw

    out_dir = output_dir or Path("data/incoming")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "demo_scanned_inspection_report.pdf"
    photo_path = out_dir / "demo_inspection_photo.png"

    # 1. Render Page 1 as an image (simulating a scanned document)
    # A4 at ~150 DPI: 1240 x 1754 px
    p1_img = Image.new("RGB", (1240, 1754), color=(252, 252, 250))
    draw = ImageDraw.Draw(p1_img)

    # Header and borders
    draw.rectangle([(40, 40), (1200, 1714)], outline=(180, 180, 180), width=2)
    draw.rectangle([(50, 50), (1190, 180)], fill=(235, 238, 242))

    # Stamp / Classification banner
    draw.text((70, 70), "CONFIDENTIAL - PROPRIETARY INTEGRITY AUDIT", fill=(180, 20, 20))
    draw.text((70, 110), "ULTRASONIC THICKNESS & WELD INSPECTION REPORT", fill=(20, 30, 60))
    draw.text((70, 145), "DOCUMENT REF: INSP-2026-PV402  |  DATE: 2026-09-15  |  FACILITY: UNIT 4B", fill=(80, 80, 80))

    lines = [
        ("SECTION 1: TARGET EQUIPMENT IDENTIFICATION", (20, 40, 80)),
        ("Equipment: Primary Catalytic Distillation Vessel (Tag: PV-402)", (40, 40, 40)),
        ("Design Spec: ASME Section VIII Div 1  |  Rated Pressure: 16.5 MPa", (40, 40, 40)),
        ("Nominal Shell Wall Thickness: 18.0 mm  |  Material: SA-516 Grade 70", (40, 40, 40)),
        ("Governing SOP Standard: SOP-301 Section 2 (Weld Inspection Tolerances)", (40, 40, 40)),
        ("", (0, 0, 0)),
        ("SECTION 2: NON-DESTRUCTIVE ULTRASONIC TEST FINDINGS", (20, 40, 80)),
        ("Inspection Method: Phased Array Ultrasonic Testing (PAUT) & Digital B-Scan", (40, 40, 40)),
        ("Inspected Region: Circumferential Weld Seam CW-3 (Elevation +4.2 m)", (40, 40, 40)),
        ("Measured Minimum Wall Thickness: 16.1 mm", (160, 20, 20)),
        ("Total General Wall Thinning: 1.9 mm loss from nominal (18.0 mm)", (160, 20, 20)),
        ("SOP-301 Allowed Thinning Threshold: 1.5 mm MAXIMUM", (40, 40, 40)),
        ("Deviation Assessment: EXCEEDS MAXIMUM PERMITTED THINNING BY 0.4 mm", (180, 0, 0)),
        ("", (0, 0, 0)),
        ("SECTION 3: SURFACE CORROSION & PITTING SURVEY", (20, 40, 80)),
        ("Inspection Method: Direct Video Borescope & Laser Profilometry", (40, 40, 40)),
        ("Localized Pit Cluster: Located 120 mm upstream of Weld CW-3 heat affected zone", (40, 40, 40)),
        ("Measured Pit Cluster Width: 14.5 mm (SOP-301 limit is 10.0 mm)", (160, 20, 20)),
        ("Measured Maximum Pit Depth: 2.6 mm (SOP-301 limit is 2.2 mm)", (160, 20, 20)),
        ("Crack Indication: No linear crack indications observed along root pass.", (40, 40, 40)),
        ("", (0, 0, 0)),
        ("SECTION 4: QUALITY ASSURANCE DISPOSITION & RECOMMENDATIONS", (20, 40, 80)),
        ("1. Immediate Decertification: Vessel PV-402 is decertified pending formal repair.", (40, 40, 40)),
        ("2. Weld Overlay: Mechanical Engineering must submit weld overlay repair plan.", (40, 40, 40)),
        ("3. Proof Test: Mandatory 1.5x MAWP hydrostatic proof test required prior to return to service.", (40, 40, 40)),
        ("4. See Page 2 for high-resolution visual evidence photograph of Seam CW-3.", (40, 40, 40)),
    ]

    y = 230
    for text, color in lines:
        if text:
            draw.text((70, y), text, fill=color)
        y += 45

    # 2. Render Page 2 and Inspection Photo
    # Photo: 800 x 600 px showing technical diagram of weld seam with pit marks
    photo = Image.new("RGB", (800, 600), color=(220, 225, 230))
    p_draw = ImageDraw.Draw(photo)

    # Draw simulated weld plates and seam
    p_draw.rectangle([(50, 150), (750, 450)], fill=(160, 165, 175), outline=(100, 105, 115), width=3)
    p_draw.line([(400, 150), (400, 450)], fill=(90, 80, 70), width=24)  # Weld bead
    p_draw.text((320, 110), "WELD SEAM CW-3", fill=(40, 50, 70))

    # Draw corrosion pit cluster
    p_draw.ellipse([(280, 260), (330, 310)], fill=(120, 60, 40), outline=(80, 20, 10), width=2)
    p_draw.text((250, 325), "PIT CLUSTER (14.5mm x 2.6mm)", fill=(160, 20, 20))
    p_draw.line([(310, 310), (310, 325)], fill=(160, 20, 20), width=2)

    # Save photo directly to incoming
    photo.save(str(photo_path), format="PNG")

    # Page 2 image
    p2_img = Image.new("RGB", (1240, 1754), color=(252, 252, 250))
    p2_draw = ImageDraw.Draw(p2_img)
    p2_draw.rectangle([(40, 40), (1200, 1714)], outline=(180, 180, 180), width=2)
    p2_draw.text((70, 70), "CONFIDENTIAL - VISUAL EVIDENCE & PHOTOGRAPHIC RECORD", fill=(180, 20, 20))
    p2_draw.text((70, 110), "PAGE 2: OPTICAL BORESCOPE SURVEY - VESSEL PV-402 WELD CW-3", fill=(20, 30, 60))
    p2_draw.text((70, 160), "Figure 1: Circumferential weld CW-3 root pass and adjacent HAZ corrosion pitting cluster.", fill=(60, 60, 60))

    # Paste photo into Page 2
    p2_img.paste(photo, (220, 250))
    p2_draw.text((220, 870), "Image Reference: page_2_image_1  |  Sensor: High-Res Endoscope Model V7", fill=(80, 80, 80))
    p2_draw.text((220, 910), "Observation: Localized metal loss and pitting visible in heat-affected zone.", fill=(40, 40, 40))

    # 3. Create PDF with PyMuPDF containing the rendered page images and embedded photo
    doc = fitz.open()

    # Add Page 1 as pure image page (no native text -> forces OCR)
    p1_bytes = io.BytesIO()
    p1_img.save(p1_bytes, format="PNG")
    page1 = doc.new_page(width=612, height=792)  # Standard letter
    page1.insert_image(page1.rect, stream=p1_bytes.getvalue())

    # Add Page 2 as page with embedded raster photo
    page2 = doc.new_page(width=612, height=792)
    # Background
    p2_bytes = io.BytesIO()
    p2_img.save(p2_bytes, format="PNG")
    page2.insert_image(page2.rect, stream=p2_bytes.getvalue())

    doc.save(str(pdf_path))
    doc.close()

    return pdf_path, photo_path


if __name__ == "__main__":
    print("--- Generating and Ingesting Synthetic Demo SOPs ---")
    paths = generate_and_ingest_demo_data(ingest_to_kb=True)
    print(f"Successfully created and ingested {len(paths)} SOPs:")
    for doc_id, p in paths.items():
        print(f"  - {doc_id}: {p}")

    print("\n--- Generating Synthetic Scanned Inspection Report & Photo ---")
    pdf_p, photo_p = generate_scanned_inspection_pdf()
    print(f"Generated synthetic scanned report: {pdf_p}")
    print(f"Generated synthetic inspection photo: {photo_p}")

