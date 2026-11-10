# Model Installation & Selection Guide

## Principles
- Use **free/open-weight** models with locally hosted inference (Ollama).
- **No paid/proprietary AI APIs**.
- **Do not auto-download models**. `ModelManager.pull_model` requires `explicit_authorization=True` and `AISMA_ALLOW_MODEL_PULL=true`.
- **Do not assume a model tag exists**. Verify with `ollama list` or `GET /api/tags`.
- **Verify exact licence** before recommending/using a model in production (check official model card, Hugging Face, and Ollama model page). Licence terms can vary by model/version.

## Hardware-aware guidance (target: 4 GB VRAM)
- Prefer small, quantized models (Q4-class GGUF where appropriate).
- Use one shared inference service; **do not load 8 separate LLMs**.
- Keep `AISMA_CONCURRENCY_LIMIT=1` on constrained GPUs.
- Configure conservative `AISMA_CONTEXT_LENGTH` and `AISMA_MAX_TOKENS`.
- CPU fallback is supported by configuration and Ollama/runtime offloading; expect higher latency.
- The full model may not fit in VRAM; runtime offloading/quantization are required.

## Candidate models (verify before use)
| Candidate | Typical size class | Notes | Licence status |
|---|---:|---|---|
| `qwen3.5:4b` (observed locally during Phase 2) | ~4B, Q4_K_M | Small footprint; structured/tools capable in local tag metadata; verify quality for marketing tasks. | **Verify exact Qwen 3.5 licence/terms before production recommendation.** |
| `phi3.5:latest` (observed locally during Phase 2) | ~3.8B | Good small instruction/classification candidate; MIT family lineage commonly associated with Phi-3.5 mini. | **Verify exact local tag/model licence before production recommendation.** |
| `qwen2.5-coder:1.5b-base` | ~1.5B | Low resource; base/completion oriented, less suitable for chat/marketing generation. | Apache-2.0 lineage commonly associated; **verify exact tag**. |
| Phi-4-mini (candidate) | small | Evaluate only if an exact Ollama tag exists and is verified. | **Verify exact licence/tag availability.** |
| Qwen 3.5 2B (candidate) | ~2B | Evaluate if exact Ollama tag exists and is verified. | **Verify exact licence/tag availability.** |

## Verification checklist before selecting a default model
1. `OllamaClient().health_check()` returns `ok: true`.
2. `OllamaClient().has_model(<tag>)` is true.
3. Inspect `/api/tags` details (parameter size, quantization, context length).
4. Confirm licence from official sources.
5. Run benchmark (latency, tokens/sec, memory, structured JSON reliability, content quality, classification accuracy).
6. Confirm behavior under kill switch and injection-scan governance paths.

## Benchmarking command pattern (manual, when model/runtime available)
Use `ai.ollama_provider.OllamaProvider` / `ai.model_manager.ModelManager` with small prompts and record:
- response latency (`LLMResult.latency_ms`),
- `eval_count` / `total_duration_ns` when reported,
- RSS/VRAM observations (`nvidia-smi`, task manager / `psutil`),
- JSON parse success for `extract_structured`/classification,
- human/automated rubric for content/classification quality.

Do not claim benchmarks that were not actually executed.
