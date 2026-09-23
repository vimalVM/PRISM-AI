# 01 — Product Requirements Document (PRD)

**Product:** Sovereign AI Workbench
**Type:** Hackathon / prototype (self-hosted, air-gapped, model-agnostic, agentic, multimodal)
**Primary model:** Qwen3.5 4B  |  **Specialised multimodal model:** Gemma 4 E4B
**UI:** React + FastAPI  |  **Orchestration:** LangGraph  |  **Serving:** Ollama
**Status:** Ready for build in Antigravity
**Related docs:** `AGENTS.md`, `02_DESIGN_DOC.md`, `03_SECURITY_AND_ACCESS.md`, `04_ANTIGRAVITY_BUILD_PLAN.md`, `05_TEST_EVAL_DEMO.md`

> Items marked **[Added]** are small additions beyond the source blueprint that are needed to make the system buildable and testable. Everything else comes directly from the blueprint.

---

## 1. Vision and summary

Industrial and government organisations do confidential knowledge work every day: approval notes, engineering calculations, internal code, scanned inspection reports, drawings, financials, vendor negotiations and internal correspondence. They want the usefulness of a modern AI assistant **without sending confidential data to any external AI provider**.

Sovereign AI Workbench is a single-machine, fully on-premises AI workbench that:

- runs all inference on the organisation's own hardware,
- works with the internet disabled,
- uses **more than one** open-weight model and **automatically selects** the right one for each task,
- acts as an **agent** (plan → call tools → observe → iterate → deliver),
- understands text, scanned documents and images locally,
- grounds answers in internal manuals / SOPs through local RAG,
- produces **real business artifacts** (DOCX, XLSX, PPTX, code), not only chat replies,
- and gives **auditable evidence** that nothing leaves the environment.

**Analogy for non-experts:** think of a secure workshop with no windows to the outside. Inside are two specialists (a "thinker" and a "looker"), a filing room (knowledge base), a calculator, a test bench (sandbox) and a printer (document generators). A supervisor (LangGraph) decides who does which job, and a logbook (audit log) records everything.

---

## 2. Problem statement

Confidential knowledge work cannot be sent to cloud AI. Existing options either leak data, or are limited to chat answers with no real deliverables, or do not prove that data stayed inside. The organisation needs a local AI system that is useful (agentic, multimodal, produces files) **and** provably sovereign.

### 2.1 The system must therefore
1. Run the inference stack on the organisation's own hardware.
2. Operate without external AI APIs and remain functional when the internet is disabled.
3. Support more than one open-weight model and route tasks by capability.
4. Act as an agent: plan, call tools, observe results, iterate and produce final deliverables.
5. Understand text, scanned documents and images locally.
6. Ground answers in internal manuals, SOPs and historical documents through local RAG.
7. Generate real business artifacts rather than only chat responses.
8. Provide auditable evidence that no confidential data is sent outside the environment.

---

## 3. Goals and non-goals

### 3.1 Goals
| ID | Goal |
|---|---|
| G1 | Fully local, self-hosted prototype on one workstation (target: RTX 3050 Laptop 6 GB VRAM, 16 GB RAM). |
| G2 | Two local models with visible automatic model selection (Qwen3.5 4B + Gemma 4 E4B). |
| G3 | Agentic multi-step workflows using LangGraph with bounded retries. |
| G4 | Local RAG with citations and access control at retrieval time. |
| G5 | Scanned PDF / image / photograph understanding (PyMuPDF + PaddleOCR + Gemma 4 E4B). |
| G6 | Real deliverables: DOCX, XLSX, PPTX, code packages, calculation reports. |
| G7 | Safe code execution in a Docker sandbox with network disabled. |
| G8 | Provable air-gap: firewall / Wireshark evidence + local audit logs. |
| G9 | Model-agnostic design: new local models can be added through configuration only. |
| G10 | Repeatable 5–7 minute hackathon demo. |

### 3.2 Non-goals
- Not a production system; not authorised for safety-critical engineering, financial, legal or defence decisions.
- Not a replacement for a large frontier model; the small models are compensated by RAG, deterministic tools, validation and iteration.
- No cloud inference, cloud embeddings, cloud OCR, cloud vector DB, cloud logging or cloud storage.
- No multi-node / clustered deployment.
- No model fine-tuning or training.
- No enterprise SSO / identity integration (listed as a production gap).
- No Open WebUI, no n8n, no Streamlit, no LangSmith (see Section 12).

