# Sovereign AI Workbench — Progress Log

## Phase Checklist

- [x] **Phase 0** — Preflight, scaffold, env, model check
- [x] **Phase 1** — Config, model registry, Ollama client
- [x] **Phase 2** — Database, auth, RBAC, audit core
- [x] **Phase 3** — Minimal LangGraph agent + first tool + SSE
- [x] **Phase 4** — RAG ingestion + retrieval with access control
- [x] **Phase 5** — PDF parsing + OCR
- [x] **Phase 6** — Vision tool (Gemma 4 E4B)
- [x] **Phase 7** — Router + registry-driven model selection
- [x] **Phase 8** — Calculator + Docker sandbox + coding loop
- [x] **Phase 9** — Deliverable generators + validation
- [x] **Phase 10** — Inspection workflow + human review gate
- [x] **Phase 11** — React frontend
- [x] **Phase 12** — Sovereignty panel + egress scan + offline proof
- [x] **Phase 13** — Test suite, evaluation harness, benchmarks
- [x] **Phase 14** — Packaging, start scripts, demo data, README
- [ ] **Phase 15 (Future)** — Optional third model route (Bonsai 2 27B; post-MVP)

---

## Current Status
- **Active Phase**: Phase 14 Complete (All MVP Phases 0–14 Finished; Ready for Hackathon Demonstration)
- **Completed**:
  - Phase 0 (Scaffolding, environment, dependencies, Ollama model validation, Qwen & Gemma benchmarks, offline weights verified)
  - Phase 1 (config.py, registry.yaml, registry.py, ollama_client.py, selfcheck.py, backend/main.py with /api/health + /api/models + /api/models/reload, 20 tests all passing)
  - Phase 2 (SQLite DB schema §13, Argon2id auth + HMAC session signing, RBAC + clearance hierarchy §5, segregation of duties SEC-11, safe_path SEC-06, append-only hash chain audit log SEC-14, CSP/CSRF/CORS/rate-limiting middleware SEC-17, user seed script, 91/91 tests passing)
  - Phase 3 (AgentState and sub-models §6.2, @audited_tool registry §7.2, safe read_file and write_file §7.3, prompt delimiters and JSON schemas §6.4, LangGraph StateGraph with bounded retries §6.1, EventBroker and task_events DB persistence §6.6, /api/tasks CRUD and SSE streaming endpoints, static egress scanner scripts/scan_egress.py §3.6, 110/110 tests all passing)
  - Phase 4 (Document chunking §8.3 with paragraph/heading & table headers, multi-format parsers PDF/DOCX/XLSX/PPTX §8.4, offline CPU SentenceTransformer embeddings, persistent ChromaDB with telemetry OFF, server-side retrieval clearance filter SEC-04, version superseding SEC-05, audited search_knowledge tool §7.3, KB REST APIs §8, synthetic SOP dataset seeder scripts/make_demo_data.py, 118/118 tests all passing)
  - Phase 5 (Deterministic OCR tool `tools/ocr.py` with PyMuPDF native text detection, scanned page rendering at 150-200 DPI, PaddleOCR CPU inference with `enable_mkldnn=False`, embedded raster image extraction `page_X_image_Y.png`, upload endpoint `/api/files/upload` with SEC-07 validation, magic-byte inspection, decompression bomb protection, PDF page limits, RAG OCR ingestion fallback, synthetic scanned inspection report generator, 131/131 tests all passing)
  - Phase 6 (Multimodal vision analysis `tools/vision.py` using Gemma 4 E4B from registry, strict `VisualObservation` schema with mandatory `limitation` and `observed` vs `inferred` typing, engineering safety boundary enforcement, Lanczos downscaling to max edge 1280 px, one-shot JSON repair retry, batch analysis `vision_analyze_batch`, graceful failure handling, live smoke test on local Gemma 4 E4B, 139/139 tests all passing)
  - Phase 7 (Router & model selection engine `agent/router.py`, deterministic modality & keyword classification, LLM JSON fallback, config-driven model selection matching `models/registry.yaml`, content-free `model_route` audit logging, ModelSwapManager tracking active model and `keep_alive: 0` unloading, contiguous vision plan step clustering, intake node integration, 153/153 tests all passing)
  - Phase 8 (Safe deterministic AST calculator `tools/calculator.py`, hardened Docker sandbox `docker/sandbox/Dockerfile` and `tools/sandbox.py` with `--network=none`, `--cpus=1`, `--memory=512m`, `--pids-limit=128`, `--read-only`, non-root user 10001, wall-clock timeout kill, 64KB output cap, static denylist scanner, code deliverable packaging `agent/coding.py`, bounded correction loop, 179/179 tests all passing)
  - Phase 9 (Templates generator `scripts/make_templates.py` for approval_note.docx, report.docx, and presentation.pptx; document tools `tools/documents.py` for `create_docx`, `create_xlsx`, `create_pptx`, and `create_calculation_report` with SEC-15 formula sanitization; deliverable validation library `agent/nodes/validate.py` with re-open checks, macro rejection, residual placeholder scanning, SEC-23 external relationship/OLE scanning, source reference validation, and calculation verification; artifacts API `backend/api/artifacts.py` with metadata, validation checklist, and scoped downloads enforcing SEC-19 auditor 403 and SEC-20 reviewer 403; 198/198 tests all passing)
  - Phase 10 (Demo A Inspection Report to Approval Note workflow `agent/inspection.py` end-to-end; OCR document extraction + raster image extraction; multimodal vision analysis with mandatory `limitation` & `observed` tags; SOP-301 RAG retrieval; deterministic AST numerical calculations for general wall thinning loss [1.90 mm], threshold exceedance [0.40 mm non-compliant], and hydrostatic proof pressure [24.75 MPa]; Word deliverable generation `Inspection_Approval_Note.docx` from `templates/approval_note.docx`; deliverable validation; Human Review Gate setting `PENDING_REVIEW` with agent unable to self-approve; Review REST API `POST /api/artifacts/{id}/review` & `GET /api/review/queue` strictly enforcing SEC-11 segregation of duties: author cannot review own artifact [403], admin cannot review artifact [403], only reviewer role can approve/reject; 205/205 tests all passing)
  - Phase 11 (Complete React frontend built with Vite, TypeScript, Tailwind CSS, local font bundling [@fontsource/geist-sans, @fontsource/jetbrains-mono, lucide-react], unified AI workbench, inspection vision suite with interactive reticle HUD, human review gate with segregation of duties, sovereign knowledge base, model registry, audit trail, sovereignty status, and role-based access control login; production bundle compiled to frontend/dist and mounted to FastAPI StaticFiles)
  - Phase 12 (Sovereignty & system endpoints `backend/api/system.py` [/api/system/status, /api/system/connections, /api/system/probe]; passive psutil socket audit of workbench processes; startup air-gap enforcement in `backend/main.py` refusing non-loopback binds and :cloud model tags; static egress scanner `scripts/scan_egress.py` verified with 0 findings across 111 files; automated offline evidence collector `scripts/offline_proof.ps1` and procedure `scripts/offline_proof.md`; evidence repository `docs/evidence/README.md` indexing E1..E8; live Sovereignty page UI integrated with backend telemetry; 212 tests passing)
  - Phase 13 (Evaluation harness `scripts/eval_run.py` executing all 16 evaluation checks EV-01..EV-16 with 100% pass rate; generated markdown report `docs/evidence/eval_report.md`; hardware and tool benchmark harness `scripts/benchmark.py` measuring host CPU/RAM, NVIDIA RTX 3050 Laptop GPU VRAM, AST calculator throughput, DOCX/XLSX generation latency, and Ollama inference speed, generating `docs/evidence/benchmark.md` and `docs/evidence/benchmark_results.json`; full CI pipeline runners `scripts/check_all.ps1` and `scripts/check_all.sh` verifying egress scan, frontend build, pytest suite, eval harness, and benchmarks end-to-end; 213 unit and integration tests passing in 188s)
  - Phase 14 (One-command offline startup scripts `scripts/start.ps1` and `scripts/start.sh` enforcing offline environment variables, pre-warming models via Ollama API, seeding default users, launching FastAPI backend on `127.0.0.1:8000`, and opening local browser; offline packaging automation `scripts/package_offline.ps1` and `scripts/package_offline.sh` generating `dist/offline_package/SHA256SUMS.txt` and `OFFLINE_PACKAGE_MANIFEST.md`; complete demo dataset with synthetic 12.45 MB scanned inspection report, high-resolution weld bead photo, coding prompt for ASME UG-27 pressure vessel stress calculations, and 3 knowledge base SOPs; third-party and model license catalog `docs/LICENSES.md`; comprehensive `README.md` with system architecture diagrams, quickstart, hackathon run-of-show demo script, security & air-gap guarantees, and troubleshooting; automated demo rehearsal `scripts/run_demo.py` verifying all 13 demo milestones twice offline in under 7 minutes [Run 1: 60.39s, Run 2: 3.22s, 100% passing] recorded in `docs/evidence/demo_rehearsal.md`)
