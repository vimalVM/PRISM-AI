# Licenses and Attributions — Sovereign AI Workbench

This document catalogs open-source and open-weight models and core software libraries used by the Sovereign AI Workbench.

## 1. Local Models

| Model | Architecture | Parameter Count | License | Source / Registry |
|---|---|---|---|---|
| **Qwen3.5 4B** | `qwen35` | 4.7B | Apache License 2.0 | Alibaba Cloud / Ollama (`qwen3.5:4b`) |
| **Gemma 4 E4B** | `gemma4` | 8.0B | Apache License 2.0 | Google / Ollama (`gemma4:e4b`) |
| **Qwen3-Embedding-0.6B** | `qwen3` | 0.6B | Apache License 2.0 | Alibaba Cloud / HuggingFace / Local |

## 2. Core Frameworks & Tooling

| Technology | Role | License |
|---|---|---|
| **Ollama** | Local model inference runtime | MIT License |
| **LangGraph** | Multi-step agent graph orchestration | MIT License |
| **LangChain Core** | Agent abstractions and message types | MIT License |
| **FastAPI** | Local REST & SSE Web API | MIT License |
| **Uvicorn** | ASGI server | BSD 3-Clause |
| **ChromaDB** | Embedded persistent vector database | Apache License 2.0 |
| **Sentence-Transformers**| Embedding generation framework | Apache License 2.0 |
| **PyMuPDF (fitz)** | PDF extraction and page rasterization | AGPL-3.0 / Commercial |
| **PaddleOCR / PaddlePaddle**| Local OCR engine | Apache License 2.0 |
| **Pillow** | Imaging library | HPND License |
| **python-docx** | DOCX report & approval note generation | MIT License |
| **openpyxl** | Spreadsheet generation | MIT License |
| **python-pptx** | Presentation slide generation | MIT License |
| **Docker SDK** | Sandboxed container runner | Apache License 2.0 |
| **SQLite / SQLAlchemy** | Structured application storage & ORM | Public Domain / MIT License |
| **Argon2-cffi** | Password hashing | MIT License |
| **React / Vite / TypeScript**| Local frontend interface | MIT License |
| **Tailwind CSS** | Design system styling engine | MIT License |
| **Lucide Icons** | Locally bundled SVG icons | ISC License |
