from __future__ import annotations

from typing import Any

from governance.scoring import score_opportunity


class OpportunityRanker:
    def rank(self, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ranked: list[dict[str, Any]] = []
        for i, opp in enumerate(opportunities):
            score = score_opportunity(
                business_impact=float(opp.get("business_impact", 0.5)),
                urgency=float(opp.get("urgency", 0.5)),
                confidence=float(opp.get("confidence", 0.5)),
                effort=float(opp.get("effort", 0.5)),
                risk=float(opp.get("risk", 0.3)),
                strategic_fit=float(opp.get("strategic_fit", 0.5)),
                context=str(opp.get("context") or f"opportunity_{i}"),
            )
            item = dict(opp)
            item["deterministic_score"] = score.to_dict()
            item["priority"] = max(1, min(10, round(score.total * 10)))
            ranked.append(item)
        ranked.sort(key=lambda x: (-(x.get("deterministic_score", {}).get("total", 0)), str(x.get("id", ""))))
        return ranked
