# 05 — Test, Evaluation and Demo Guide

**Product:** Sovereign AI Workbench
**Related:** `01_PRD.md` (requirements), `03_SECURITY_AND_ACCESS.md` (security tests), `04_ANTIGRAVITY_BUILD_PLAN.md` (phases)

---

## 1. Evaluation plan (from blueprint, with IDs)

| ID | Area | Test | Success criterion | Req |
|---|---|---|---|---|
| EV-01 | Local inference | Disconnect Internet and run Qwen3.5 | Model still responds | FR-01, FR-08 |
| EV-02 | Local inference (vision) | Disconnect Internet and run Gemma 4 E4B on a test image | Observations returned | FR-02 |
| EV-03 | Routing | Run text, coding and image tasks | Correct configured route selected and logged | FR-04, FR-05 |
| EV-04 | Agent | Multi-step report task | Multiple tools called in correct sequence | FR-10 |
| EV-05 | RAG | Ask a question from internal SOP | Answer grounded in retrieved source, cited | FR-30–33 |
| EV-06 | OCR | Scanned report | Useful text extracted with page references | FR-21, FR-41 |
| EV-07 | Vision | Photograph / drawing | Useful visual observations returned with limitation | FR-22, FR-42 |
| EV-08 | Coding | Generated program + tests | Sandbox executes and reports result | FR-25, FR-53 |
| EV-09 | Artifacts | DOCX / XLSX / PPTX | Files open and contain required sections | FR-50–55 |
| EV-10 | Security | Wireshark / firewall | No external traffic during run | FR-90–93 |
| EV-11 | Auditability | Review logs | Model / tool route and outcomes visible | FR-80–83 |
| EV-12 | Access | Low-clearance user asks about restricted SOP | No restricted content returned | FR-73 |
| EV-13 | Human control | Author tries to approve | Blocked | FR-14 |
| EV-14 | UI | Run Demo A entirely from UI | Timeline, evidence, download, review all work | FR-60–68 |
| EV-15 | Resource fit | Run on RTX 3050 6 GB | No out-of-memory; timings recorded | NFR-02, NFR-03 |
| EV-16 | Bounded retries | Force validation failure | Stops at `MAX_AGENT_RETRIES` with clear message | FR-13 |

`scripts/eval_run.py` executes or guides each row and writes `docs/evidence/eval_report.md` (PASS / FAIL / MANUAL).

---

## 2. Test layers

| Layer | Tool | Notes |
|---|---|---|
| Unit | pytest | Tools, router, registry, safe_path, calculator, validators, RBAC, audit chain |
| Integration | pytest + FastAPI TestClient | API + DB + fake Ollama client (no GPU needed) |
| Live model | pytest `-m live_model` | Uses real Ollama models; run on the demo laptop |
| Frontend | Vitest + Testing Library | Timeline, RoleGuard, EvidencePanel, ReviewForm |
| End-to-end | Scripted run (`eval_run.py`) + manual browser check | Demo A / B / C |
| Security | pytest + scripts | Section 3 |
| Egress | `scripts/scan_egress.py` | Static scan; must be clean |

**Fake Ollama client:** returns canned JSON for plan / classification / vision so most tests run fast and offline.

---

## 3. Security and access tests (full list)

