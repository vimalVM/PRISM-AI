# 04 — Antigravity Build Plan

**Product:** Sovereign AI Workbench
**Use:** Give this file (plus the other 5 docs) to the Antigravity agent. Build **one phase at a time**. Do not start a phase until the previous phase's acceptance checks pass.
**Related:** `AGENTS.md` (rules), `01_PRD.md` (what), `02_DESIGN_DOC.md` (how), `03_SECURITY_AND_ACCESS.md` (controls), `05_TEST_EVAL_DEMO.md` (tests + demo)

---

## 0. How to use this plan in Antigravity

1. Create the repo folder `sovereign-ai-workbench/`. Put `AGENTS.md` at the root and the other five docs in `docs/`.
2. Open the folder as a workspace in Antigravity.
3. Start a new agent task with this first message:

> **Kick-off prompt (paste once):**
> "Read `AGENTS.md`, then `docs/01_PRD.md`, `docs/02_DESIGN_DOC.md`, `docs/03_SECURITY_AND_ACCESS.md`, `docs/04_ANTIGRAVITY_BUILD_PLAN.md` and `docs/05_TEST_EVAL_DEMO.md` fully. Do not write code yet. Summarise in 15 lines: the goal, the fixed stack, the forbidden technologies, and the phase list. Create `docs/PROGRESS.md` with a checklist of all phases. Then wait for me to say 'start phase N'."

4. For each phase, paste the phase prompt below ("start phase N"). Ask the agent to **plan first**, then implement, then run tests, then report.
5. After each phase, review the diff, run the acceptance checks yourself, tick the box in `docs/PROGRESS.md`, and commit (`phase-N: …`).
6. Use synthetic data only. The IDE agent is an online development tool; the **product** must never call out at runtime.
7. **Forbidden (repeat to the agent if it drifts):** Open WebUI, n8n, Streamlit, Gradio, LangSmith, any cloud AI API, CDN assets, telemetry.

### Phase overview

| Phase | Name | Milestone |
|---|---|---|
| 0 | Preflight, scaffold, env, model check | M1 |
| 1 | Config, model registry, Ollama client | M1 |
| 2 | Database, auth, RBAC, audit core | M1 |
| 3 | Minimal LangGraph agent + first tool + SSE | M2 |
| 4 | RAG ingestion + retrieval with access control | M2 |
| 5 | PDF parsing + OCR | M3 |
| 6 | Vision tool (Gemma 4 E4B) | M3 |
| 7 | Router + registry-driven model selection | M3 |
| 8 | Calculator + Docker sandbox + coding loop | M4 |
| 9 | Deliverable generators + validation | M4 |
| 10 | Inspection workflow + human review gate | M5 |
| 11 | React frontend | M6 |
| 12 | Sovereignty panel + egress scan + offline proof | M6 |
| 13 | Test suite, evaluation harness, benchmarks | M6 |
| 14 | Packaging, start scripts, demo data, README | M6 |
| 15 | **FUTURE (post-MVP, on human approval only):** Bonsai 2 27B third route, see `06_FUTURE_ENHANCEMENTS.md` | Future |

---

## Phase 0 — Preflight, scaffold, environment, model verification

**Goal:** a clean repo, working local models, and verified package / model names (the blueprint says to verify them). **Needs internet (install time only).**

**Tasks**
1. Create folder structure from `AGENTS.md` §6 (empty packages with `__init__.py`, `.gitignore` incl. `data/`, `logs/`, `.env`, `node_modules/`, `wheelhouse/`).
2. Create Python 3.11+ virtual env; create `requirements.txt` from `02_DESIGN_DOC.md` §3.3; install; then pin versions (`pip freeze` into `requirements.lock.txt`).
3. Install / check **Ollama >= v0.20.0** (`ollama --version`).
4. The human has already pulled both models (`qwen3.5:4b`, `gemma4:e4b`) with Ollama 0.34.2. **Do not re-download.** Verify with `ollama list`, record `ollama show <tag>` output (size, quantisation, digest) in `docs/evidence/models.txt`. If a tag is missing, **stop and ask the human**. Also test with `--think=false` and record tokens/s for thinking on vs off.
5. Verify local inference: `ollama run qwen3.5:4b "Say hello"`; test Gemma with a sample image via the Ollama API.
6. Benchmark quick smoke test on the target laptop (RTX 3050 6 GB / 16 GB RAM): tokens/s, VRAM (`nvidia-smi`), load time for each model **one at a time**. Save to `docs/evidence/benchmark_phase0.md`. If Gemma 4 E4B spills to RAM heavily, note the quantisation / context settings to try.
7. Download the embedding model (Qwen3-Embedding-0.6B) into `data/models/` and PaddleOCR weights (run one OCR call to cache them). Confirm they load with `HF_HUB_OFFLINE=1`.
8. Build the Docker sandbox image placeholder (Phase 8 finishes it); confirm `docker run --rm hello-world` works.
9. Node 20+ and `npm` check (build time only).
10. Create `.env.example`, `docs/PROGRESS.md`, `docs/LICENSES.md` (model + library licences).

