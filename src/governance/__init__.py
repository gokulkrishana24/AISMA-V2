"""Governance engine for the AI-Native Social Media Agent Team v2.

Security and policy enforcement are implemented in Python code (fail-closed).
LLM outputs are untrusted inputs and must pass governance checks before use.
"""

from .audit import AuditLogger, verify_audit_chain
from .budget import BudgetEnforcer, BudgetExceededError
from .frontmatter import FrontmatterError, parse_frontmatter, validate_frontmatter
from .injection import InjectionScanError, scan_untrusted_text
from .killswitch import KillSwitch, KillSwitchEngagedError
from .permissions import PermissionDeniedError, PermissionManager
from .policy import PolicyEngine, PolicyViolationError
from .preflight import PreflightError, run_preflight
from .scoring import score_opportunity
from .triggers import TriggerEngine

__all__ = [
    "AuditLogger",
    "BudgetEnforcer",
    "BudgetExceededError",
    "FrontmatterError",
    "InjectionScanError",
    "KillSwitch",
    "KillSwitchEngagedError",
    "PermissionDeniedError",
    "PermissionManager",
    "PolicyEngine",
    "PolicyViolationError",
    "PreflightError",
    "TriggerEngine",
    "parse_frontmatter",
    "run_preflight",
    "scan_untrusted_text",
    "score_opportunity",
    "validate_frontmatter",
    "verify_audit_chain",
]
