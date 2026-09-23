# AGENTS.md — Sovereign AI Workbench (READ THIS FIRST)

> This file is the master rulebook for any AI coding agent (Antigravity) building this repository.
> Place it at the **repo root**. Put the other five docs in `docs/`.
> If your Antigravity version supports workspace rules (for example an `.agent/rules/` folder), copy Section 2 and Section 5 into a rule file too, so they are always in context.

---

## 1. What we are building (one paragraph)

**Sovereign AI Workbench** is a self-hosted, air-gapped, agentic AI workbench for confidential industrial / government knowledge work. It runs entirely on one local workstation. Two local open-weight models are served by **Ollama**: **Qwen3.5 4B** (primary: reasoning, planning, tool use, coding, RAG answers, deliverable drafting) and **Gemma 4 E4B** (specialised multimodal / vision). **LangGraph** orchestrates the agent and routes each task to the right model. The system uses local RAG (ChromaDB), OCR (PaddleOCR), a Docker code sandbox, and generates real **DOCX / XLSX / PPTX / code** deliverables. The UI is **React** (frontend) + **FastAPI** (backend). The "nothing leaves the premises" claim must be **provable** (network isolation, local logs, Wireshark / firewall evidence).

**Scope note:** this is a hackathon / prototype. It is NOT authorised for safety-critical engineering, financial, legal or defence decisions. Human approval and validation are mandatory.

**Core principle:** the LLM is the reasoning / orchestration component. It is NOT the calculator, database, OCR engine, code executor or file generator. Deterministic tools do deterministic work; RAG supplies organisation-specific knowledge.

---

## 2. HARD CONSTRAINTS (never violate)

### 2.1 Technologies that are FORBIDDEN in this project

| Forbidden | Why / what to use instead |
|---|---|
| **Open WebUI** | Not used. The UI is our own React app. Do not install, embed, reference or mention it as an option. |
| **n8n** | Not used. LangGraph does all orchestration. No n8n container, no webhooks, no n8n docs links. |
| **Streamlit / Gradio** | The source blueprint has leftover Streamlit references (`ui.py`, `pip install streamlit`). Ignore them. UI = React + FastAPI only. |
| **LangSmith / LangFuse cloud / any hosted tracing** | Breaks air-gap. Use local audit log (SQLite + JSONL). |
| **Any cloud LLM API** (OpenAI, Anthropic, Google, Azure, Cohere, Mistral API, etc.) | All inference is local via Ollama on `127.0.0.1`. No API keys anywhere. |
| **Cloud embeddings / rerankers / OCR / vector DB / logging / storage** | Use local sentence-transformers, ChromaDB (persistent local), PaddleOCR, SQLite, local disk. |
| **CDN assets** (Google Fonts, cdnjs, unpkg, jsDelivr, Font Awesome CDN, etc.) | All fonts, icons, JS, CSS must be bundled locally. |
| **Analytics / telemetry / crash reporters** (Sentry, GA, PostHog, Chroma telemetry, etc.) | Disable or do not include. |

### 2.2 Behaviour rules
1. **Localhost only.** Bind FastAPI to `127.0.0.1`, Ollama to `127.0.0.1:11434`, ChromaDB embedded (no network server).
2. **No runtime internet.** After installation, the app must work with the network disabled. Models, OCR weights and embedding weights must be present on local disk.
3. **No secrets in code, prompts or logs.** Secrets are generated at first run and stored under `data/secrets/` (git-ignored).
4. **No `eval()` / `exec()` / `subprocess(shell=True)` on model-generated content** outside the Docker sandbox. Arithmetic uses a safe AST evaluator.
5. **Every file path** goes through `core/paths.safe_path()` (allowlist + normalisation + `..` rejection).
6. **Every tool call and model route is audited** through the `@audited_tool` decorator / audit service.
7. **RAG access control is enforced at retrieval time** in `rag/retrieve.py` (server side), never only in the UI and never by the model.
8. **Human confirmation** is required before final approval, deletion, or any external-system change. The agent can never approve its own output.
9. **Bounded retries.** No unbounded agent loops. `MAX_AGENT_RETRIES` (default 3) and `MAX_TOOL_STEPS` (default 25) come from config.
10. **Config over hard-coding.** Model names, capabilities and routing rules live in `models/registry.yaml`. Adding a model must not require changing the LangGraph state machine.
11. **Do not add a dependency** that is not listed in `docs/02_DESIGN_DOC.md` Section 3 without recording the reason in `docs/PROGRESS.md`, and never add one that phones home.
12. **Never present visual-model output as measured fact.** Vision output is "observation", labelled `observed` vs `inferred`, with a limitation note.