- **Deviations**: None.
- **Decisions & Notes**:
  - `qwen3.5:4b` (3.4 GB) and `gemma4:e4b` (9.6 GB) verified on Ollama 0.34.2.
  - VRAM fit verified on RTX 3050 Laptop GPU (peak ~3.8 GB / 6 GB).
  - Qwen3-Embedding-0.6B offline encoding confirmed with `HF_HUB_OFFLINE=1`.
  - PaddleOCR offline inference confirmed with `enable_mkldnn=False` and `use_textline_orientation=True`.
  - Gemma 4 E4B live multimodal inference confirmed on `demo_inspection_photo.png` (passed in 24.91s).
  - SEC-01 & SEC-02 verified: Startup enforcement rejects non-loopback hosts (`0.0.0.0` or external IPs) and external Ollama URLs, setting mandatory offline environment flags.
  - SEC-08 verified: Sandboxed code network access attempt fails in `--network=none`.
  - SEC-09 verified: Sandboxed infinite loop killed at wall-clock timeout (status `timeout`, exit code 124).
  - SEC-10 verified: Sandboxed memory bomb exceeding 512 MB fails safely.
  - SEC-11 verified: Segregation of duties strictly enforced. The artifact author cannot approve their own artifact (403 Forbidden). Admin cannot approve artifacts (403 Forbidden). Only designated non-author reviewers can approve or reject deliverables.
  - SEC-14 verified: Append-only hash-chained audit trail confirms cryptographic integrity.
  - SEC-15 verified: Formula injection attempts (`=HYPERLINK(...)`, `=cmd|...`, `@SUM(...)`, `+1000`) in XLSX are safely escaped with `'` so Excel stores them strictly as text without formula execution.
  - SEC-19 verified: Auditor role is strictly prohibited from downloading deliverable artifacts (403 Forbidden).
  - SEC-20 verified: Reviewer role cannot access or download deliverable artifacts assigned to another reviewer (403 Forbidden).
  - SEC-23 verified: Office packages are scanned for external relationships (`TargetMode="External"`) in `.rels` files and embedded OLE/binary objects, failing validation if detected.
  - Approval Note template & generator enforce separate Facts vs Recommendations sections, mandatory source references on all findings, mandatory limitation notes on visual observations, and a blank human review & sign-off gate.
  - Evaluation Matrix: All 16 checks (EV-01 through EV-16) pass in `docs/evidence/eval_report.md` (100.0%).
  - CI Pipeline: `scripts/check_all.ps1` and `scripts/check_all.sh` run all 5 verification phases without failure.
  - Static egress scanner (`scripts/scan_egress.py`) confirmed CLEAN with 0 findings across 115 scanned files (zero external URLs, zero CDNs, zero telemetry).