**Prompt to paste**
> "Start phase 0 from `docs/04_ANTIGRAVITY_BUILD_PLAN.md`. Plan first. Create the scaffold, pin dependencies, verify Ollama and both model tags, cache embedding + OCR weights, and write the evidence files. If any model tag or package is not found, stop and ask me. Do not add forbidden technologies."

**Acceptance**
- [ ] `ollama list` shows `qwen3.5:4b` and `gemma4:e4b`.
- [ ] Both models answer a prompt locally.
- [ ] Embedding + PaddleOCR load with offline flags.
- [ ] `docs/evidence/models.txt` and `benchmark_phase0.md` exist.

---

## Phase 1 — Config, model registry, Ollama client

**Tasks**
1. `backend/core/config.py` (pydantic-settings) with all keys from `02` §15. Refuse non-loopback hosts unless `ALLOW_LAN=true`.
2. `models/registry.yaml` exactly as `02` §4.2; loader + Pydantic validation in `models/registry.py`; skip `enabled:false` models; expose `resolve(rule_facts)`.
3. `models/ollama_client.py`: thin wrapper over the local Ollama API (`chat`, `generate`, `list`, `ps`, image input) with timeouts, retries (bounded), model-load handling, streaming support, a `think` option read from the registry (default `false`; thinking text is never surfaced or logged), and a check that refuses non-loopback base URLs and `:cloud` tags.
4. Startup self-checks (`02` §17.3) in `backend/core/selfcheck.py`.
5. Minimal `backend/main.py` with `/api/health` and `/api/models`.

**Prompt**
> "Start phase 1. Implement config, the model registry loader, the Ollama client with safety checks, and startup self-checks. Add pytest tests: registry loads, disabled models skipped, non-loopback URL rejected, `:cloud` tag rejected."

**Acceptance**
- [ ] `pytest tests/test_registry.py tests/test_ollama_client.py` passes.
- [ ] `GET /api/models` returns both models with health.
- [ ] Editing `registry.yaml` changes results without code change.

---

## Phase 2 — Database, authentication, RBAC, audit core

> Done **before** tools so every later action is audited and access-controlled.

**Tasks**
1. `backend/core/db.py` (SQLAlchemy 2 + SQLite) with tables from `02` §13; simple migration script.
2. `core/security.py`: Argon2id hashing, session cookie (HttpOnly, SameSite=Strict, TTL), first-run secret key generation into `data/secrets/`, login lockout.
3. `core/rbac.py`: roles, clearance enum, `require_role`, `require_clearance`, ownership helpers, permission matrix from `03` §5.3 as data + tests.
4. `core/audit.py`: append-only audit with hash chain, JSONL mirror, `verify_chain()`, content-free details.
5. `core/paths.py`: `safe_path()` per `03` §7.1.
6. API: `/auth/login`, `/auth/logout`, `/auth/me`, `/users` (admin), `/audit`, `/audit/verify`, `/audit/export`.
7. `scripts/seed_users.py` (prompted passwords, never hard-coded): creates admin, engineer, reviewer, auditor demo users.
8. Security middleware: CORS allowlist, CSP + headers, CSRF header check, rate limiting.

**Prompt**
> "Start phase 2. Implement DB, auth, RBAC, audit with hash chain, `safe_path`, security middleware and the seed script exactly per docs 02 and 03. Write tests for every row of the permission matrix, lockout after 5 failures, path traversal rejection, and audit tamper detection."

**Acceptance**
- [ ] SEC-06, SEC-11 (stub), SEC-12, SEC-13, SEC-14, SEC-17 tests pass.
- [ ] No password or key appears in git, logs, or source.
- [ ] Audit rows contain no document text.

---

## Phase 3 — Minimal LangGraph agent, tool registry, first tool, SSE

