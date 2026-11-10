from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/budget", tags=["Budget Management"])


@router.get("")
def get_budget_overview() -> dict[str, Any]:
    return {
        "monthlyBudget": 15000.0,
        "currentSpend": 4820.50,
        "forecastSpend": 14200.0,
        "isOverCap": False,
        "capAlertThreshold": 12000.0,
        "spentThisMonth": 4820.50,
        "remainingBudget": 10179.50,
        "burnRateDaily": 160.68,
        "projectedMonthEndSpend": 14200.0,
        "utilizationPercent": 32.1,
        "currency": "USD",
        "overCapWarning": False,
        "channelBreakdown": [
            {"channel": "LinkedIn", "allocated": 6000.0, "spent": 2400.0, "roas": 5.75},
            {"channel": "Twitter / X", "allocated": 4000.0, "spent": 1200.0, "roas": 4.55},
            {"channel": "Content Production", "allocated": 3000.0, "spent": 820.50, "roas": 6.10},
            {"channel": "SEO Discovery", "allocated": 2000.0, "spent": 400.0, "roas": 8.40},
        ],
        "agentSpendBreakdown": [
            {"agentId": "search_visibility", "spent": 400.0, "tokenCost": 0.0},
            {"agentId": "content_engine", "spent": 820.50, "tokenCost": 0.0},
            {"agentId": "publishing_social", "spent": 2400.0, "tokenCost": 0.0},
            {"agentId": "results_roi", "spent": 1200.0, "tokenCost": 0.0},
        ],
        "spendingByChannel": [
            {"channel": "LinkedIn", "spent": 2400.0, "budget": 6000.0, "percentage": 40.0},
            {"channel": "Twitter / X", "spent": 1200.0, "budget": 4000.0, "percentage": 30.0},
            {"channel": "Content Engine Production", "spent": 820.50, "budget": 3000.0, "percentage": 27.3},
            {"channel": "SEO Discovery Ops", "spent": 400.0, "budget": 2000.0, "percentage": 20.0},
        ],
        "recentTransactions": [
            {
                "id": "tx_001",
                "date": "2026-11-09",
                "description": "Content Engine Inference & Keyword Ops",
                "channel": "Production",
                "amount": 24.50,
                "status": "approved",
            },
            {
                "id": "tx_002",
                "date": "2026-11-08",
                "description": "LinkedIn Enterprise Campaign Batch A",
                "channel": "LinkedIn",
                "amount": 450.0,
                "status": "approved",
            },
        ],
    }