---

## 3. Fixed technology stack

| Layer | Technology |
|---|---|
| Local inference server | **Ollama** (>= v0.20.0; needed for Gemma 4) |
| Primary model | **Qwen3.5 4B** — Ollama tag `qwen3.5:4b` |
| Vision / multimodal model | **Gemma 4 E4B** — Ollama tag `gemma4:e4b` |
| Agent orchestration | **LangGraph** (+ `langchain-ollama`, `langchain-core`) |
| RAG | Custom Python or LangChain components |
| Vector DB | **ChromaDB** (persistent, local, telemetry OFF) |
| Embeddings | Local **Qwen3-Embedding-0.6B** via `sentence-transformers` (config-driven; any small local embedder can replace it) |
| OCR | **PaddleOCR** (Tesseract as fallback) |
| PDF parsing | **PyMuPDF** |
| Code sandbox | **Docker** (`--network=none`) |
| Calculations | Python (safe AST evaluator; data work inside sandbox) |
| Deliverables | **python-docx**, **openpyxl**, **python-pptx** |
| Backend | **FastAPI** + Uvicorn |
| Frontend | **React + TypeScript + Vite** (built and served locally) |
| App database | **SQLite** |
| Network evidence | Wireshark + OS firewall |

> **Verify before final build:** package names and Ollama model tags must be checked against official docs (tags can change). Phase 0 of the build plan does this with `ollama show` and `pip index`/`pip download` checks while still online.

---

## 4. Conflicts in the source blueprint — how they are resolved

The source file has some older text that contradicts its own "FINAL" decision. Follow this table.

| Topic | Old / conflicting text | **Decision to follow** |
|---|---|---|
| Vision model | §3, §4, §14 say Qwen3.5 handles vision | **Gemma 4 E4B is the vision model.** Qwen3.5 vision may exist only as an optional, disabled-by-default fallback in the registry. |
| Router policy | §4 routes images to `qwen3.5:4b` | Images / photos → Gemma 4 E4B. Scanned docs → PaddleOCR + Gemma 4 E4B. Text / RAG / coding → Qwen3.5 4B. |
| UI | `ui.py`, `streamlit`, Streamlit docs link | **React + FastAPI** only. |
| Open WebUI | §Design Goal says "can be added" | **Removed.** Not used. |
| n8n | "optional" | **Removed.** Not used. |
| LangSmith | "optional dev tool" | **Removed** (air-gap). |
| Router config | old `scanned_document: default` | New rules in `docs/02_DESIGN_DOC.md` §5. |
| `pip install` list | Missing `paddlepaddle`, includes `streamlit` | Use the corrected list in `docs/02_DESIGN_DOC.md` §3.3. |
| Step numbering | Lists numbered 12–47 continuously | Just an export artefact. Use phase numbers from `docs/04_...`. |

---

## 5. Working method for the Antigravity agent

