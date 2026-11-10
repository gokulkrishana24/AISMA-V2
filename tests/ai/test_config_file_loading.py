"""Regression tests for the optional YAML AI configuration overlay.

These cover the defect where ``src/api/deps.py`` passed a ``pathlib.Path`` to
``load_ai_config()`` (which expects an environment mapping), so the presence of
``config/ai_config.yaml`` crashed backend startup.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.config import AIConfigError, load_ai_config_file, validate_ai_config


def _write(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_missing_config_file_uses_environment(tmp_path: Path) -> None:
    cfg = load_ai_config_file(
        tmp_path / "does_not_exist.yaml",
        environ={"AISMA_DEFAULT_MODEL": "env-model", "AISMA_MAX_TOKENS": "512"},
    )
    assert cfg.default_model == "env-model"
    assert cfg.max_tokens == 512


def test_empty_config_file_uses_environment(tmp_path: Path) -> None:
    path = _write(tmp_path / "ai_config.yaml", "")
    cfg = load_ai_config_file(path, environ={"AISMA_DEFAULT_MODEL": "env-model"})
    assert cfg.default_model == "env-model"


def test_yaml_overlays_environment_and_keeps_extra_keys(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "ai_config.yaml",
        """
service:
  owner: platform-team
ollama_endpoint: http://127.0.0.1:11434
default_model: qwen3.5:4b
max_tokens: 2048
temperature: 0.4
cpu_fallback_enabled: false
""",
    )
    cfg = load_ai_config_file(path, environ={"AISMA_MAX_TOKENS": "256"})

    # YAML wins for keys it declares, environment is preserved otherwise.
    assert cfg.max_tokens == 2048
    assert cfg.default_model == "qwen3.5:4b"
    assert cfg.temperature == 0.4
    assert cfg.cpu_fallback_enabled is False
    assert cfg.extra == {"service": {"owner": "platform-team"}}


@pytest.mark.parametrize(
    ("body", "expected_fragment"),
    [
        ("- not\n- a\n- mapping\n", "must contain a YAML mapping"),
        ("default_model: [unclosed\n", "Unable to read AI config file"),
        ("temperature: 9.0\n", "temperature must be between"),
        ("gpu_preference: tpu\n", "gpu_preference must be one of"),
        ("max_tokens: many\n", "must be an integer"),
        ("concurrency_limit: 0\n", "concurrency_limit must be at least 1"),
        ("ollama_endpoint: localhost:11434\n", "ollama_endpoint must be an http"),
    ],
)
def test_invalid_config_file_raises(tmp_path: Path, body: str, expected_fragment: str) -> None:
    path = _write(tmp_path / "ai_config.yaml", body)
    with pytest.raises(AIConfigError) as err:
        load_ai_config_file(path, environ={})
    assert expected_fragment in str(err.value)


def test_validate_ai_config_reports_all_problems() -> None:
    from ai.config import AIConfig

    bad = AIConfig(ollama_endpoint="ftp://nope", gpu_preference="tpu", temperature=5.0)
    with pytest.raises(AIConfigError) as err:
        validate_ai_config(bad)
    message = str(err.value)
    assert "ollama_endpoint" in message
    assert "gpu_preference" in message
    assert "temperature" in message


# --- deps.py startup regression -------------------------------------------------


@pytest.fixture
def deps_sandbox(monkeypatch, tmp_path: Path):
    from api import deps

    monkeypatch.setattr(deps, "BASE_DIR", tmp_path)
    monkeypatch.setattr(deps, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(deps, "_model_manager", None)
    monkeypatch.setattr(deps, "_kill_switch", None)
    return deps, tmp_path


def test_model_manager_starts_with_config_file_present(deps_sandbox) -> None:
    deps, tmp_path = deps_sandbox
    (tmp_path / "config").mkdir()
    _write(
        tmp_path / "config" / "ai_config.yaml",
        "default_model: yaml-model\ngpu_preference: cpu_only\n",
    )

    manager = deps.get_model_manager()

    assert manager.config.default_model == "yaml-model"
    assert manager.config.gpu_preference == "cpu_only"


def test_model_manager_starts_with_config_file_absent(deps_sandbox) -> None:
    deps, tmp_path = deps_sandbox

    manager = deps.get_model_manager()

    assert manager.config.ollama_endpoint.startswith("http")
    assert manager.config.default_model
    assert not (tmp_path / "config").exists()
