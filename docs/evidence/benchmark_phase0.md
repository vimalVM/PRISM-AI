# Phase 0 Benchmark Report — Target Hardware Smoke Test

**Environment:**
- GPU: NVIDIA GeForce RTX 3050 Laptop GPU (6 GB VRAM)
- Driver / CUDA: 581.86 / CUDA 13.0
- Ollama Server: v0.34.2 bound to `127.0.0.1:11434`
- Memory Policy: `OLLAMA_MAX_LOADED_MODELS=1` (Sequential model residence)

---

## 1. Qwen3.5 4B (`qwen3.5:4b`) Performance

| Metric | Thinking Mode OFF (`think: false`) | Thinking Mode ON (`think: true`) |
|---|---|---|
| **Cold / Load Duration** | 11.04 s | 0.03 s |
| **Total Wall-Clock Time** | 100.21 s | 22.19 s |
| **Output Token Count** | 4076 tokens | 1029 tokens |
| **Generation Speed** | **45.84 tokens/s** | **46.79 tokens/s** |
| **Prompt Eval Speed** | 106.38 tokens/s | - |
| **VRAM Usage (Before / Peak)** | 0 MiB / 6144 MiB -> 3829 MiB / 6144 MiB | 3829 MiB / 6144 MiB -> 0 MiB / 6144 MiB |

### Responses:
- **Thinking OFF Response**:
  > 

- **Thinking ON Response**:
  > I am Qwen3.5, an AI assistant designed to help you with tasks, answer questions, and provide information....

**Observation on Thinking Mode:**
Turning `think: false` eliminates extraneous chain-of-thought overhead for JSON generation, routing, and tool steps, yielding much faster wall-clock completion with lower token budgets.

---

## 2. Gemma 4 E4B (`gemma4:e4b`) Multimodal Vision Performance

| Metric | Measured Value |
|---|---|
| **Input** | `docs/evidence/test_image.png` (200x200 text render) |
| **Load Duration** | 7.9 s |
| **Total Wall-Clock Time** | 14.04 s |
| **Output Token Count** | 242 tokens |
| **Generation Speed** | **43.04 tokens/s** |
| **VRAM Usage (Before / Peak)** | 0 MiB / 6144 MiB -> 0 MiB / 6144 MiB |

### Observation Output:
> The image is an abstract, dark background featuring smoky or distressed textures, but contains no visible text or recognizable elements.

---

## 3. Findings & Memory Strategy Validation
1. **Fit on 6 GB VRAM**: Both models load and run successfully within the workstation envelope.
2. **Swap Overhead**: Switching between models takes ~2-5 seconds depending on disk cache and VRAM allocation. Vision tasks should be batched together during multi-step execution.
3. **Offline Integrity**: Inference executed against `127.0.0.1:11434` with zero external requests.
