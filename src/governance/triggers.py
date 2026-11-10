from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TriggerResult:
    trigger_id: str
    fired: bool
    reason: str
    idempotency_key: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "fired": self.fired,
            "reason": self.reason,
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
        }


def idempotency_key(trigger_id: str, business_id: str, subject: str, window: str = "") -> str:
    raw = json.dumps(
        {"trigger_id": trigger_id, "business_id": business_id, "subject": subject, "window": window},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class TriggerEngine:
    """Evaluates deterministic triggers. No LLM involvement."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict[str, Any]], TriggerResult]] = {}
        self.register("ranking_drop", self._ranking_drop)
        self.register("negative_review", self._negative_review)
        self.register("high_intent_lead", self._high_intent_lead)
        self.register("budget_threshold", self._budget_threshold)

    def register(self, trigger_id: str, handler: Callable[[dict[str, Any]], TriggerResult]) -> None:
        self._handlers[trigger_id] = handler

    def evaluate(self, trigger_id: str, event: dict[str, Any]) -> TriggerResult:
        if trigger_id not in self._handlers:
            raise KeyError(f"Unknown trigger: {trigger_id}")
        return self._handlers[trigger_id](event)

    def _ranking_drop(self, event: dict[str, Any]) -> TriggerResult:
        business_id = str(event.get("business_id", ""))
        keyword = str(event.get("keyword", ""))
        prev = float(event.get("previous_position", 0) or 0)
        curr = float(event.get("current_position", 0) or 0)
        threshold = float(event.get("drop_threshold", 3) or 3)
        drop = curr - prev if prev > 0 and curr > 0 else 0.0
        fired = drop >= threshold
        key = idempotency_key("ranking_drop", business_id, keyword, str(event.get("window", "")))
        return TriggerResult(
            "ranking_drop",
            fired,
            f"drop={drop}, threshold={threshold}",
            key,
            {"keyword": keyword, "previous_position": prev, "current_position": curr, "drop": drop},
        )

    def _negative_review(self, event: dict[str, Any]) -> TriggerResult:
        business_id = str(event.get("business_id", ""))
        review_id = str(event.get("review_id", ""))
        rating = float(event.get("rating", 5) or 5)
        sentiment = str(event.get("sentiment", "")).lower()
        fired = rating <= 2 or sentiment in {"negative", "very_negative"}
        key = idempotency_key("negative_review", business_id, review_id)
        return TriggerResult(
            "negative_review",
            fired,
            f"rating={rating}, sentiment={sentiment}",
            key,
            {"review_id": review_id, "rating": rating, "requires_human_approval": True},
        )

    def _high_intent_lead(self, event: dict[str, Any]) -> TriggerResult:
        business_id = str(event.get("business_id", ""))
        lead_id = str(event.get("lead_id", ""))
        score = float(event.get("intent_score", 0) or 0)
        threshold = float(event.get("threshold", 0.75) or 0.75)
        fired = score >= threshold
        key = idempotency_key("high_intent_lead", business_id, lead_id)
        return TriggerResult(
            "high_intent_lead",
            fired,
            f"intent_score={score}, threshold={threshold}",
            key,
            {"lead_id": lead_id, "intent_score": score},
        )

    def _budget_threshold(self, event: dict[str, Any]) -> TriggerResult:
        business_id = str(event.get("business_id", ""))
        ratio = float(event.get("usage_ratio", 0) or 0)
        threshold = float(event.get("threshold", 0.9) or 0.9)
        fired = ratio >= threshold
        window = str(event.get("date", ""))
        key = idempotency_key("budget_threshold", business_id, "budget", window)
        return TriggerResult(
            "budget_threshold",
            fired,
            f"usage_ratio={ratio}, threshold={threshold}",
            key,
            {"usage_ratio": ratio},
        )