**Tasks**
1. `agent/state.py` (`AgentState`, Pydantic sub-models).
2. `tools/registry.py`: `@audited_tool`, `ToolContext`, timeouts, role check, audit start / end.
3. `tools/files.py`: `read_file`, `write_file` (allowlists via `safe_path`).
4. `agent/graph.py`: nodes `intake → plan → execute → observe → validate → finalize`, with `revise` and bounded retries; plan validated against the tool registry.
5. `agent/prompts.py`: system prompt, untrusted-content delimiters, JSON schemas.
6. `backend/api/tasks.py`: `POST /tasks`, `GET /tasks/{id}`, `GET /tasks/{id}/events` (SSE via `sse-starlette`); background task runner; cancel.
7. `task_events` persistence and event emitter.

**Prompt**
> "Start phase 3. Build the minimal LangGraph agent with Qwen3.5 (default model from registry), the audited tool registry, `read_file` and `write_file`, and the SSE events endpoint. The planner must output strict JSON and reject unknown tools. Add tests with a fake Ollama client so tests run without GPU."

**Acceptance**
- [ ] A request "read this file and summarise it" runs INTAKE→…→FINALIZE and streams events.
- [ ] Every tool call has an audit record.
- [ ] Forced failure stops after `MAX_AGENT_RETRIES`.
- [ ] Unknown tool in plan is rejected.
- [ ] `scripts/scan_egress.py` (first version) runs clean.

---

## Phase 4 — RAG ingestion and retrieval with access control

**Tasks**
1. `rag/chunking.py`: paragraph / heading aware chunks (600–800 tokens, 80–100 overlap), table chunks with repeated header.
2. `rag/ingest.py`: parsers — PDF (PyMuPDF; scanned pages later via OCR in Phase 5), DOCX (python-docx), XLSX (openpyxl), PPTX (python-pptx); metadata (`filename, doc_id, page, section, doc_version, classification, content_hash, superseded`); embeddings from local model (CPU); Chroma persistent client with telemetry off.
3. Version handling: re-index marks old chunks superseded.
4. `rag/retrieve.py`: server-side `where` filter from session user (`02` §8.5), top-k, citations.
5. `tools/rag.py`: `search_knowledge`.
6. API: `/kb/documents` (POST / GET / DELETE / reindex), `/kb/search`.
7. RAG answer prompt with citations; validator that all citations map to retrieved chunk ids.

**Prompt**
> "Start phase 4. Implement RAG per doc 02 §8 and doc 03 §6. Access filtering must be in the vector query and derived from the authenticated user only. Create a synthetic SOP set (4 short documents with different classifications) via `scripts/make_demo_data.py`. Write tests: INTERNAL user gets zero RESTRICTED chunks even when the query matches exactly; version change supersedes old chunks; citations map to real chunks."

**Acceptance**
- [ ] SEC-04 and SEC-05 (RAG part) pass.
- [ ] Q&A over the synthetic SOP returns cited answers with document + page.
- [ ] No embeddings / vector calls leave localhost (egress scan clean).

---

## Phase 5 — PDF parsing and OCR

**Tasks**
1. `tools/ocr.py`: `ocr_document` — PyMuPDF native text; scanned-page detection (chars/page threshold); render 200–300 DPI; PaddleOCR (CPU) with Tesseract fallback; results with page refs and confidence; cache by file hash.
2. Extract embedded images from PDF pages (for Phase 6) with names like `page_7_image_1`.
3. Upload endpoint `/files/upload` with validation from `03` §7.2 (extension, magic bytes, size, pages, pixel limits, UUID names, SHA-256).
4. Integrate scanned pages into RAG ingestion (OCR fallback).
5. `scripts/make_demo_data.py` extension: generate a synthetic **scanned-style** inspection report PDF (image-only pages with typed text rendered as image + a placeholder photo).

**Prompt**
> "Start phase 5. Implement `ocr_document`, embedded-image extraction, and the validated upload endpoint. OCR must run with the network disabled. Return text with page numbers. Add tests using the synthetic scanned PDF and malicious upload cases (renamed exe, oversize, bomb image)."

**Acceptance**
- [ ] OCR text returned with correct page refs for the scanned demo PDF.
- [ ] SEC-07 passes.
- [ ] OCR runs offline (verified with firewall on).

---

## Phase 6 — Vision tool (Gemma 4 E4B)