---

## 4. Users and personas

| Persona | Description | Main needs |
|---|---|---|
| **Engineer / Analyst** (role `engineer`) | Uploads reports, asks questions, requests deliverables, runs coding tasks. | Fast, cited answers; real DOCX/XLSX/PPTX; code that has been tested. |
| **Reviewer / Approver** (role `reviewer`) | Senior person who reviews AI-drafted approval notes. | See sources, see facts vs recommendations, approve / reject with comments. |
| **Knowledge Admin** (role `admin`) | Manages users and the internal knowledge base. | Ingest SOPs with versions and classification; view model health. |
| **Security Auditor / IT** (role `auditor`) | Proves the system is sovereign and controlled. | Read-only audit log, network status, evidence export. |
| **Hackathon judge** | Watches a 5–7 min demo. | Clear proof of local models, routing, agent, deliverables, offline mode. |

---

## 5. Design goals table (from blueprint)

| Design Goal | Target |
|---|---|
| Deployment | Single workstation/server; entirely on premises |
| Primary LLM | Qwen3.5 4B served locally through Ollama |
| Specialised multimodal | Gemma 4 E4B served locally through Ollama |
| Agent framework | LangGraph |
| Knowledge base | Local RAG with ChromaDB + local embeddings |
| OCR / document parsing | PaddleOCR (Tesseract as fallback) + PyMuPDF |
| Code execution | Docker sandbox |
| Deliverables | DOCX, XLSX, PPTX, code and calculation reports |
| UI | **React + FastAPI** |
| Automation | LangGraph only (**no n8n**) |
| Security proof | Network isolation + local logs + Wireshark / OS firewall evidence |

---

## 6. Scope

### 6.1 P0 (must have for the demo)
Local models via Ollama; router; LangGraph agent; RAG with citations; OCR + vision pipeline; calculation tool; Docker sandbox; DOCX generation with validation; login + roles + retrieval-time access control; audit log; React UI with workflow timeline; offline proof (sovereignty panel + evidence procedure).

### 6.2 P1 (should have)
XLSX and PPTX generation; code-package artifact; model status page; audit export; review queue; knowledge-base admin page; benchmark script; egress scan script.

### 6.3 P2 (nice to have)
Optional stronger local model route (registry entry, disabled by default); audit hash-chain verification UI **[Added]**; dark/light theme toggle.

---

## 7. Functional requirements

Priority: P0 / P1 / P2. Each requirement has an acceptance test ID in `05_TEST_EVAL_DEMO.md`.

### 7.1 Model serving and routing
| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| FR-01 | Serve Qwen3.5 4B locally through Ollama on localhost. | P0 | Model answers a prompt with network disabled. |
| FR-02 | Serve Gemma 4 E4B locally through Ollama on localhost. | P0 | Model returns visual observations for a test image, network disabled. |
| FR-03 | Model registry in `models/registry.yaml` holds model names, capabilities, enabled flag and routing rules. | P0 | Changing the registry changes routing with no code change. |
| FR-04 | Router automatically selects a model by task type, modality and complexity, using configuration only. | P0 | Text→Qwen, image→Gemma, scanned doc→OCR+Gemma then Qwen. |
| FR-05 | The UI and audit log show which model was chosen and why (route reason). | P0 | Visible badge + audit record per model call. |
| FR-06 | Optional "stronger local model" route for complex tasks when hardware allows. **Future enhancement, not part of the MVP build** (planned candidate: Bonsai 2 27B; see `06_FUTURE_ENHANCEMENTS.md`). | P2 | Disabled by default; the registry slot exists, and enabling it later needs a `llama_cpp` provider plus a registry edit. |
| FR-07 | Only one large model is resident in VRAM at a time on 6 GB GPUs; loading and unloading is automatic. **[Added]** | P0 | Ollama configured with `OLLAMA_MAX_LOADED_MODELS=1`; no out-of-memory in demo. |
| FR-08 | Whole system functions with internet disabled. | P0 | Offline test passes (EV-01). |

