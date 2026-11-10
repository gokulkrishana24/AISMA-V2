from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Deterministic scoring: no randomness, no LLM calls.
DEFAULT_WEIGHTS = {
    "business_impact": 0.30,
    "urgency": 0.20,
    "confidence": 0.20,
    "effort_inverse": 0.10,
    "risk_inverse": 0.10,
    "strategic_fit": 0.10,
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class OpportunityScore:
    total: float
    components: dict[str, float]
    weights: dict[str, float]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": round(self.total, 6),
            "components": {k: round(v, 6) for k, v in self.components.items()},
            "weights": self.weights,
            "rationale": self.rationale,
        }


def score_opportunity(
    *,
    business_impact: float,
    urgency: float,
    confidence: float,
    effort: float,
    risk: float,
    strategic_fit: float,
    weights: dict[str, float] | None = None,
    context: str = "",
) -> OpportunityScore:
    """Score an opportunity on a 0..1 scale using deterministic weighted factors.

    Inputs are expected on 0..1 (or 0..100, auto-normalized). effort/risk are costs,
    so they are inverted.
    """
    w = dict(weights or DEFAULT_WEIGHTS)

    def norm(v: float) -> float:
        x = float(v)
        if x > 1.0:
            x = x / 100.0
        return _clamp(x)

    components = {
        "business_impact": norm(business_impact),
        "urgency": norm(urgency),
        "confidence": norm(confidence),
        "effort_inverse": 1.0 - norm(effort),
        "risk_inverse": 1.0 - norm(risk),
        "strategic_fit": norm(strategic_fit),
    }
    # Normalize weights defensively.
    weight_sum = sum(w.get(k, 0.0) for k in components)
    if weight_sum <= 0:
        raise ValueError("weights must sum to a positive value")
    total = sum(components[k] * (w.get(k, 0.0) / weight_sum) for k in components)
    rationale = (
        "Deterministic weighted score from impact/urgency/confidence/effort/risk/strategic_fit"
    )
    if context:
        rationale += f"; context={context}"
    return OpportunityScore(
        total=_clamp(total),
        components=components,
        weights={k: w.get(k, 0.0) / weight_sum for k in components},
        rationale=rationale,
    )