**Tasks**
1. `tools/vision.py`: `vision_analyze(image_ref, question?)` — downscale to max edge (e.g. 1280 px), send to `vision` model from registry, strict JSON schema output (`02` §9.3), mandatory `limitation`, `type` observed / inferred; repair-retry once on invalid JSON.
2. Batch mode: analyse all images of a run together to minimise model swaps.
3. Prompt for vision includes the safety boundary; output never called "measurement".
4. Validator rejects observations without `limitation`.
5. Handle vision failure (mark evidence unavailable; use fallback only if enabled).

**Prompt**
> "Start phase 6. Implement `vision_analyze` with Gemma 4 E4B through the registry, strict JSON output, mandatory limitation field, batching, and failure handling. Tests use a fake client plus one live smoke test marked `@pytest.mark.live_model`."

**Acceptance**
- [ ] Demo photo returns valid `VisualObservation[]` with `limitation` and `type`.
- [ ] Invalid JSON is repaired once, else safely reported.
- [ ] Audit shows model = `gemma4:e4b`.

---

## Phase 7 — Router and registry-driven model selection

**Tasks**
1. `agent/router.py` implementing `02` §5 (facts → first matching rule → plan; skip disabled; audit `model_route` with rule name + reason).
2. INTAKE classification: deterministic file / keyword rules first; LLM JSON fallback.
3. Wire router into the graph: text → Qwen; image → Gemma; scanned → OCR + Gemma → Qwen.
4. Model swap manager: group vision calls, unload / load using Ollama `keep_alive`, expose current loaded model to UI.
5. `POST /models/reload` (admin) to reload registry.

**Prompt**
> "Start phase 7. Implement the config-driven router and integrate it with the graph. Add tests for the three model-selection examples in doc 01 §9, for a disabled model being skipped, and for adding a new model via registry only."

**Acceptance**
- [ ] "Summarize this SOP" → Qwen; photo → Gemma → Qwen; scanned report → OCR+Gemma → Qwen.
- [ ] Each route is in the audit log with reason.
- [ ] Enabling `future_strong_reasoning` requires no code change.

---

## Phase 8 — Calculator, Docker sandbox, coding agent loop

**Tasks**
1. `tools/calculator.py`: safe AST evaluator (allowlisted nodes / functions), magnitude limits, returns `{inputs, formula, result, assumptions}`.
2. `docker/sandbox/Dockerfile` (minimal, non-root, pytest; no compilers / curl / git); build script; `docker save` for offline reload.
3. `tools/sandbox.py`: `run_code` using docker SDK with all flags from `03` §8; wall-clock kill; output cap; per-run temp dir; cleanup.
4. Coding workflow in graph: plan → generate code + tests → run → observe → bounded fix loop → package (`src/`, `tests/`, `README.md`, `RESULT.txt`).
5. Static denylist scan of generated code (report only).

**Prompt**
> "Start phase 8. Implement the safe calculator, the Docker sandbox tool with all hardening flags, and the coding-agent loop with bounded corrections. Write tests SEC-08, SEC-09, SEC-10 (network attempt, infinite loop, memory bomb) and a calculator fuzz test (no eval, no attribute access, `9**9**9` rejected)."

**Acceptance**
- [ ] Demo B: a coding task passes tests in the sandbox and returns a code package.
- [ ] A failing first attempt triggers exactly one bounded correction cycle.
- [ ] SEC-08/09/10 pass.

---

## Phase 9 — Deliverable generators and validation

**Tasks**
1. Create `templates/approval_note.docx`, `templates/report.docx`, `templates/presentation.pptx` (simple, professional; `{{placeholders}}`).
2. `tools/documents.py`: `create_docx`, `create_xlsx`, `create_pptx` per `02` §10.
3. Validation library `agent/nodes/validate.py` with all checks from `02` §10.3 and `03` §11 (placeholders, source refs, re-open, macro-free, external relationships, formula sanitising, checksums).
4. Artifact records + `/artifacts` endpoints + download with `Content-Disposition: attachment`.
5. Calculation report generation (DOCX / XLSX) with inputs, formula, result, assumptions.

**Prompt**
> "Start phase 9. Build the three templates and generators, the validation checks, and the artifact API. Approval note must have separate Facts and Recommendations sections, source refs on every finding, an Observed/Inferred tag on visual items, and a blank human-review section. Add tests SEC-15 (formula injection) and template placeholder leftovers."

**Acceptance**
- [ ] DOCX / XLSX / PPTX open and contain required sections.
- [ ] Validation fails when a source ref or field is missing.
- [ ] No macro formats or external relationships in outputs.