### 7.2 Agent behaviour
| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| FR-10 | LangGraph stateful agent with nodes: INTAKE → PLAN → tool execution → OBSERVE → VALIDATE → FINALIZE (with human-review gate). | P0 | Graph trace shows nodes in order. |
| FR-11 | Agent state holds: user_request, task_type, selected_model, uploaded_files, parsed content refs, retrieved chunks + source metadata, tool results, generated artifacts, validation results, approval status, audit events, errors. | P0 | State schema test. |
| FR-12 | INTAKE classifies task, files and risk level. | P0 | Unit test with sample inputs. |
| FR-13 | Validation failure → revise plan → retry, **bounded** by `MAX_AGENT_RETRIES`. | P0 | Forced failure stops after N retries with a clear message. |
| FR-14 | Human approval gate before final approval, deletion, or external-system change. | P0 | Agent cannot mark an artifact APPROVED. |
| FR-15 | Progress events stream to the UI in real time (SSE). **[Added]** | P0 | UI timeline updates during a run. |
| FR-16 | Agent separates **facts** from **recommendations** and **observed** from **inferred** in outputs. | P0 | Approval note has separate sections. |

### 7.3 Local tool layer
| ID | Tool | Input → Output | Safety / validation | Pri |
|---|---|---|---|---|
| FR-20 | `read_file` | local path → text + metadata | Allowlisted directories only | P0 |
| FR-21 | `ocr_document` | PDF / image → OCR text + page metadata | No network; keep source page refs | P0 |
| FR-22 | `vision_analyze` | image / page → structured visual observations | Never treated as authoritative measurement | P0 |
| FR-23 | `search_knowledge` | query + filters → relevant chunks + citations | Return source document + page; access-filtered | P0 |
| FR-24 | `calculate` | expression / data → deterministic result | Safe evaluator; input validation | P0 |
| FR-25 | `run_code` | generated code + tests → stdout / stderr / exit code | Docker isolation, timeout, no network | P0 |
| FR-26 | `write_file` | path + content → artifact path | Output directory allowlist | P0 |
| FR-27 | `create_docx` | structured content → DOCX | Template + required fields | P0 |
| FR-28 | `create_xlsx` | tables / formulas → XLSX | Validate formulas / values | P1 |
| FR-29 | `create_pptx` | slides / content → PPTX | Template + slide validation | P1 |

### 7.4 Local knowledge base / RAG
| ID | Requirement | Pri |
|---|---|---|
| FR-30 | Ingest PDF, DOCX, XLSX, PPTX → parse → chunk → local embeddings → ChromaDB. | P0 |
| FR-31 | Store metadata per chunk: filename, page number, section, document version, access classification. | P0 |
| FR-32 | Retrieve top-k relevant chunks; Qwen3.5 receives question + retrieved context. | P0 |
| FR-33 | Answers cite internal source document and page. | P0 |
| FR-34 | Access control enforced at retrieval time (server side), not only in the UI. | P0 |
| FR-35 | Re-index when a document version changes; preserve version metadata. | P1 |
| FR-36 | No external embedding or reranking APIs; vector DB and sources on local disk. | P0 |
| FR-37 | Large documents are chunked and retrieved, never pasted whole into one prompt. | P0 |

### 7.5 Multimodal / scanned document pipeline
| ID | Requirement | Pri |
|---|---|---|
| FR-40 | Native PDF text → PyMuPDF. | P0 |
| FR-41 | Scanned PDF → render page → PaddleOCR (Tesseract fallback) → text with page refs. | P0 |
| FR-42 | Photographs / drawings / inspection images → Gemma 4 E4B → structured observations (`component`, `visible_condition`, `source`, `limitation`, plus `type: observed/inferred`). | P0 |
| FR-43 | Scanned pages where OCR alone is insufficient → OCR + Gemma. | P0 |
| FR-44 | Engineering drawings are treated as non-authoritative observations; no precise measurements unless a validated specialist pipeline exists. | P0 |
| FR-45 | Handwritten notes handled by OCR / vision; quality-dependent, shown with a limitation warning. | P1 |

### 7.6 Deliverables
| ID | Artifact | Library | Approach | Pri |
|---|---|---|---|---|
| FR-50 | Approval note / report | python-docx | Template + structured fields + findings + references + human-review section | P0 |
| FR-51 | Analysis spreadsheet | openpyxl | Tables, formulas, summary sheets, source metadata | P1 |
| FR-52 | Presentation | python-pptx | Template-driven slides | P1 |
| FR-53 | Code package | Python filesystem tools | Source + tests + README + execution result | P0 |
| FR-54 | Calculation report | python-docx / XLSX | Inputs + formula + deterministic result + assumptions | P1 |
| FR-55 | Validation node checks mandatory fields, source references, and that the output file exists and re-opens. | P0 |

