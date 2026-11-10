from ai.config import load_ai_config
from ai.hardware import detect_hardware, recommend_runtime_options
from ai.registry import ModelRegistry


def test_load_ai_config_from_env(monkeypatch) -> None:
    monkeypatch.setenv("AISMA_OLLAMA_ENDPOINT", "http://127.0.0.1:11434/")
    monkeypatch.setenv("AISMA_DEFAULT_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("AISMA_FALLBACK_MODEL", "phi3.5:latest")
    monkeypatch.setenv("AISMA_REQUEST_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("AISMA_MAX_TOKENS", "256")
    monkeypatch.setenv("AISMA_CONTEXT_LENGTH", "2048")
    monkeypatch.setenv("AISMA_CONCURRENCY_LIMIT", "2")
    monkeypatch.setenv("AISMA_CPU_FALLBACK_ENABLED", "true")
    cfg = load_ai_config()
    assert cfg.ollama_endpoint == "http://127.0.0.1:11434"
    assert cfg.default_model == "qwen3.5:4b"
    assert cfg.request_timeout_seconds == 45.0
    assert cfg.max_tokens == 256
    assert cfg.context_length == 2048
    assert cfg.concurrency_limit == 2
    assert cfg.cpu_fallback_enabled is True


def test_model_registry() -> None:
    reg = ModelRegistry()
    assert reg.get("phi3.5:latest") is not None
    rows = reg.to_dict()
    assert any(r["tag"] == "qwen3.5:4b" for r in rows)


def test_hardware_snapshot_and_runtime_options() -> None:
    snap = detect_hardware()
    d = snap.to_dict()
    assert "cpu_count" in d and "ram_total_mb" in d
    opts = recommend_runtime_options(
        gpu_preference="auto", gpu_memory_budget_mb=3072, context_length=8192, num_predict=512
    )
    assert opts["num_ctx"] >= 512
    assert opts["num_predict"] >= 1
    cpu_opts = recommend_runtime_options(
        gpu_preference="cpu_only", gpu_memory_budget_mb=3072, context_length=2048, num_predict=128
    )
    assert cpu_opts["num_gpu"] == 0