---

## Phase 10 — Inspection workflow (Demo A) + human review gate

**Tasks**
1. Inspection graph path: upload → classify (scanned / native / images) → OCR (CPU) → vision batch (Gemma) → extract facts (Qwen, JSON) → RAG on SOP → compare findings vs guidance → optional `calculate` → draft note (facts vs recommendations) → `create_docx` → validate → `review_gate`.
2. `review_gate` node sets `PENDING_REVIEW`; the graph has **no** path to APPROVED.
3. Review API: `/review/queue`, `/artifacts/{id}/review` with segregation of duties (`03` §5.3, §10).
4. Full audit trail linking run → model calls → tool calls → artifact → review.

**Prompt**
> "Start phase 10. Implement the full Demo A workflow per doc 01 §9 and doc 02 §9.4, plus the human review gate and review API. Run it end-to-end on the synthetic scanned inspection report and the synthetic SOP KB with the network disabled. Provide a test that proves an author cannot approve their own artifact and that the agent cannot set APPROVED."

**Acceptance**
- [ ] `Inspection_Approval_Note.docx` produced with all sections, citations, and human-review block.
- [ ] Numeric calculation done by `calculate`, not by the model.
- [ ] SEC-11 passes. Audit trail complete.
- [ ] Run works offline.

---

## Phase 11 — React frontend

**Tasks** (pages and components in `02` §14)
1. Vite + React + TypeScript + Tailwind; local fonts; icons via `lucide-react`; **no CDN / external URLs**.
2. Auth flow (login, session, `RoleGuard`).
3. **Workbench**: chat, file dropzone, task hint, live `WorkflowTimeline` (SSE), `ModelBadge` with route reason, `EvidencePanel` (Sources / OCR / Vision / Calculations), artifacts card with validation checklist.
4. Run detail page, Artifacts page, Review queue + `ReviewForm`, Knowledge Base page, Models page, Audit page, Users page, Sovereignty page (Phase 12 fills data).
5. UX rules from `02` §14.5 (observed / inferred tags, AI-draft label, vision notice, confirm dialogs, empty / loading / error states, keyboard access).
6. Theme tokens in `theme.css` (dark + light).
7. Build to `frontend/dist`; FastAPI serves it; dev proxy for Vite.
8. Frontend tests with Vitest for timeline, role guard, evidence panel.

**Prompt**
> "Start phase 11. Build the React frontend per doc 02 §14 with a distinct, professional dark 'control room' theme (navy + amber, tokens in theme.css). Everything must be bundled locally, with no external URLs. After building, use the browser to verify: login as each role, run Demo A from the UI, watch the timeline, open evidence, download the DOCX, review as reviewer. Report any UI defects and fix them."

**Acceptance**
- [ ] All roles see only their permitted pages.
- [ ] Demo A, B, C can be run entirely from the UI.
- [ ] Built bundle contains no external URLs (`scan_egress.py`).
- [ ] Keyboard navigation works on main flows.

---

## Phase 12 — Sovereignty panel, egress scan, offline proof

**Tasks**
1. `backend/api/system.py`: `/system/status` (models, bind addresses, offline flags, last scan result), `/system/connections` (passive `psutil` check of workbench processes for non-loopback sockets), optional active egress probe (disabled by default).
2. Finalise `scripts/scan_egress.py` (`03` §3.6) including built frontend bundle and forbidden tech names.
3. `scripts/offline_proof.md` (or `.ps1`): step-by-step evidence capture (`03` §3.5, §15) and folder `docs/evidence/`.
4. Sovereignty page complete in UI.
5. Startup enforcement (`03` §3.3).

**Prompt**
> "Start phase 12. Implement the sovereignty status endpoints, the passive connection check, the final egress scan, startup enforcement, and the Sovereignty page. Then write `docs/evidence/README.md` explaining how to capture Wireshark and firewall evidence. Do NOT run any active outbound probe."

**Acceptance**
- [ ] Sovereignty page shows 0 non-loopback connections while running Demo A.
- [ ] `scan_egress.py` clean, exit code 0.
- [ ] Backend refuses non-loopback bind or `:cloud` model.

---

## Phase 13 — Test suite, evaluation harness, benchmarks