### 7.7 User interface (React)
| ID | Requirement | Pri |
|---|---|---|
| FR-60 | Login page and role-aware navigation. | P0 |
| FR-61 | Workbench page: chat, file upload (drag and drop), task type hint, run button. | P0 |
| FR-62 | Live **workflow timeline**: each LangGraph node, tool call, model badge, duration, status. | P0 |
| FR-63 | Evidence panel: retrieved SOP chunks with document / page; OCR text with page refs; vision observations with limitations. | P0 |
| FR-64 | Artifacts page: list, preview summary, download; status DRAFT / PENDING_REVIEW / APPROVED / REJECTED. | P0 |
| FR-65 | Review queue for `reviewer` role: approve / reject with comment. | P0 |
| FR-66 | Knowledge Base page for `admin`: upload, classify, version, re-index, delete. | P1 |
| FR-67 | Audit page for `auditor` / `admin`: filter, view, export. | P1 |
| FR-68 | **Sovereignty panel**: models local, Ollama bound to 127.0.0.1, passive list of non-loopback connections, offline indicator. | P0 |
| FR-69 | All assets bundled locally (no CDN, no external fonts). | P0 |

### 7.8 Authentication and access control
| ID | Requirement | Pri |
|---|---|---|
| FR-70 | Local username / password login (hashed passwords, no plaintext). | P0 |
| FR-71 | Roles: `admin`, `engineer`, `reviewer`, `auditor`. | P0 |
| FR-72 | Clearance levels and document classifications: `PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`. | P0 |
| FR-73 | A user can only retrieve chunks with classification ≤ their clearance. | P0 |
| FR-74 | Users see only their own files / tasks / artifacts unless role allows more. | P0 |
| FR-75 | Full matrix in `03_SECURITY_AND_ACCESS.md`. | P0 |

### 7.9 Audit and logging
| ID | Requirement | Pri |
|---|---|---|
| FR-80 | Audit every model route and every tool call: model name, tool name, timestamps, file identifiers, success / failure. | P0 |
| FR-81 | Do not log unnecessary sensitive document contents (store hashes, counts, ids). | P0 |
| FR-82 | Audit records are append-only and hash-chained for tamper evidence. **[Added]** | P1 |
| FR-83 | Audit trail is shown in the UI alongside the result. | P0 |

### 7.10 Sovereignty / air-gap proof
| ID | Requirement | Pri |
|---|---|---|
| FR-90 | Application-to-model traffic on localhost. | P0 |
| FR-91 | Outbound traffic blocked by OS firewall and/or container network policy. | P0 |
| FR-92 | Wireshark / firewall evidence captured showing no external AI / API connection during inference. | P0 |
| FR-93 | Codebase and configuration scanned for cloud endpoints and telemetry; unnecessary telemetry removed. | P0 |
| FR-94 | Uploaded files and generated artifacts stay on local storage. | P0 |

---

## 8. Non-functional requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Privacy | Zero outbound calls at runtime. |
| NFR-02 | Performance | Benchmark locally and record tokens/s, VRAM, time to first token and end-to-end Demo A time. Targets to validate (not guarantees): interactive chat first token within ~10 s after warm-up; Demo A finishes within ~5 minutes on target laptop. **[Added]** |
| NFR-03 | Resource fit | Must run on RTX 3050 Laptop (6 GB VRAM) + 16 GB RAM using quantised builds; context size tuned (start at 4096–8192 tokens). |
| NFR-04 | Reliability | Bounded retries; timeouts on every model call, tool call and sandbox run; graceful error messages. |
| NFR-05 | Auditability | 100% of model routes and tool calls logged. |
| NFR-06 | Extensibility | New model = registry edit. New tool = one file + registration. |
| NFR-07 | Usability | A first-time user can run Demo A from the UI without documentation. |
| NFR-08 | Maintainability | Type hints, linting, tests for every tool and security control. |
| NFR-09 | Portability | Windows 10/11 or Linux; one start script; all dependencies pinned. |
| NFR-10 | Accessibility | Keyboard navigable; colour contrast AA; no information by colour alone. |

---

## 9. Key user flows (requirements-level)

