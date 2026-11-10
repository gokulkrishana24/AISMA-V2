# Hardware Compatibility Guide

## Target baseline
Phase 2 is designed to be hardware-aware for constrained local development:
- Windows 11
- NVIDIA RTX 3050 Laptop GPU (4 GB VRAM observed in this environment)
- Python 3.12
- Local Ollama runtime

## Constraints
- **Do not assume the full model fits in 4 GB VRAM.** Use quantized models and let Ollama/llama.cpp manage offloading.
- Keep `context_length` and `max_tokens` conservative on constrained systems.
- Use **one shared inference service** (`concurrency_limit=1` recommended).
- Avoid loading multiple large models simultaneously.

## Detection
`ai.hardware.detect_hardware()` reports:
- CPU count
- RAM total/available (`psutil`)
- GPU name and VRAM total/free via `nvidia-smi` when available

`ModelManager.hardware_snapshot()` exposes this for selection/monitoring.

## Runtime options
`ai.hardware.recommend_runtime_options()` applies conservative request sizing:
- caps/bounds `num_ctx` and `num_predict`
- sets `num_gpu=0` when `AISMA_GPU_PREFERENCE=cpu_only`
- keeps defaults conservative for <= 4 GB VRAM

## CPU fallback
- Enable with `AISMA_CPU_FALLBACK_ENABLED=true` (default).
- `ModelManager.select_model`/`run_with_fallback` can select a fallback model when primary is unavailable or errors occur.
- CPU-only mode can be forced with `AISMA_GPU_PREFERENCE=cpu_only`.
- Expect slower latency and potential timeouts; increase `AISMA_REQUEST_TIMEOUT_SECONDS` if needed.

## Known environment observations (Phase 2 implementation session)
Observed locally (factual):
- Ollama API reachable at `http://localhost:11434`.
- Installed models reported by Ollama included `qwen3.5:4b`, `qwen3.5:9b`, `qwen2.5-coder:1.5b-base`, `phi3.5:latest`.
- GPU: NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB.
- RAM: ~16 GB total, but low available memory at observation time.

A real inference smoke test was attempted against `qwen3.5:4b` and **timed out** at 60 seconds in that environment state; the timeout was handled (`OllamaTimeoutError`). This indicates cold-load/resource pressure risk on constrained hardware — tune timeout/context/max tokens and close other workloads.
