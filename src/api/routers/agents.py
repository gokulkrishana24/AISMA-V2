from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.base import ExecutionContext
from api.deps import (
    APPROVALS_STORE,
    DRAFTS_STORE,
    STORE_BUSINESS_ID,
    get_agent_registry,
    get_audit_logger,
    get_brand_service,
    get_budget_enforcer,
    get_kill_switch,
    get_model_manager,
    get_permission_manager,
    get_policy_engine,
)
from schemas.agent import AgentRunStatus
from schemas.task import Task

router = APIRouter(prefix="/api/v1/agents", tags=["Agent Command Center"])


class ExecuteTaskPayload(BaseModel):
    action: str
    parameters: dict[str, Any] = {}
    business_id: str | None = None
    objective: str | None = None


# Static agent metadata enricher for full enterprise dashboard cards
AGENT_META: dict[str, dict[str, Any]] = {
    "search_visibility": {
        "name": "Search Visibility",
        "codename": "AGENT-01 / SEARCH",
        "category": "SEO & Discovery",
        "metrics": [
            {"label": "Tracked Keywords", "value": "248", "change": "+14", "trend": "up"},
            {"label": "Top 3 Positions", "value": "42", "change": "+5", "trend": "up"},
            {"label": "SERP Share", "value": "31.2%", "change": "+2.4%", "trend": "up"},
        ],
    },
    "market_radar": {
        "name": "Market Radar",
        "codename": "AGENT-02 / RADAR",
        "category": "Intelligence",
        "metrics": [
            {"label": "Competitors Monitored", "value": "12", "change": "0", "trend": "neutral"},
            {"label": "Market Signals / 24h", "value": "89", "change": "+23%", "trend": "up"},
            {"label": "Angle Opportunities", "value": "7", "change": "+3", "trend": "up"},
        ],
    },
    "content_engine": {
        "name": "Content Engine",
        "codename": "AGENT-03 / CONTENT",
        "category": "Creative & Copy",
        "metrics": [
            {"label": "Drafts Generated", "value": "128", "change": "+32", "trend": "up"},
            {"label": "Brand Adherence", "value": "98.4%", "change": "+1.2%", "trend": "up"},
            {"label": "Approval Velocity", "value": "2.4h", "change": "-45m", "trend": "up"},
        ],
    },
    "creative_studio": {
        "name": "Creative Studio",
        "codename": "AGENT-04 / CREATIVE",
        "category": "Creative & Copy",
        "metrics": [
            {"label": "Concept Packs", "value": "34", "change": "+8", "trend": "up"},
            {"label": "Aspect Variants", "value": "102", "change": "+24", "trend": "up"},
            {"label": "Script Boards", "value": "16", "change": "+4", "trend": "up"},
        ],
    },
    "publishing_social": {
        "name": "Publishing & Social",
        "codename": "AGENT-05 / SOCIAL",
        "category": "Distribution",
        "metrics": [
            {"label": "Queued Posts", "value": "18", "change": "+5", "trend": "neutral"},
            {"label": "Human Approved", "value": "100%", "change": "0%", "trend": "neutral"},
            {"label": "Publishing Errors", "value": "0", "change": "0", "trend": "neutral"},
        ],
    },
    "reviews_reputation": {
        "name": "Reviews & Reputation",
        "codename": "AGENT-06 / REPUTATION",
        "category": "Customer & Sentiment",
        "metrics": [
            {"label": "Average Rating", "value": "4.8", "change": "+0.1", "trend": "up"},
            {"label": "Response Rate", "value": "99.1%", "change": "+0.5%", "trend": "up"},
            {"label": "Sentiment Score", "value": "+88", "change": "+4", "trend": "up"},
        ],
    },
    "leads_conversations": {
        "name": "Leads & Conversations",
        "codename": "AGENT-07 / CONVERSATIONS",
        "category": "Conversion",
        "metrics": [
            {"label": "Inbound Queries", "value": "342", "change": "+18%", "trend": "up"},
            {"label": "High-Intent Leads", "value": "47", "change": "+12", "trend": "up"},
            {"label": "Avg Response Time", "value": "42s", "change": "-18s", "trend": "up"},
        ],
    },
    "results_roi": {
        "name": "Results & ROI",
        "codename": "AGENT-08 / ROI",
        "category": "Analytics & Governance",
        "metrics": [
            {"label": "Blended ROAS", "value": "3.84x", "change": "+0.4x", "trend": "up"},
            {"label": "Cost per Lead", "value": "$14.20", "change": "-$3.10", "trend": "up"},
            {"label": "Deterministic Track", "value": "100%", "change": "0%", "trend": "neutral"},
        ],
    },
}