### Demo A — Scanned inspection report → approval note
1. User uploads a scanned inspection report.
2. System detects document type and creates a LangGraph workflow.
3. PDF pages are rendered and processed by PaddleOCR; images / pages are sent only to local vision inference (Gemma 4 E4B).
4. Qwen3.5 extracts key findings, equipment identifiers, dates, observations and requested actions.
5. Agent searches the local SOP / inspection-procedure knowledge base.
6. Agent compares findings with retrieved internal guidance and clearly separates facts from recommendations.
7. If a numerical calculation is needed, Qwen3.5 calls the Python calculation tool (never does the arithmetic itself).
8. Agent drafts an approval note with source references and a human-review section.
9. python-docx generates the real `.docx`.
10. Validation node checks mandatory fields, source references and that the output file exists.
11. UI shows the approval note and an audit trail of model / tool calls.
12. A `reviewer` approves or rejects. **Expected artifact:** `Inspection_Approval_Note.docx`.

### Demo B — Coding agent
1. User gives a coding task. 2. LangGraph routes to Qwen3.5. 3. Model plans and generates code + tests. 4. Code runs in Docker sandbox, network disabled, with timeout. 5. Agent reads stdout / stderr / test results. 6. If tests fail, error goes back to the model for a bounded correction cycle. 7. On success the system returns code and verification results. **The model proposes code; the sandbox verifies it.**

### Demo C — Multimodal
1. User uploads an engineering photograph, drawing or scanned page. 2. Gemma 4 E4B analyses the image locally. 3. OCR is used where text extraction is needed. 4. Result states clearly what was **observed** versus **inferred**, with limitations.

### Model-selection examples (must work)
| Request | Route |
|---|---|
| "Summarize this SOP." | Qwen3.5 4B → local RAG → answer |
| "Analyze this inspection photograph." | Gemma 4 E4B → visual observations → Qwen3.5 4B → answer |
| "Read this scanned inspection report and prepare an approval note." | PaddleOCR + Gemma 4 E4B → Qwen3.5 4B → local SOP RAG → Python calc if needed → python-docx → validation → DOCX |

---

## 10. Requirement-to-implementation mapping (full table from blueprint)

| Case requirement | Implementation in this design |
|---|---|
| Self-hosted / own GPU | Ollama + local Qwen3.5 + Gemma 4 + local services |
| Nothing leaves premises | No cloud inference; local storage; outbound network blocked |
| Multiple open-weight models | Model registry + configurable Ollama models |
| Automatic model selection | LangGraph router based on task / modality / complexity |
| New models addable later | Model registry and capability-based routing |
| Agentic multi-step work | LangGraph state graph + tools + bounded retries |
| File read / write | Local filesystem tools with allowlists |
| Code execution | Docker sandbox with network disabled |
| Spreadsheet work | openpyxl |
| Internal document search | ChromaDB + local embeddings + RAG |
| Scanned PDFs | PyMuPDF + PaddleOCR |
| Handwritten notes | OCR / vision; quality-dependent |
| Engineering drawings / photos | Local multimodal model (Gemma 4 E4B); visual interpretation, non-authoritative |
| Real deliverables | python-docx, openpyxl, python-pptx, code artifacts |
| Approval-note example | Inspection report → OCR / vision → RAG → reasoning → DOCX |
| Coding example | Generate → sandbox → test → fix → retest |
| No external calls proof | Firewall / network isolation + Wireshark + logs |
| Mid-range GPU fallback | Qwen3.5 4B quantised deployment and smaller components |

---

## 11. Assumptions, dependencies, constraints

**Assumptions**
- One Windows or Linux workstation with an NVIDIA GPU (reference: RTX 3050 Laptop 6 GB, 16 GB RAM).
- Internet is available **only during installation** (to download models, wheels, npm packages, Docker base image). After that, the network is disabled.
- Ollama >= v0.20.0 is installed (required for Gemma 4 support).
- Docker Desktop / Engine is installed and the sandbox image is pre-built locally.

**Dependencies**
Ollama, Qwen3.5 4B (`qwen3.5:4b`), Gemma 4 E4B (`gemma4:e4b`), Qwen3-Embedding-0.6B weights, PaddleOCR weights, Docker, Python 3.11+, Node 20+ (build time only).

**Constraints**
- 6 GB VRAM cannot hold both models comfortably at once. Load one at a time; expect slower inference when a model spills to system RAM. Benchmark and tune.
- Gemma 4 E4B download size reported by community guides varies (roughly 3 GB to ~10 GB depending on build/quantisation). Check `ollama show gemma4:e4b` and `ollama list` and choose a quantisation that fits.
- Model tags can change; verify before final build.

