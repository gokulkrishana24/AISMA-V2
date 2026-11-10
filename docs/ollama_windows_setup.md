# Ollama Setup Guide (Windows)

This project uses **local** Ollama inference only. No paid/proprietary AI APIs.

## Prerequisites
- Windows 11 (development target)
- Python 3.12+
- Sufficient RAM/VRAM for selected model (4 GB VRAM is constrained; use quantized small models)
- Ollama for Windows installed

## Install Ollama
1. Download and install Ollama for Windows from the official Ollama distribution channel you trust.
2. After installation, confirm the service is available:
   ```bash
   curl http://localhost:11434/api/tags
   ```
   A JSON response with a `models` array indicates the local API is reachable.

Default endpoint used by this project: `http://localhost:11434` (override with `AISMA_OLLAMA_ENDPOINT`).

## Install a model (explicit authorization only)
The application **does not auto-download models**. Pull models only with explicit operator authorization.

Examples (run manually):
```bash
ollama pull phi3.5:latest
ollama pull qwen3.5:4b
```

Before using a model in production, verify:
- exact model tag exists locally (`ollama list` / `/api/tags`),
- runtime compatibility,
- memory footprint on target hardware,
- **exact licence** from the official model card/Ollama listing.

## Configuration
Environment variables (see `docs/environment_configuration.md`):
- `AISMA_OLLAMA_ENDPOINT=http://localhost:11434`
- `AISMA_DEFAULT_MODEL=qwen3.5:4b` (example; choose a verified installed model)
- `AISMA_FALLBACK_MODEL=phi3.5:latest`
- `AISMA_REQUEST_TIMEOUT_SECONDS=120`
- `AISMA_CONCURRENCY_LIMIT=1` (recommended for 4 GB VRAM shared service)

## Quick connectivity check (Python)
```python
from ai.ollama_client import OllamaClient
print(OllamaClient().health_check())
print(OllamaClient().list_models())
```

## Safety notes
- External/untrusted text is scanned by Phase 1 injection scanning before LLM processing.
- Kill switch and governance checks can block AI runtime operations.
- LLM outputs never directly execute privileged actions; sensitive operations must pass `PolicyEngine`/`PermissionManager`.
