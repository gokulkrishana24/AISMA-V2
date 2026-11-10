import pytest

from governance.budget import BudgetEnforcer, BudgetExceededError, BudgetLimits
from governance.policy import PolicyEngine
from governance.scoring import score_opportunity


def test_scoring_is_deterministic() -> None:
    a = score_opportunity(
        business_impact=0.9, urgency=0.7, confidence=0.8, effort=0.2, risk=0.1, strategic_fit=0.9
    )
    b = score_opportunity(
        business_impact=90, urgency=70, confidence=80, effort=20, risk=10, strategic_fit=90
    )
    assert a.total == b.total
    assert 0 <= a.total <= 1
    assert a.total > 0.5


def test_policy_default_deny_publishing(policy_engine: PolicyEngine) -> None:
    d = policy_engine.evaluate(
        "publish",
        actor="publishing_social",
        business_id="biz1",
        resource={"status": "approved"},
        has_human_approval=False,
    )
    assert d.allowed is False
    assert d.requires_human_approval is True
    allowed = policy_engine.evaluate(
        "publish",
        actor="publishing_social",
        business_id="biz1",
        resource={"status": "approved"},
        has_human_approval=True,
        lint_passed=True,
    )
    assert allowed.allowed is True


def test_negative_review_requires_approval(policy_engine: PolicyEngine) -> None:
    d = policy_engine.evaluate(
        "respond_negative_review",
        actor="reviews_reputation",
        business_id="biz1",
        has_human_approval=False,
    )
    assert d.allowed is False and d.requires_human_approval is True


def test_budget_enforcement(tmp_path) -> None:
    enf = BudgetEnforcer(tmp_path, strict=True)
    enf.set_limits("biz1", BudgetLimits(100, 2, 10.0))
    enf.check_and_reserve("biz1", tokens=10, actions=1, cost_units=1.0)
    with pytest.raises(BudgetExceededError):
        enf.check_and_reserve("biz1", tokens=1, actions=2, cost_units=0.0)
