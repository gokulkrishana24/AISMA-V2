# Model Benchmarking Report (Phase 2 — Real-Inference Recovery)

**Status:** Partial benchmark evidence with **successful real local inference** on a controlled, hardware-constrained setup.  
**Rule:** No fabricated benchmark numbers. Real inference is reported only where actually executed. Successful, failed, and not-performed tests are distinguished explicitly.

## 1. Environment / runtime inspection (observed 2026-11-09, local Windows session)

| Item | Observed value |
|---|---|
| Python | 3.12.7 |
| Ollama API | `http://localhost:11434` reachable (`/api/tags` OK) |
| GPU (`nvidia-smi`) | NVIDIA GeForce RTX 3050 Laptop GPU, **4096 MiB** total |
| GPU state (before recovery run) | ~2525 MiB used, ~1438 MiB free, 0% util |
| GPU state (after phi3.5 tests) | ~2317 MiB used, ~1646 MiB free, 0% util |
| RAM (`psutil`) | ~15709 MB total; **~1805 MB available at inspection** (~88.5% used); swap ~20799 MB total, ~3624 MB used |
| CPU | 16 logical CPUs, ~50% observed during brief sample |
| Ollama loaded model (`/api/ps`, before recovery) | `qwen3.5:4b` loaded (Q4_K_M, 4.2B, `size_vram` ~1.88 GB, `context_length` 4096, runner `llamacpp`) |
| Ollama loaded model (`/api/ps`, after tests) | `phi3.5:latest` loaded (`size_vram` ~2.34 GB, `context_length` 512) |

**Constraints:** 4 GB VRAM; limited available RAM/high memory pressure; model loading/offloading can dominate latency. One request at a time was used for controlled tests.

## 2. Installed model metadata (`GET /api/tags`, observed)

| Model tag | Parameter/quant/size | Reported context | Capabilities | Suitability (instruction/chat) |
|---|---|---:|---|---|
| `qwen3.5:4b` | 4.2B, Q4_K_M, ~3.32 GB | 262144 | completion, vision, tools, **thinking** | **Suitable instruction-capable model**, but observed to emit `thinking` output; with small `num_predict` can exhaust budget before `response` (see failed/partial observations). Already loaded initially (advantage) but heavier. |
| `qwen3.5:9b` | 9.0B, Q4_K_M, ~6.55 GB | 262144 | completion, vision, tools, thinking | **Not selected** for 4 GB VRAM constrained recovery (too large/risky). |
| `phi3.5:latest` | 3.8B, Q4_0, ~2.18 GB | 131072 | completion | **Smallest suitable instruction-following model already installed** for this recovery: Phi-3.5 mini family is instruction-tuned/chat-oriented in practice; not a base coding model. Smaller artifact than `qwen3.5:4b`. **Selected for controlled success path**. Licence must still be verified for exact tag before production recommendation. |
| `qwen2.5-coder:1.5b-base` | 1.5B, Q4_K_M, ~0.99 GB | 32768 | completion, insert | **Not suitable** for chat/instruction-following (explicit base coding/completion model). Excluded by instruction. |

**No models were downloaded or pulled.**

## 3. Real inference tests (actual)

### 3.1 Controlled real generation — **SUCCESS** (acceptance criterion met)
- **Model:** `phi3.5:latest` (smallest suitable installed instruction-following model; see §2)
- **Endpoint:** `http://localhost:11434` (local Ollama)
- **Prompt:** `Reply with exactly: AISMA_INFERENCE_OK`
- **Options:** `num_ctx=512`, `num_predict=16`, `temperature=0`, one request at a time
- **Timeout (client):** 300.0 s (suitable for load/CPU offloading)
- **Start time (local):** `2026-11-09T23:46:33+0530`
- **End time (local):** `2026-11-09T23:47:18+0530`
- **Elapsed:** **45.024 s**
- **Recorded output (`response`, repr):** `'AISMA_INFERENCE_OK\n\n(Note: "'`
- **Metadata:** `eval_count=16`, `prompt_eval_count=24`, `total_duration_ns=42961405400`, `load_duration_ns=23774894700`, `done_reason=length`
- **Result:** **SUCCESSFUL real local generation** with recorded output and latency. The required marker `AISMA_INFERENCE_OK` appears at the start of the response. Output was truncated by the small `num_predict` limit (`done_reason=length`), which is expected given the controlled small-output setting.

### 3.2 Structured JSON output — **SUCCESS** (real)
- **Model:** `phi3.5:latest`
- **Prompt:** `Return JSON only: {"status":"ok","value":1}` with `format=json`
- **Options:** `num_ctx=512`, `num_predict=64`, `temperature=0`
- **Start:** `2026-11-09T23:47:50+0530`, **elapsed:** **2.613 s**
- **Output:** `{\n  "status": "ok",\n  "value": 1\n}`
- **JSON parse:** **OK** (`{'status': 'ok', 'value': 1}`)
- **Result:** **SUCCESS**.