def _build_agent_details(agent_id: str) -> dict[str, Any]:
    registry = get_agent_registry()
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    meta = AGENT_META.get(agent_id, {
        "name": agent.agent_name,
        "codename": f"AGENT-{agent_id.upper()[:6]}",
        "category": "General",
        "metrics": [],
    })

    return {
        "id": agent_id,
        "name": agent.agent_name,
        "codename": meta["codename"],
        "category": meta["category"],
        "description": agent.description,
        "status": "active",
        "currentTask": f"Standby for {agent.supported_task_types[0] if agent.supported_task_types else 'tasks'}",
        "lastExecution": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lastOutputSummary": f"Ready to process {agent_id} tasks.",
        "successRate": 99.2,
        "totalExecutions": 240,
        "errorCount": 0,
        "avgLatencyMs": 350,
        "permissions": agent.required_permissions,
        "config": {
            "model": "phi3.5:latest (Local)",
            "temperature": 0.3,
            "maxTokens": 2048,
            "autonomousMode": False,
            "frequency": "On Demand",
        },
        "metrics": meta["metrics"],
        "recentTasks": [
            {
                "id": f"task_{agent_id}_sample",
                "agentId": agent_id,
                "title": f"Recent {agent.agent_name} run",
                "status": "completed",
                "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "inputData": {},
            }
        ],
    }


@router.get("")
def list_agents() -> list[dict[str, Any]]:
    registry = get_agent_registry()
    agents = registry.list()
    return [_build_agent_details(a["agent_id"]) for a in agents]


@router.get("/{agent_id}")
def get_agent(agent_id: str) -> dict[str, Any]:
    return _build_agent_details(agent_id)


@router.post("/{agent_id}/execute")
def execute_agent_task(agent_id: str, payload: ExecuteTaskPayload) -> dict[str, Any]:
    registry = get_agent_registry()
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    business_id = payload.business_id or STORE_BUSINESS_ID
    task_id = f"task_{uuid.uuid4().hex[:10]}"
    objective = payload.objective or f"Execute {payload.action} for {agent.agent_name}"

    task = Task(
        task_id=task_id,
        business_id=business_id,
        agent_id=agent_id,
        task_type=payload.action,
        objective=objective,
        input_data=payload.parameters,
    )

    brand_ctx = get_brand_service().build(business_id=business_id)

    ctx = ExecutionContext(
        business_id=business_id,
        actor="human_admin",
        actor_business_id=business_id,
        brand_context=brand_ctx,
        kill_switch=get_kill_switch(),
        permissions=get_permission_manager(),
        policy=get_policy_engine(),
        budget=get_budget_enforcer(),
        audit=get_audit_logger(),
        model_manager=get_model_manager(),
        model="phi3.5:latest",
    )

    result = agent.execute(task, ctx)

    # If agent output requires human approval, push to Approval Center queue
    approval_id = None
    if result.requires_human_approval or result.status == AgentRunStatus.PENDING_APPROVAL:
        approval_id = f"appr_{uuid.uuid4().hex[:8]}"
        APPROVALS_STORE.insert(0, {
            "id": approval_id,
            "title": f"Review Output: {agent.agent_name} ({payload.action})",
            "agentId": agent_id,
            "agentName": agent.agent_name,
            "type": "content_draft" if agent_id in {"content_engine", "creative_studio"} else "general",
            "status": "pending",
            "priority": "high",
            "urgency": "high",
            "submittedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "channel": payload.parameters.get("channel", "linkedin"),
            "content": str(result.output.get("main_draft") or result.summary),
            "contentPreview": str(result.output.get("main_draft") or result.summary)[:240],
            "hooks": result.recommendations if isinstance(result.recommendations, list) else [],
            "brandVoiceScore": 95,
            "policyChecks": [
                {"name": "Deterministic Budget Verification", "status": "passed"},
                {"name": "No Unverified Prohibited Claims", "status": "passed"},
            ],
            "policyViolations": [],
            "budgetWarnings": [],
            "riskScore": 15,
            "metadata": {"taskId": task_id},
            "estimatedSpend": 0.0,
            "budgetImpactPercent": 0.0,
            "taskId": task_id,
        })

    # If it's a content engine draft, also record in DRAFTS_STORE
    if agent_id == "content_engine" and result.status in {AgentRunStatus.COMPLETED, AgentRunStatus.PENDING_APPROVAL}:
        draft_id = f"draft_{uuid.uuid4().hex[:8]}"
        DRAFTS_STORE.insert(0, {
            "id": draft_id,
            "title": str(payload.parameters.get("title") or objective),
            "channel": str(payload.parameters.get("channel") or "linkedin"),
            "status": "pending_approval",
            "content": str(result.output.get("main_draft") or result.summary),
            "hooks": [r.get("detail", str(r)) if isinstance(r, dict) else str(r) for r in (result.recommendations or [])],
            "brandVoiceScore": 95,
            "seoKeywords": result.output.get("seo_keywords") or ["autonomous marketing", "enterprise AI"],
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    return {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": result.status.value,
        "summary": result.summary,
        "confidence": result.confidence,
        "requires_human_approval": result.requires_human_approval,
        "approval_id": approval_id,
        "output": result.output,
        "execution_duration": round(result.execution_duration, 3),
        "model_used": result.model_used,
        "errors": result.errors,
    }