**Tasks**
1. Complete unit / integration tests per `05` §2–§4. Mark GPU tests with `@pytest.mark.live_model`.
2. `scripts/eval_run.py`: runs the evaluation plan (`05` §1) and writes `docs/evidence/eval_report.md` with pass / fail per row.
3. `scripts/benchmark.py`: tokens/s, TTFT, VRAM, model load time, Demo A wall-clock; results saved.
4. Add a CI-style script `scripts/check_all.sh|ps1`: ruff, pytest, vitest, egress scan.

**Prompt**
> "Start phase 13. Complete the test suite and the evaluation harness so that every row of the evaluation table in doc 05 has an automated or scripted check with a pass / fail result, and generate `docs/evidence/eval_report.md`. Add the benchmark script and run it."

**Acceptance**
- [ ] `check_all` passes.
- [ ] `eval_report.md` shows all P0 rows passing.
- [ ] Benchmark numbers recorded for the target laptop.

---

## Phase 14 — Packaging, start scripts, demo data, README

**Tasks**
1. `scripts/start.ps1` and `scripts/start.sh`: set offline env flags, verify Ollama, warm both models (tiny prompt each, one at a time), start FastAPI on 127.0.0.1, open browser.
2. `scripts/package_offline.*`: wheelhouse, `docker save`, list of model files, checksum manifest.
3. Demo data: synthetic SOP KB, synthetic scanned inspection report, photo placeholder instructions, coding task prompts, demo users (from seed script).
4. `README.md`: prerequisites, one-command start, offline instructions, demo script link, troubleshooting (VRAM, model tags, Docker, Paddle).
5. Final pass on `docs/LICENSES.md`, `docs/PROGRESS.md`.
6. Rehearsal: run the 5–7 min demo from `05` §6 twice with network disabled; record fallback video.

**Prompt**
> "Start phase 14. Create start and packaging scripts, demo data, and the README. Then run the full demo script from doc 05 §6 twice with the network disabled and report timings and any failures. Fix failures."

**Acceptance**
- [ ] One command starts the whole system offline.
- [ ] Demo script completes within 7 minutes.
- [ ] Definition of Done in `AGENTS.md` §7 is fully ticked.

---

## Phase 15 — FUTURE: optional third model route (Bonsai 2 27B)

**Do not start this phase** until Phases 0–14 are done, the Definition of Done in `AGENTS.md` §7 is ticked, and the human says "start phase 15". Full design, security changes, tests and the go / no-go benchmark gate are in `docs/06_FUTURE_ENHANCEMENTS.md`. The core system (Qwen3.5 4B + Gemma 4 E4B) must stay unchanged and fully working with the new route disabled.

---

## Appendix A — Reusable prompts

**Drift correction**
> "You added <X>. `AGENTS.md` forbids Open WebUI, n8n, Streamlit, Gradio, LangSmith, cloud APIs and CDNs. Remove it and use the stack in AGENTS.md §3. Re-run the egress scan."

**Security review at end of each phase**
> "Review this phase against `docs/03_SECURITY_AND_ACCESS.md`. List each control that applies, show where it is implemented and the test that proves it. Fix gaps."

**When a model is too weak**
> "Do not switch models silently. Improve prompts, reduce context, add a deterministic tool, or add a validator. If still failing, report to me with the failing example."

**Stuck / VRAM problems**
> "Report `nvidia-smi`, `ollama ps` and settings used. Try: smaller `num_ctx`, one model resident, batch vision calls, CPU for OCR and embeddings. Then report."

## Appendix B — Order-of-work rationale
Auth, RBAC and audit come before tools so no tool exists un-audited. RAG comes before OCR / vision so the knowledge base and access filter are proven early. The router comes after both models work individually. The frontend comes after the API stabilises. Sovereignty proof and packaging come last because they verify the finished system.

## Appendix C — Coverage check (blueprint → phase)
| Blueprint area | Phase |
|---|---|
| Model architecture, registry, upgrade strategy | 1, 7 |
| Ollama local API | 0, 1 |
| LangGraph agent, state, bounded retries | 3 |
| Local tool layer (10 tools) | 3, 4, 5, 6, 8, 9 |
| RAG + citations + access control | 4 |
| OCR / PDF / multimodal | 5, 6 |
| Router / model auto-selection | 7 |
| Code sandbox / coding agent | 8 |
| DOCX / XLSX / PPTX deliverables | 9 |
| Demo A / B / C | 10, 8, 6 |
| Security controls | 2, 8, 9, 12 |
| Sovereignty proof | 12 |
| UI (React + FastAPI) | 11 |
| Evaluation plan | 13 |
| Known limitations | UI notices (11), README (14) |
| Hackathon demo | 14 |