---

## 12. Explicitly excluded technology

| Excluded | Reason |
|---|---|
| **Open WebUI** | Not used; the UI is a custom React app. |
| **n8n** | Not used; LangGraph handles all orchestration, tools, retries, branching. |
| Streamlit / Gradio | Not used; React + FastAPI only. |
| LangSmith and any hosted tracing | Would break the air-gap; local audit log is used. |
| Any cloud AI provider or cloud storage | Violates sovereignty requirement. |

---

## 13. Risks and mitigations

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | 4B model weaker than frontier models | Lower answer quality | RAG + deterministic tools + validation + bounded agent iteration; do not overclaim. |
| R2 | 6 GB VRAM too small for both models | Slow or failed loads | One model resident at a time; small context; quantised builds; OCR on CPU; benchmark early (Phase 0). |
| R3 | Vision model misreads labels / defects | Wrong observation | Label as observation; show limitation; human review mandatory; never present as measurement. |
| R4 | OCR quality poor (scan quality, handwriting, language) | Missing / wrong text | Show OCR text beside page image; Tesseract fallback; allow manual correction **[Added]**. |
| R5 | Model tag / package name changes | Build failure | Phase 0 verification while online; pin versions. |
| R6 | Runaway agent loops | Hang / resource use | `MAX_AGENT_RETRIES`, `MAX_TOOL_STEPS`, per-step timeouts. |
| R7 | Prompt injection through uploaded documents | Unsafe tool use | Treat document text as data; tool allowlists; human gates; see security doc. |
| R8 | Hidden network calls from libraries | Breaks sovereignty claim | Offline env flags, telemetry off, egress scan, Wireshark proof. |
| R9 | Large documents overflow context | Truncated reasoning | Chunk + retrieve; never paste whole docs. |
| R10 | Live demo failure | Lost credibility | Pre-warmed models, recorded fallback video, pre-generated demo data (see doc 05). |

---

## 14. Known limitations (how to present them honestly)

- A 4B model is not a substitute for a large frontier model in every reasoning task.
- Engineering / safety-critical conclusions require human / domain-expert validation.
- Vision models can misread small labels, dimensions or ambiguous drawings; never present visual guesses as measured facts.
- OCR quality depends on scan quality, handwriting and language.
- Local inference on an RTX 3050 6 GB can be slower than cloud inference; quantisation and context size must be tuned.
- Large documents must be chunked and retrieved.
- Bounded retries prevent runaway loops.
- Production deployment would additionally need enterprise identity, authorisation, secrets management, patching, backups, model governance and a formal security review.

---

## 15. Success metrics

| Metric | Target |
|---|---|
| Offline inference works | 100% of demo requests succeed with network disabled |
| Correct routing | 100% of the 3 model-selection examples route correctly |
| Deliverable validity | DOCX opens, contains all mandatory sections and source references |
| Sandbox verification | Generated code executes in sandbox and result is reported |
| Access control | 0 unauthorised chunks retrievable in access tests |
| Audit completeness | Every model route + tool call present in audit log |
| Network evidence | 0 external connections attributed to the workbench during the run |

Full test matrix: `05_TEST_EVAL_DEMO.md`.

---

## 16. Milestones (map to build phases in doc 04)

| Milestone | Phases |
|---|---|
| M1 — Foundations (env, registry, auth, audit) | 0–2 |
| M2 — Agent core + RAG | 3–4 |
| M3 — Multimodal + routing | 5–7 |
| M4 — Tools, code sandbox, deliverables | 8–9 |
| M5 — Inspection workflow + human review | 10 |
| M6 — UI, sovereignty proof, tests, packaging | 11–14 |

---

## 17. Glossary

| Term | Meaning |
|---|---|
| Air-gapped | Runs with no connection to the internet. |
| Sovereign | Data and inference stay under the organisation's own control. |
| Ollama | Local server that runs open-weight models and exposes a localhost API. |
| LangGraph | Framework to build stateful, multi-step agent workflows as a graph. |
| RAG | Retrieval-Augmented Generation: find relevant internal text first, then let the model answer using it. |
| OCR | Optical character recognition: turning scanned images into text. |
| Sandbox | An isolated container where untrusted code can run safely. |
| SOP | Standard Operating Procedure. |
| Clearance / classification | Access level of a user / a document. |