1. **Read order:** `AGENTS.md` → `docs/01_PRD.md` → `docs/02_DESIGN_DOC.md` → `docs/03_SECURITY_AND_ACCESS.md` → `docs/04_ANTIGRAVITY_BUILD_PLAN.md` → `docs/05_TEST_EVAL_DEMO.md`. Also skim `docs/06_FUTURE_ENHANCEMENTS.md`, but it is **FUTURE ONLY**: do not build anything from it (for example the Bonsai 2 27B route, the `llama_cpp` provider or escalation routing) until the human says "start phase 15".
2. **Build phase by phase** exactly as in `docs/04_ANTIGRAVITY_BUILD_PLAN.md`. Each phase has acceptance criteria. **Do not start the next phase until the current one passes its tests.**
3. **Plan first.** For each phase, produce a short plan (files to create, tests to write), then implement, then run tests.
4. **Write tests with the code.** Every tool and every security control needs at least one pytest test (see `docs/05`).
5. **Keep `docs/PROGRESS.md` updated:** phase, what was done, what is left, deviations, decisions.
6. **Ask the human** (do not guess) when: a model tag is not found, hardware limits block a step, a forbidden technology seems needed, or requirements conflict.
7. **No cloud calls at runtime.** Antigravity itself is an online development tool; the *product* you build must never call out. Never put real confidential data into the IDE agent. Use synthetic demo data.
8. **Run the egress scan** (`scripts/scan_egress.py`) at the end of every phase from Phase 3 onward; it must report zero forbidden endpoints.
9. **Commit style:** small commits, message = `phase-N: what changed`.

---

## 6. Target repository layout

```
sovereign-ai-workbench/
├── AGENTS.md
├── README.md
├── docs/
│   ├── 01_PRD.md
│   ├── 02_DESIGN_DOC.md
│   ├── 03_SECURITY_AND_ACCESS.md
│   ├── 04_ANTIGRAVITY_BUILD_PLAN.md
│   ├── 05_TEST_EVAL_DEMO.md
│   └── PROGRESS.md
├── backend/                     # FastAPI app (replaces old app/ui.py + app/api.py)
│   ├── main.py                  # app factory, static serving of built frontend
│   ├── api/                     # routers: auth, files, tasks, artifacts, kb, models, audit, system
│   ├── core/                    # config, db, security, rbac, paths, audit, logging
│   └── schemas/                 # pydantic models
├── agent/
│   ├── graph.py                 # LangGraph StateGraph
│   ├── state.py                 # AgentState
│   ├── router.py                # config-driven model / task router
│   ├── prompts.py
│   └── nodes/                   # intake, plan, execute, observe, validate, finalize, review_gate
├── models/
│   ├── registry.yaml            # model names, capabilities, routing rules
│   └── ollama_client.py
├── tools/
│   ├── files.py                 # read_file, write_file
│   ├── ocr.py                   # ocr_document
│   ├── vision.py                # vision_analyze (Gemma 4 E4B)
│   ├── rag.py                   # search_knowledge
│   ├── calculator.py            # calculate
│   ├── sandbox.py               # run_code (Docker)
│   ├── documents.py             # create_docx / create_xlsx / create_pptx
│   └── registry.py              # tool registry + @audited_tool
├── rag/
│   ├── ingest.py
│   ├── retrieve.py
│   └── chunking.py
├── frontend/                    # React + TS + Vite (bundled assets only)
├── data/                        # git-ignored
│   ├── incoming/
│   ├── knowledge_base/
│   ├── outputs/
│   ├── chroma/
│   ├── db/
│   └── secrets/
├── templates/
│   ├── approval_note.docx
│   ├── report.docx
│   └── presentation.pptx
├── tests/
├── logs/
├── docker/
│   └── sandbox/                 # Dockerfile for the code sandbox image
├── scripts/                     # start, seed users, egress scan, demo data, benchmark
├── requirements.txt
└── README.md
```

---

## 7. Definition of Done (whole project)

- [ ] All P0 requirements in `docs/01_PRD.md` pass their acceptance tests.
- [ ] Demo A (scanned inspection report → approval note DOCX), Demo B (coding agent in sandbox), Demo C (multimodal) all run end-to-end **with Wi-Fi/Ethernet disabled**.
- [ ] Both models are visibly selected by the router (UI shows model + reason; audit log records it).
- [ ] Access control proven: a user without clearance cannot retrieve a restricted document, even by asking the model directly.
- [ ] Audit log shows every model route and tool call; no document contents in the log.
- [ ] `scripts/scan_egress.py` reports no cloud endpoints, no telemetry.
- [ ] Wireshark / firewall evidence captured and saved in `docs/evidence/`.
- [ ] `README.md` explains one-command offline start.
- [ ] No mention or use of Open WebUI, n8n, Streamlit, or LangSmith anywhere in code or docs (except the "forbidden" tables in these docs).
