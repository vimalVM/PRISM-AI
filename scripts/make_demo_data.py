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
from typing import Dict

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


if __name__ == "__main__":
    print("--- Generating and Ingesting Synthetic Demo SOPs ---")
    paths = generate_and_ingest_demo_data(ingest_to_kb=True)
    print(f"Successfully created and ingested {len(paths)} SOPs:")
    for doc_id, p in paths.items():
        print(f"  - {doc_id}: {p}")