### 3.3 Short classification request — **SUCCESS** (real)
- **Model:** `phi3.5:latest`
- **Prompt:** sentiment classification, return JSON `{"label":"positive|negative"}` for text `"I love this product."`, with `format=json`
- **Options:** `num_ctx=512`, `num_predict=48`, `temperature=0`
- **Start:** `2026-11-09T23:47:53+0530`, **elapsed:** **21.220 s**
- **Output:** `{"label":"positive"}`
- **JSON parse:** **OK** (`{'label': 'positive'}`)
- **Result:** **SUCCESS** (correct label for the trivial case).

### 3.4 Previous failed/partial real observations (factual, not erased)

| Test | Model | Setting | Outcome | Diagnosis |
|---|---|---|---|---|
| Optional smoke (earlier session) | `qwen3.5:4b` | `max_tokens=32`, 60s timeout | **FAILED (timeout)** | `OllamaTimeoutError` after ~60s. Likely **memory pressure + model load/warmup/CPU offloading latency** under constrained RAM (low available) and 4GB VRAM; timeout too short for that state. Timeout handling behaved correctly. |
| Recovery probe 1 | `qwen3.5:4b` (already loaded) | `num_ctx=512`, `num_predict=16`, 300s | **Completed but empty `response`** (31.035s) | Raw included `thinking` and `done`; `qwen3.5:4b` used generation budget on **thinking** output; no final `response` field content. Inference executed, but output channel/format unsuitable for this small-budget config. |
| Recovery probe 2 | `qwen3.5:4b` (loaded) | `num_ctx=512`, `num_predict=128`, 300s | **Completed but empty `response`** (16.480s) | `eval_count=128`, `prompt_eval_count=19`, `done_reason=length`, `thinking` populated. Confirms **thinking-token budget consumption** caused truncation before `response` for this model/config. Not a server crash; not primarily timeout; model/config behavior under small output budget. |

## 4. Diagnosis summary
- **Server state:** Ollama was available and responding (`/api/tags`, `/api/ps`, successful generations on `phi3.5:latest`). No evidence of server crash during successful runs.
- **Model loading/offload:** `phi3.5:latest` successful run showed large `load_duration_ns` (~23.77s of 42.96s total), consistent with **model load/placement/offloading** cost on constrained hardware.
- **Memory pressure:** Low available RAM (~1.8 GB) and 4 GB VRAM create sensitivity; swap in use. This plausibly contributed to earlier timeout/slowness and to load latency.
- **Timeout configuration:** 60s was insufficient in the earlier constrained state; **300s** with small context/output was sufficient for controlled recovery.
- **Model/config behavior (`qwen3.5:4b`):** “thinking” capability can consume `num_predict` before populating `response` in `/api/generate` output shape; this is a **model-output/config interaction**, not a transport failure. Recovery used `phi3.5:latest` to satisfy the controlled minimal-output requirement.
- **No security controls weakened:** timeouts retained, no auto model pulls, kill-switch/injection protections not disabled.

## 5. Required benchmark dimensions — evidence status (updated)

| Dimension | Evidence status |
|---|---|
| Response latency | **Partial (real)** — successful controlled generations recorded: 45.024s (includes load), 2.613s (JSON, warm-ish), 21.220s (classification). Not a broad latency distribution. |
| Tokens/second | **Partial/derivable (real)** — metadata captured (`eval_count`, `prompt_eval_count`, durations) for successful/attempted runs; not summarized as a formal tokens/sec benchmark across workloads. |
| Memory consumption | **Partial (observed)** — RAM/GPU snapshots and Ollama `size_vram` observed; no controlled per-inference memory profiler trace. |
| Structured-output reliability | **Limited real success** — 1/1 JSON-format request parsed successfully on `phi3.5:latest` in this recovery; **not statistically benchmarked**. |
| Content quality | **Not benchmarked** (beyond minimal instruction compliance). |
| Classification accuracy | **Limited real success** — 1/1 trivial sentiment case correct; **not benchmarked**. |

## 6. Mocked/deterministic regression status (after recovery work)
- `python -m pytest -q` → **38 passed, 1 skipped** (optional real test skipped by default).
- `python -m ruff check src tests` → **All checks passed**.
- No Phase 1/Phase 2 source modules were modified for this recovery; report updated with actual results only.

## 7. Recommendations
1. Use `phi3.5:latest` as a conservative *verified-working local candidate* for 4 GB VRAM/minimal-output checks on this machine **after exact licence verification**; treat as provisional until broader benchmarks are run.
2. For `qwen3.5:4b` (thinking-capable), configure/test with adequate output budget or model-specific “thinking” controls only if verified in the target Ollama/model version; validate where final answer appears (`response` vs `thinking`).
3. Keep `num_ctx`/`num_predict` small on 4 GB VRAM, one request at a time, and timeouts generous for cold loads (>=300s when memory pressure is high).
4. Run broader benchmarks (latency distribution, tokens/sec, structured-output reliability rate, content/classification quality, memory profiling) only when RAM/VRAM pressure is reduced and models are warm; record actual measurements.
5. Do not select `qwen3.5:9b` for routine 4 GB VRAM operation. Do not use `qwen2.5-coder:1.5b-base` for instruction/chat tasks.
