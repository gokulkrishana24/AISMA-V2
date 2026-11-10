# Troubleshooting Guide (Phase 2 Local AI)

## Ollama unavailable
**Symptoms:** `health_check()` returns `ok:false`, `OllamaUnavailableError`, connection refused.
**Checks:**
- Ensure Ollama is running on Windows.
- Verify endpoint: `curl http://localhost:11434/api/tags`.
- Confirm `AISMA_OLLAMA_ENDPOINT` matches the actual local server.
- Check firewall/VPN/proxy interference for localhost.

## Model not found
**Symptoms:** `OllamaModelNotFoundError`, `has_model()` false, fallback selection.
**Checks:**
- Run `ollama list` and compare exact tag (including `:latest`/version where applicable).
- Do not assume tags; set `AISMA_DEFAULT_MODEL`/`AISMA_FALLBACK_MODEL` to installed tags.
- Pull only with explicit authorization: `ollama pull <tag>`.

## Timeouts / slow inference
**Symptoms:** `OllamaTimeoutError`, real smoke timeout.
**Checks:**
- First request may load the model (cold start) — increase `AISMA_REQUEST_TIMEOUT_SECONDS`.
- Reduce `AISMA_MAX_TOKENS` and `AISMA_CONTEXT_LENGTH`.
- Set `AISMA_CONCURRENCY_LIMIT=1`.
- Close memory/VRAM-heavy applications; 4 GB VRAM systems are sensitive.
- Consider CPU-only mode (`AISMA_GPU_PREFERENCE=cpu_only`) for debugging; expect slower responses.
- Prefer smaller quantized models.

## Invalid / non-JSON structured output
**Symptoms:** `extract_structured` raises `OllamaError` ("Model did not return valid JSON").
**Checks:**
- Confirm provider uses JSON format where supported.
- Lower temperature for extraction.
- Simplify schema and prompt; validate/repair in a controlled post-processing step (never bypass governance for privileged actions).
- Try a model with better structured-output reliability (benchmark first).

## Injection scan blocks input
**Symptoms:** `InjectionScanError` from untrusted input processing.
**Checks:**
- This is expected for prompt-injection/jailbreak patterns in untrusted sources.
- Do not disable injection scanning for external text.
- Review source content; if false positive, adjust patterns carefully with tests (Phase 1 governance code).

## Kill switch blocks runtime
**Symptoms:** `PermissionError: Kill switch engaged...`
**Checks:**
- Inspect global/business kill switch state (`state/killswitch/*`).
- Disengage only through authorized governance/admin flow.
- AI runtime respects kill switch by design.

## GPU / hardware detection issues
**Symptoms:** missing VRAM info.
**Checks:**
- Ensure NVIDIA drivers and `nvidia-smi` are available in PATH.
- `psutil` should be installed for RAM/CPU metrics.
- Hardware-aware selection degrades conservatively if metrics are unavailable.

## Tests
- Default suite uses mocked Ollama responses: `python -m pytest -q`.
- Real Ollama smoke test is opt-in: `AISMA_RUN_REAL_OLLAMA_TESTS=1 python -m pytest -q tests/ai/test_real_ollama_optional.py`.
- Report real inference only when it actually ran and completed.
