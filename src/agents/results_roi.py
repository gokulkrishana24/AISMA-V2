from __future__ import annotations

from typing import Any

from schemas.task import Task

from .base import BaseAgent, ExecutionContext


class ResultsROIAgent(BaseAgent):
    agent_id = "results_roi"
    agent_name = "Results & ROI Agent"
    description = "Deterministic marketing KPI/ROI calculations from supplied data."
    capabilities = ["roi_calculation", "kpi_summary", "channel_comparison", "trend_analysis"]
    supported_task_types = ["roi_analysis", "campaign_performance", "kpi_summary"]
    required_permissions = ["read_business_data", "read_analytics", "view_audit"]

    def validate_task(self, task: Task, context: ExecutionContext) -> None:
        if task.task_type not in self.supported_task_types:
            raise ValueError(f"Unsupported task_type: {task.task_type}")
        if task.business_id != context.business_id:
            raise PermissionError("Business isolation violation")

    @staticmethod
    def _to_num(v: Any) -> float | None:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _calculate(cls, metrics: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        missing: list[str] = []
        spend = cls._to_num(metrics.get("spend"))
        revenue = cls._to_num(metrics.get("revenue"))
        leads = cls._to_num(metrics.get("leads"))
        conversions = cls._to_num(metrics.get("conversions"))
        clicks = cls._to_num(metrics.get("clicks"))
        impressions = cls._to_num(metrics.get("impressions"))

        out: dict[str, Any] = {}
        if revenue is None or spend is None:
            out["roi"] = None
            missing.append("roi_requires_revenue_and_spend")
        elif spend == 0:
            out["roi"] = None
            missing.append("roi_undefined_spend_zero")
        else:
            out["roi"] = (revenue - spend) / spend
        if revenue is None or spend is None:
            out["roas"] = None
            missing.append("roas_requires_revenue_and_spend")
        elif spend == 0:
            out["roas"] = None
            missing.append("roas_undefined_spend_zero")
        else:
            out["roas"] = revenue / spend
        if spend is None or leads is None:
            out["cost_per_lead"] = None
            missing.append("cost_per_lead_requires_spend_and_leads")
        elif leads == 0:
            out["cost_per_lead"] = None
            missing.append("cost_per_lead_undefined_leads_zero")
        else:
            out["cost_per_lead"] = spend / leads
        if conversions is None or clicks is None:
            out["conversion_rate"] = None
            missing.append("conversion_rate_requires_conversions_and_clicks")
        elif clicks == 0:
            out["conversion_rate"] = None
            missing.append("conversion_rate_undefined_clicks_zero")
        else:
            out["conversion_rate"] = conversions / clicks
        if clicks is None or impressions is None:
            out["ctr"] = None
            missing.append("ctr_requires_clicks_and_impressions")
        elif impressions == 0:
            out["ctr"] = None
            missing.append("ctr_undefined_impressions_zero")
        else:
            out["ctr"] = clicks / impressions
        out["inputs"] = {"spend": spend, "revenue": revenue, "leads": leads, "conversions": conversions, "clicks": clicks, "impressions": impressions}
        return out, sorted(set(missing))

    def _execute_impl(self, task: Task, context: ExecutionContext) -> dict[str, Any]:
        metrics = task.input_data.get("metrics") or task.input_data
        if not isinstance(metrics, dict):
            metrics = {}
        calcs, missing = self._calculate(metrics)
        # Optional concise narrative via LLM, but never for numeric truth.
        narrative = "Deterministic ROI/KPI calculations completed from supplied metrics."
        try:
            schema = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}
            prompt = (
                f"{self._build_system_prompt(task, context)}\n"
                "Summarize these already-calculated metrics. Do NOT compute or invent numbers. Missing values must be marked.\n"
                f"CALCULATIONS: {calcs}\nMISSING: {missing}\nOBJECTIVE: {task.objective}"
            )
            data = self._llm_json(task, context, prompt, schema, retries=0)
            narrative = str(data.get("summary") or narrative)
        except Exception:
            pass
        return {
            "summary": narrative,
            "findings": [{"type": "kpi_calculations", "item": calcs}],
            "recommendations": [{"type": "data_quality", "detail": f"Missing/undefined: {missing}"}] if missing else [],
            "evidence": [{"type": "calculation", "detail": "Computed in Python from supplied metrics; no invented data."}],
            "confidence": 1.0 if not missing else 0.7,
            "risks": [{"type": "missing_data", "items": missing}] if missing else [],
            "requires_human_approval": False,
            "calculations": calcs,
            "missing_values": missing,
        }