| ID | Test | Expected |
|---|---|---|
| SEC-01 | Network disabled; run inference | Works |
| SEC-02 | Firewall on; run Demo A | No external packets from workbench |
| SEC-03 | `scan_egress.py` | Clean (no cloud endpoints / telemetry / forbidden tech names) |
| SEC-04 | `INTERNAL` user searches `RESTRICTED` doc | Zero chunks |
| SEC-05 | Prompt injection inside uploaded / retrieved text | No policy bypass; no restricted data |
| SEC-06 | Path traversal in `read_file` (`../`, `..\`, absolute, UNC, symlink) | Denied + audited |
| SEC-07 | Renamed executable uploaded as `.pdf` | Rejected |
| SEC-08 | Sandbox code attempts network | Fails |
| SEC-09 | Sandbox infinite loop | Killed at timeout |
| SEC-10 | Sandbox memory bomb | Killed |
| SEC-11 | Author approves own artifact; agent tries to set APPROVED | 403 / impossible |
| SEC-12 | `engineer` calls admin endpoints | 403 |
| SEC-13 | 6 wrong passwords | Locked + audit |
| SEC-14 | Modify an audit row | `/audit/verify` fails |
| SEC-15 | Formula injection text in XLSX | Stored as text / blocked |
| SEC-16 | Grep logs for known document strings | None found |
| SEC-17 | Cross-origin request from other origin | Blocked |
| SEC-18 | Registry with `:cloud` tag or non-loopback Ollama URL | Startup check fails |
| SEC-19 | Auditor tries to download an artifact | 403 |
| SEC-20 | Reviewer opens artifact not assigned | 403 |
| SEC-21 | Delete KB doc without confirmation token | Rejected |
| SEC-22 | Output written outside `data/outputs` | Denied |
| SEC-23 | DOCX / PPTX output scanned for external relationships / OLE | None |
| SEC-24 | Citation in output that does not map to a retrieved chunk | Validation fails |

### 3.1 Access-matrix tests
Generate one parametrised test per cell of the matrix in `03` §5.3 (role × capability). Any change to the matrix must change the test data.

---

## 4. Functional test scenarios

### 4.1 Routing (EV-03)
| Input | Expected route (audit `model_route`) |
|---|---|
| "Summarize this SOP." | rule `text_default` → Qwen3.5 4B, RAG tool used |
| "Analyze this inspection photograph." + image | rule `image_or_photo` → Gemma 4 E4B → Qwen3.5 4B |
| "Read this scanned inspection report and prepare an approval note." + scanned PDF | rule `scanned_document` → OCR + Gemma 4 E4B → Qwen3.5 4B |
| "Write a Python function that … with tests." | rule `coding` → Qwen3.5 4B + sandbox |
| Registry: enable `future_strong_reasoning` and give a high-complexity task | rule `complex_reasoning` selected (no code change) |
| Registry: disable Gemma | vision route skipped with audit note; user sees "vision unavailable" |

### 4.2 Agent behaviour
- Plan contains only registered tools; unknown tool → rejected.
- Retry counter increments on validation failure and stops at limit.
- Step limit stops a looping plan.
- Facts and recommendations are in separate sections of the note.

### 4.3 RAG
- Cited answer includes document name, version and page.
- "Not in the sources" answer when the SOP does not contain the answer.
- Superseded version is not retrieved.
- Chunk metadata contains all required fields.

### 4.4 Multimodal
- Native PDF → PyMuPDF text with page refs (no OCR).
- Scanned PDF → OCR text with page refs.
- Embedded image → Gemma observation with `source = page_N_image_M`.
- Every observation has `limitation`; drawings never produce dimensional claims.

### 4.5 Deliverables
- DOCX: all mandatory sections; no `{{…}}`; human-review block present and blank.
- XLSX: sheets `Data`, `Calculations`, `Summary`, `Sources`; formulas present; no external links.
- PPTX: title, content, sources slide; no empty titles.
- Code package: `src/`, `tests/`, `README.md`, `RESULT.txt` with exit code 0.

### 4.6 Calculator
- Correct results for arithmetic / powers / whitelisted math functions.
- Rejects attribute access, imports, names outside whitelist, `9**9**9`, very long input.
- Model-facing rule: arithmetic in the approval note comes from `calculate` results (validator checks).

---

## 5. Benchmarks (record on the target laptop) — NFR-02

`scripts/benchmark.py` records for each model separately:

| Metric | How |
|---|---|
| Model load time (cold) | time to first response after unload |
| Time to first token (warm) | streaming first token |
| Tokens per second | Ollama response stats |
| VRAM used | `nvidia-smi` sample |
| RAM used | psutil |
| Context size used | settings |
| Demo A end-to-end time | wall-clock |
| Demo B end-to-end time | wall-clock |
| Model swap overhead | Gemma → Qwen switch time |

Save to `docs/evidence/benchmark.md`. Note: targets in the PRD are soft; report real numbers honestly. If speeds are low, tune `num_ctx`, quantisation, batching, and CPU offload settings.

---

## 6. Hackathon demo script (5–7 minutes)

### 6.1 Preparation (before going on stage)
- [ ] Models warmed (one at a time), network enabled only until warm-up done.
- [ ] Synthetic SOP KB ingested (with different classifications).
- [ ] Synthetic scanned inspection report + a photograph ready in a folder.
- [ ] Users seeded: engineer, reviewer, auditor, admin (passwords known to presenter only).
- [ ] Firewall rules ready; Wireshark open on the physical interface; Sovereignty page open in a tab.
- [ ] Recorded fallback video of a full run.
- [ ] Power and display checked; laptop plugged in and set to high performance.

### 6.2 Run of show

| Time | Step | What to show | Talking point |
|---|---|---|---|
| 0:00 | 1 | Open workbench; models panel shows Qwen3.5 4B + Gemma 4 E4B, endpoint 127.0.0.1 | "Everything runs on this machine." |
| 0:30 | 2 | Log in as engineer; upload the scanned inspection report | Role-based access. |
| 1:00 | 3 | Start run; timeline shows OCR then vision extraction | "OCR for text, Gemma for the photo — observations, not measurements." |
| 1:45 | 4 | Router badge: Gemma for the image, Qwen for reasoning; audit reason visible | Automatic model selection. |
| 2:15 | 5 | Agent calls local knowledge base; open the retrieved SOP evidence chip | Cited, grounded answers. |
| 2:45 | 6 | Show the calculation step (Python tool, not the model) | "Model reasons; tools compute." |
| 3:15 | 7 | Open generated `Inspection_Approval_Note.docx` | Real deliverable with sources and human-review block. |
| 3:45 | 8 | Switch to reviewer, approve (or show author cannot approve own) | Human in control. |
| 4:15 | 9 | Coding task: show sandbox run, failed test → fix → pass | "Model proposes; sandbox verifies." |
| 5:00 | 10 | Upload an image; show observed vs inferred + limitation notice | Honest limits. |
| 5:30 | 11 | **Disable network** (Wi-Fi off). Repeat a short inference request | Live offline proof. |
| 6:00 | 12 | Show Wireshark filter (nothing), Sovereignty panel (0 connections), audit log export | Evidence, not claims. |
| 6:30 | 13 | Access-control moment: log in as low-clearance user, ask about restricted SOP → refusal | Enforced at retrieval, not in UI. |
| 7:00 | End | Limitations slide: 4B model, human review required, not for safety-critical decisions | Honest positioning. |

If time is short, drop step 13 or step 9.

### 6.3 What to say about limitations
- A 4B model does not equal a large frontier model; RAG, tools and validation compensate.
- Vision and OCR can misread; humans must review.
- Not for safety-critical, financial, legal or defence decisions without expert validation.
- Production needs enterprise identity, secrets management, patching, backups, model governance and security review.

### 6.4 Fallback plan
| Problem | Action |
|---|---|
| Model slow / VRAM full | Use pre-run results loaded in Runs list; show timeline replay. |
| OCR fails on demo scan | Switch to pre-cached OCR result (cache by file hash). |
| Docker not starting | Show recorded sandbox run + test output. |
| Network proof tool fails | Show saved pcap screenshots in `docs/evidence/`. |
| Everything fails | Play the recorded video. |

---

## 7. Demo data specification (synthetic only)

| Item | Description |
|---|---|
| SOP set | 4 short SOP PDFs (inspection procedure, weld acceptance, calculation method, escalation), versions v1 and v2 of one SOP, classifications INTERNAL / CONFIDENTIAL / RESTRICTED. |
| Scanned inspection report | 8-page image-only PDF (typed text rendered as images), equipment ID, date, inspector, observations, one embedded photograph on page 7 (`page_7_image_1`), one measurement table for the calculation step. |
| Photograph | Royalty-free image of a pipe joint / industrial component supplied by the team (not generated by the agent). |
| Coding tasks | e.g. "Write a function that computes stress = force / area with unit checks, with pytest tests." |
| Users | `admin`, `engineer1`, `reviewer1`, `auditor1`, plus `engineer_low` (INTERNAL clearance). Passwords entered at seed time. |

`scripts/make_demo_data.py` generates the SOPs and the scanned-style report. Never use real confidential data.

---

## 8. Requirement traceability (short)

| Requirement group | Tests |
|---|---|
| FR-01 – FR-08 (models, routing) | EV-01, EV-02, EV-03, SEC-18 |
| FR-10 – FR-16 (agent) | EV-04, EV-13, EV-16 |
| FR-20 – FR-29 (tools) | Unit tests per tool, SEC-06, SEC-08–10, SEC-15 |
| FR-30 – FR-37 (RAG) | EV-05, EV-12, SEC-04, SEC-05, SEC-24 |
| FR-40 – FR-45 (multimodal) | EV-06, EV-07 |
| FR-50 – FR-55 (deliverables) | EV-09, SEC-23 |
| FR-60 – FR-69 (UI) | EV-14, Vitest suite |
| FR-70 – FR-75 (access) | Access-matrix tests, SEC-11, SEC-12, SEC-19, SEC-20 |
| FR-80 – FR-83 (audit) | EV-11, SEC-14, SEC-16 |
| FR-90 – FR-94 (sovereignty) | EV-10, SEC-01–03 |
| NFR-02, NFR-03 | EV-15, Benchmarks |

---

## 9. Final acceptance checklist

- [ ] All EV-01 … EV-16 pass (or MANUAL with evidence).
- [ ] All SEC-01 … SEC-24 pass.
- [ ] `check_all` (ruff, pytest, vitest, egress scan) passes.
- [ ] Demo run twice offline within 7 minutes.
- [ ] Evidence folder complete (models, benchmark, egress scan, Wireshark, firewall, audit export, eval report).
- [ ] No use or mention of Open WebUI, n8n, Streamlit or LangSmith in code or docs (except forbidden-technology tables).
