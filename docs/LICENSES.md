# Sovereign AI Workbench — Third-Party Licenses & Software Manifest

This document records the licensing terms for all third-party open-weight models, libraries, frameworks, and fonts bundled or utilized within the **Sovereign AI Workbench**.

---

## 1. Local Open-Weight Foundation Models

| Model | Source Organization | License / Terms of Use | Commercial Use Permitted |
|---|---|---|---|
| **Qwen3.5 4B** | Alibaba Cloud / Qwen Team | **Apache 2.0** / Qwen License Agreement | Yes (< 100M MAU) |
| **Gemma 4 E4B** | Google DeepMind | **Gemma Terms of Use** | Yes (subject to acceptable use policy) |
| **Qwen3-Embedding-0.6B** | Alibaba Cloud / Qwen Team | **Apache 2.0** | Yes |

*Note: Models run exclusively via local weights in Ollama (`127.0.0.1:11434`). No remote API calls or telemetry.*

---

## 2. Backend & Agent Orchestration Libraries

| Library | Function in Workbench | License |
|---|---|---|
| **FastAPI** | Local REST & SSE Web API Framework | **MIT License** |
| **Uvicorn** | ASGI Local Web Server | **BSD 3-Clause License** |
| **Pydantic (v2)** | Strict Data Validation & Schemas | **MIT License** |
| **LangGraph** | Cyclical Agent State Machine Orchestrator | **MIT License** |
| **LangChain Core / Ollama** | Tool abstraction & local Ollama bindings | **MIT License** |
| **SQLAlchemy** | Local SQLite ORM & Query Engine | **MIT License** |
| **ChromaDB** | Local Persistent Vector Database | **Apache 2.0** |
| **Sentence-Transformers** | Offline CPU Embeddings Pipeline | **Apache 2.0** |
| **PaddleOCR / PaddlePaddle** | High-precision CPU Document OCR Engine | **Apache 2.0** |
| **PyMuPDF** | PDF Parsing & High-DPI Page Rendering | **AGPL-3.0 / Commercial** |
| **python-docx** | Word Deliverable Generation (`.docx`) | **MIT License** |
| **openpyxl** | Spreadsheet Generation (`.xlsx`) | **MIT License** |
| **python-pptx** | Slide Presentation Generation (`.pptx`) | **MIT License** |
| **Pillow (PIL)** | Image Preprocessing & Format Validation | **HPND License** |
| **Argon2-cffi** | Memory-Hard Password Hashing | **MIT License** |
| **psutil** | Passive Localhost Socket & Hardware Auditing | **BSD 3-Clause License** |

---

## 3. Frontend Web Application & Assets

| Component | Function | License |
|---|---|---|
| **React (v18)** | Declarative User Interface | **MIT License** |
| **Vite (v5)** | Local Frontend Bundler | **MIT License** |
| **TypeScript** | Type Safety & Verification | **Apache 2.0** |
| **Tailwind CSS** | Styling & UI Design System | **MIT License** |
| **Lucide React** | Local Vector UI Icons | **ISC License** |
| **Geist Sans** | Bundled Local UI Typography | **SIL Open Font License 1.1** |
| **JetBrains Mono** | Bundled Local Monospace Typography | **Apache 2.0** |

---

## 4. Air-Gap & IP Affirmations

1. **No External CDN Dependencies**: All CSS, JavaScript, fonts, and icons are compiled into `frontend/dist` and served locally. Zero network fetches occur at runtime.
2. **Deterministic File Generators**: Document deliverables (`.docx`, `.xlsx`, `.pptx`) are created using standard MIT-licensed libraries without proprietary watermarks or hidden cloud telemetry.
3. **Container Sandboxing**: The Docker execution sandbox operates under `--network=none` with unprivileged user `10001:10001` and dropped capabilities.
