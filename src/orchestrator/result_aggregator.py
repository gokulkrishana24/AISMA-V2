from __future__ import annotations

from typing import Any

from schemas.agent import AgentResult


class ResultAggregator:
    def aggregate(self, results: list[AgentResult]) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
        errors: list[str] = []
        approvals: list[str] = []
        for r in results:
            findings.extend({"agent_id": r.agent_id, **f} if isinstance(f, dict) else {"agent_id": r.agent_id, "item": f} for f in r.findings)
            recommendations.extend({"agent_id": r.agent_id, **x} if isinstance(x, dict) else {"agent_id": r.agent_id, "item": x} for x in r.recommendations)
            risks.extend({"agent_id": r.agent_id, **x} if isinstance(x, dict) else {"agent_id": r.agent_id, "item": x} for x in r.risks)
            errors.extend([f"{r.agent_id}: {e}" for e in r.errors])
            if r.requires_human_approval:
                approvals.append(r.task_id)
        conflicts = self._detect_conflicts(results)
        return {
            "summary": f"Aggregated {len(results)} agent result(s)",
            "findings": findings,
            "recommendations": recommendations,
            "risks": risks,
            "errors": errors,
            "pending_approval_task_ids": approvals,
            "conflicts": conflicts,
        }

    def _detect_conflicts(self, results: list[AgentResult]) -> list[dict[str, Any]]:
        # Simple deterministic conflict detection: opposing high-priority channel guidance or duplicated contradictory statuses.
        conflicts: list[dict[str, Any]] = []
        publish = [r for r in results if r.agent_id == "publishing_social"]
        content = [r for r in results if r.agent_id == "content_engine"]
        if publish and content:
            for p in publish:
                detail = str(p.output)
                if "integration_not_configured" in detail and any(c.status.value == "completed" for c in content):
                    conflicts.append({
                        "type": "publishing_readiness",
                        "detail": "Content drafted but publishing integration is not configured; human/integration steps required.",
                        "agents": ["content_engine", "publishing_social"],
                    })
        return conflicts
