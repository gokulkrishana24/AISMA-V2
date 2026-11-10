from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResult:
    model: str
    text: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None


class LLMProvider(ABC):
    """Unified interface for local/open-weight LLM runtimes.

    Implementations must not call paid/proprietary AI APIs.
    """

    provider_name: str = "base"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> LLMResult | Iterator[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> LLMResult | Iterator[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def classify(
        self,
        text: str,
        labels: list[str],
        *,
        model: str | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        raise NotImplementedError

    @abstractmethod
    def summarize(
        self,
        text: str,
        *,
        model: str | None = None,
        max_points: int = 5,
        **kwargs: Any,
    ) -> LLMResult:
        raise NotImplementedError

    @abstractmethod
    def extract_structured(
        self,
        text: str,
        schema: dict[str, Any],
        *,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> list[dict[str, Any]]:
        raise NotImplementedError
