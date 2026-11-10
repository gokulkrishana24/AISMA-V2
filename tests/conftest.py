from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Ensure fast deterministic test execution and isolate test SQLite DB away from live state/aisma.db
os.environ.setdefault("AISMA_TEST_MODE", "true")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
if "DATABASE_URL" not in os.environ and os.environ.get("AISMA_USE_LIVE_DB") != "1":
    _test_db = (Path(tempfile.gettempdir()) / f"aisma_pytest_{os.getpid()}.db").as_posix()
    os.environ["DATABASE_URL"] = f"sqlite:///{_test_db}"

import pytest

from governance.audit import AuditLogger
from governance.budget import BudgetEnforcer, BudgetLimits
from governance.killswitch import KillSwitch
from governance.permissions import PermissionManager
from governance.policy import PolicyEngine


@pytest.fixture
def tmp_state(tmp_path: Path) -> Path:
    return tmp_path / "state"


@pytest.fixture
def audit_logger(tmp_path: Path) -> AuditLogger:
    return AuditLogger(tmp_path / "audit")


@pytest.fixture
def kill_switch(tmp_path: Path) -> KillSwitch:
    return KillSwitch(tmp_path / "killswitch")


@pytest.fixture
def permission_manager() -> PermissionManager:
    return PermissionManager()


@pytest.fixture
def budget_enforcer(tmp_path: Path) -> BudgetEnforcer:
    enf = BudgetEnforcer(tmp_path / "budget", strict=True)
    enf.set_limits(
        "biz1",
        BudgetLimits(max_tokens_per_day=1000, max_actions_per_day=10, max_cost_units_per_day=5.0),
    )
    return enf


@pytest.fixture
def policy_engine() -> PolicyEngine:
    return PolicyEngine({"default_deny_publishing": True})
