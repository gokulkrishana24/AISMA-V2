# Environment Configuration Reference (Phase 2 AI)

Configuration is loaded by `ai.config.load_ai_config()` from environment variables. **Never hardcode secrets.**

| Variable | Default | Description |
|---|---:|---|
| `AISMA_OLLAMA_ENDPOINT` | `http://localhost:11434` | Local Ollama API base URL. |
| `AISMA_DEFAULT_MODEL` | `qwen3.5:4b` | Primary model tag. Must be verified/installed. |
| `AISMA_FALLBACK_MODEL` | `phi3.5:latest` | Fallback model tag. |
| `AISMA_REQUEST_TIMEOUT_SECONDS` | `120` | HTTP/inference timeout (seconds). |
| `AISMA_MAX_TOKENS` | `1024` | Default max generation tokens (`num_predict`). |
| `AISMA_CONTEXT_LENGTH` | `4096` | Requested context window (bounded conservatively for 4GB VRAM). |
| `AISMA_TEMPERATURE` | `0.2` | Sampling temperature. |
| `AISMA_CONCURRENCY_LIMIT` | `1` | Shared inference concurrency slots (recommended 1 on 4GB VRAM). |
| `AISMA_GPU_PREFERENCE` | `auto` | `auto`, `prefer_gpu`, or `cpu_only`. |
| `AISMA_GPU_MEMORY_BUDGET_MB` | `3072` | Conservative GPU memory budget hint. |
| `AISMA_CPU_FALLBACK_ENABLED` | `true` | Enables fallback model/error recovery selection. |
| `AISMA_ALLOW_MODEL_PULL` | `false` | Must be `true` **and** explicit authorization passed to allow pulls. |
| `AISMA_MAX_INPUT_CHARS` | `24000` | Input-size limit before untrusted LLM processing. |
| `AISMA_STREAMING_ENABLED` | `true` | Streaming capability flag/configuration hint. |
| `AISMA_RUN_REAL_OLLAMA_TESTS` | unset/false | Opt-in for real Ollama pytest smoke (`tests/ai/test_real_ollama_optional.py`). |

## Deployment notes
- Keep Ollama bound to local/trusted interfaces unless network controls are in place.
- Use OS/service environment configuration for deployment-specific values.
- Validate configuration at startup using governance preflight checks where applicable.
- All privileged/sensitive actions triggered by model outputs must go through Phase 1 governance (kill switch, permissions, policy, audit, approval).
