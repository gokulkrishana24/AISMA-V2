from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelRecord:
    """Registry entry for a locally usable open-weight model.

    Licence and availability must be verified before production recommendation.
    Tags must be checked against the actual Ollama runtime (no assumptions).
    """

    tag: str
    family: str
    parameter_size: str
    license: str  # e.g., Apache-2.0, MIT (verify exact model card)
    quantization: str = ""
    context_length: int = 0
    approximate_size_gb: float = 0.0
    min_ram_gb: float = 4.0
    min_vram_gb: float = 0.0  # 0 means CPU/offload feasible
    strengths: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "family": self.family,
            "parameter_size": self.parameter_size,
            "license": self.license,
            "quantization": self.quantization,
            "context_length": self.context_length,
            "approximate_size_gb": self.approximate_size_gb,
            "min_ram_gb": self.min_ram_gb,
            "min_vram_gb": self.min_vram_gb,
            "strengths": self.strengths,
            "notes": self.notes,
        }


# Registry candidates. Actual availability/licence/runtime compatibility must be
# verified in the target environment before use/recommendation.
DEFAULT_MODEL_REGISTRY: list[ModelRecord] = [
    ModelRecord(
        tag="qwen3.5:4b",
        family="qwen3.5",
        parameter_size="4.2B",
        license="verify:model-card",  # Qwen model terms vary; verify before production claim
        quantization="Q4_K_M",
        context_length=262144,
        approximate_size_gb=3.3,
        min_ram_gb=8.0,
        min_vram_gb=0.0,
        strengths=["structured output", "tools", "multilingual", "small footprint"],
        notes="Observed in local Ollama during Phase 2 setup; verify exact licence/fitness.",
    ),
    ModelRecord(
        tag="phi3.5:latest",
        family="phi3",
        parameter_size="3.8B",
        license="MIT",
        quantization="Q4_0",
        context_length=131072,
        approximate_size_gb=2.2,
        min_ram_gb=6.0,
        min_vram_gb=0.0,
        strengths=["instruction following", "classification", "summarization", "small footprint"],
        notes="MIT-licensed Phi-3.5 mini family; verify local tag/runtime behavior.",
    ),
    ModelRecord(
        tag="qwen2.5-coder:1.5b-base",
        family="qwen2.5-coder",
        parameter_size="1.5B",
        license="Apache-2.0",
        quantization="Q4_K_M",
        context_length=32768,
        approximate_size_gb=1.0,
        min_ram_gb=4.0,
        min_vram_gb=0.0,
        strengths=["code completion", "low resource"],
        notes="Base/completion-oriented; not ideal for chat/marketing generation.",
    ),
]


class ModelRegistry:
    def __init__(self, records: list[ModelRecord] | None = None):
        self._records = {r.tag: r for r in (records or DEFAULT_MODEL_REGISTRY)}

    def get(self, tag: str) -> ModelRecord | None:
        return self._records.get(tag)

    def all(self) -> list[ModelRecord]:
        return list(self._records.values())

    def register(self, record: ModelRecord) -> None:
        self._records[record.tag] = record

    def to_dict(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.all()]
