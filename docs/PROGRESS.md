# Sovereign AI Workbench — Progress Log

## Phase Checklist

- [x] **Phase 0** — Preflight, scaffold, env, model check
- [x] **Phase 1** — Config, model registry, Ollama client
- [x] **Phase 2** — Database, auth, RBAC, audit core
- [x] **Phase 3** — Minimal LangGraph agent + first tool + SSE
- [x] **Phase 4** — RAG ingestion + retrieval with access control
- [x] **Phase 5** — PDF parsing + OCR
- [ ] **Phase 6** — Vision tool (Gemma 4 E4B)
- [ ] **Phase 7** — Router + registry-driven model selection
- [ ] **Phase 8** — Calculator + Docker sandbox + coding loop
- [ ] **Phase 9** — Deliverable generators + validation
- [ ] **Phase 10** — Inspection workflow + human review gate
- [ ] **Phase 11** — React frontend
- [ ] **Phase 12** — Sovereignty panel + egress scan + offline proof
- [ ] **Phase 13** — Test suite, evaluation harness, benchmarks
- [ ] **Phase 14** — Packaging, start scripts, demo data, README
- [ ] **Phase 15 (Future)** — Optional third model route (Bonsai 2 27B; post-MVP)

---

## Current Status
- **Active Phase**: Phase 5 Complete (Ready for Phase 6)
- **Completed**:
  - Phase 0 (Scaffolding, environment, dependencies, Ollama model validation, Qwen & Gemma benchmarks, offline weights verified)
  - Phase 1 (config.py, registry.yaml, registry.py, ollama_client.py, selfcheck.py, backend/main.py with /api/health + /api/models + /api/models/reload, 20 tests all passing)
  - Phase 2 (SQLite DB schema §13, Argon2id auth + HMAC session signing, RBAC + clearance hierarchy §5, segregation of duties SEC-11, safe_path SEC-06, append-only hash chain audit log SEC-14, CSP/CSRF/CORS/rate-limiting middleware SEC-17, user seed script, 91/91 tests passing)
  - Phase 3 (AgentState and sub-models §6.2, @audited_tool registry §7.2, safe read_file and write_file §7.3, prompt delimiters and JSON schemas §6.4, LangGraph StateGraph with bounded retries §6.1, EventBroker and task_events DB persistence §6.6, /api/tasks CRUD and SSE streaming endpoints, static egress scanner scripts/scan_egress.py §3.6, 110/110 tests all passing)
  - Phase 4 (Document chunking §8.3 with paragraph/heading & table headers, multi-format parsers PDF/DOCX/XLSX/PPTX §8.4, offline CPU SentenceTransformer embeddings, persistent ChromaDB with telemetry OFF, server-side retrieval clearance filter SEC-04, version superseding SEC-05, audited search_knowledge tool §7.3, KB REST APIs §8, synthetic SOP dataset seeder scripts/make_demo_data.py, 118/118 tests all passing)
  - Phase 5 (Deterministic OCR tool `tools/ocr.py` with PyMuPDF native text detection, scanned page rendering at 150-200 DPI, PaddleOCR CPU inference with `enable_mkldnn=False`, embedded raster image extraction `page_X_image_Y.png`, upload endpoint `/api/files/upload` with SEC-07 validation, magic-byte inspection, decompression bomb protection, PDF page limits, RAG OCR ingestion fallback, synthetic scanned inspection report generator, 131/131 tests all passing)
- **Deviations**: None.
- **Decisions & Notes**:
  - `qwen3.5:4b` (3.4 GB) and `gemma4:e4b` (9.6 GB) verified on Ollama 0.34.2.
  - VRAM fit verified on RTX 3050 Laptop GPU (peak ~3.8 GB / 6 GB).
  - Qwen3-Embedding-0.6B offline encoding confirmed with `HF_HUB_OFFLINE=1`.
  - PaddleOCR offline inference confirmed with `enable_mkldnn=False` and `use_textline_orientation=True`.
  - Phase 1: 20/20 tests pass.
  - Phase 2: 91/91 tests pass.
  - Phase 3: 110/110 tests pass.
  - Phase 4: 118/118 tests pass.
  - Phase 5: 131/131 tests pass across unit, security, and integration suites (`test_upload_validation.py`, `test_tools_ocr.py`).
  - SEC-07 verified: renamed `.exe` files, forbidden extensions (`.bat`, `.xlsm`, `.zip`), oversized uploads, and decompression bomb images are strictly rejected.
  - Scanned PDF OCR text extraction and embedded image extraction verified on synthetic demo inspection report.
  - Static egress scanner (`scripts/scan_egress.py`) confirmed CLEAN with 0 findings across 52 scanned files.


