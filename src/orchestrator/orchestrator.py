from __future__ import annotations

import uuid
from typing import Any

from agents.base import ExecutionContext
from agents.registry import AgentRegistry
from ai.model_manager import ModelManager
from governance.audit import AuditLogger
from governance.budget import BudgetEnforcer
from governance.killswitch import KillSwitch
from governance.permissions import (
    Action,
    PermissionContext,
    PermissionManager,
)
from governance.policy import PolicyEngine
from governance.preflight import run_preflight
from schemas.agent import AgentResult, AgentRunStatus
from schemas.brief import ExecutionBrief
from schemas.results import OrchestrationReport
from schemas.task import Task, TaskStatus

from .opportunity_ranker import OpportunityRanker
from .planner import TaskPlanner
from .result_aggregator import ResultAggregator
from .scheduler import Scheduler
from .task_manager import TaskManager


class Orchestrator:
    def __init__(
        self,
        *,
        registry: AgentRegistry,
        model_manager: ModelManager,
        permissions: PermissionManager | None = None,
        policy: PolicyEngine | None = None,
        kill_switch: KillSwitch | None = None,
        budget: BudgetEnforcer | None = None,
        audit: AuditLogger | None = None,
    ):
        self.registry = registry
        self.model_manager = model_manager
        self.permissions = permissions or PermissionManager()
        self.policy = policy or PolicyEngine({"default_deny_publishing": True})
        self.kill_switch = kill_switch
        self.budget = budget
        self.audit = audit
        self.task_manager = TaskManager()
        self.planner = TaskPlanner()
        self.scheduler = Scheduler()
        self.ranker = OpportunityRanker()
        self.aggregator = ResultAggregator()

    def _audit(self, business_id: str, actor: str, action: str, resource: str, outcome: str, details: dict[str, Any] | None = None) -> str | None:
        if not self.audit:
            return None
        return self.audit.log(business_id=business_id, actor=actor, action=action, resource=resource, outcome=outcome, details=details or {}).entry_hash

    def _preflight(self, required_paths: list[str] | None = None) -> dict[str, Any]:
        res = run_preflight(required_paths=required_paths or [], writable_paths=[], config_files={}, fail_closed=False)
        return res.to_dict()

    def execute(
        self,
        *,
        business_id: str,
        objective: str,
        tasks: list[Task | dict[str, Any]],
        context_data: dict[str, Any] | None = None,
        strategy: str = "dependency_based",
        opportunities: list[dict[str, Any]] | None = None,
        has_human_approval: bool = False,
    ) -> OrchestrationReport:
        report_id = str(uuid.uuid4())
        audit_ids: list[str] = []
        actor = "orchestrator"
        try:
            if not business_id:
                raise PermissionError("business_id is required")
            # preflight
            pre = self._preflight()
            # kill switch
            if self.kill_switch and self.kill_switch.is_engaged(business_id):
                raise PermissionError(f"Kill switch engaged for business {business_id}")
            # permissions for orchestration
            self.permissions.require(PermissionContext(business_id=business_id, actor=actor, actor_business_id=business_id), Action.READ_BUSINESS_DATA)

            task_objs: list[Task] = []
            for t in tasks:
                task = t if isinstance(t, Task) else Task.model_validate(t)
                if task.business_id != business_id:
                    raise PermissionError(f"Business isolation violation in task {task.task_id}")
                task_objs.append(self.task_manager.add(task))

            plan = self.planner.plan(task_objs, strategy=strategy)
            schedule = self.scheduler.schedule(plan)
            ranked = self.ranker.rank(opportunities or [])
            # priority alignment (deterministic)
            rank_map = {str(o.get("task_id") or o.get("id")): int(o.get("priority", 5)) for o in ranked}
            for task in task_objs:
                if task.task_id in rank_map:
                    # tasks are immutable pydantic; update through manager replacement
                    rec = self.task_manager._tasks[task.task_id]  # noqa: SLF001
                    rec.task = rec.task.model_copy(update={"priority": rank_map[task.task_id]})

            results: list[AgentResult] = []
            completed_ids: set[str] = set()
            # dependency-based batch execution, sequential within batches (concurrency=1)
            for batch in plan.get("batches") or []:
                for td in batch:
                    tid = td["task_id"]
                    task = self.task_manager.get(tid)
                    if not task:
                        continue
                    # dependency check
                    deps = [d for d in task.dependencies if d]
                    if any(d not in completed_ids for d in deps):
                        self.task_manager.set_status(tid, TaskStatus.BLOCKED, reason="dependencies_not_satisfied")
                        results.append(AgentResult(task_id=tid, agent_id=task.agent_id, status=AgentRunStatus.BLOCKED, summary="Blocked: dependencies not satisfied", confidence=0.0, errors=["dependencies_not_satisfied"]))
                        continue
                    agent = self.registry.get(task.agent_id)
                    if not agent:
                        self.task_manager.set_status(tid, TaskStatus.FAILED, reason="unknown_agent")
                        results.append(AgentResult(task_id=tid, agent_id=task.agent_id, status=AgentRunStatus.FAILED, summary="Unknown agent", confidence=0.0, errors=["unknown_agent"]))
                        continue
                    self.task_manager.set_status(tid, TaskStatus.VALIDATED, reason="orchestrator_validated")
                    self.task_manager.set_status(tid, TaskStatus.RUNNING, reason="orchestrator_running")
                    self.task_manager.increment_attempt(tid)
                    ctx = ExecutionContext(
                        business_id=business_id,
                        actor=actor,
                        actor_business_id=business_id,
                        kill_switch=self.kill_switch,
                        permissions=self.permissions,
                        policy=self.policy,
                        budget=self.budget,
                        audit=self.audit,
                        has_human_approval=has_human_approval,
                        model_manager=self.model_manager,
                        metadata=context_data or {},
                    )
                    # attach brand context if service provided via metadata hook
                    if (context_data or {}).get("brand_context_obj") is not None:
                        ctx.brand_context = context_data["brand_context_obj"]
                    result = agent.execute(task, ctx)
                    results.append(result)
                    if result.status == AgentRunStatus.COMPLETED:
                        self.task_manager.mark_result(tid, agent.serialize_result(result), TaskStatus.COMPLETED)
                        completed_ids.add(tid)
                    elif result.status == AgentRunStatus.PENDING_APPROVAL:
                        self.task_manager.mark_result(tid, agent.serialize_result(result), TaskStatus.PENDING_APPROVAL)
                        completed_ids.add(tid)  # allow dependents? conservative: treat as produced artifact needing approval
                    elif result.status == AgentRunStatus.BLOCKED:
                        self.task_manager.mark_result(tid, agent.serialize_result(result), TaskStatus.BLOCKED, error=";".join(result.errors))
                    elif result.status == AgentRunStatus.PARTIALLY_COMPLETED:
                        self.task_manager.mark_result(tid, agent.serialize_result(result), TaskStatus.PARTIALLY_COMPLETED)
                        completed_ids.add(tid)
                    else:
                        # retry once deterministically if allowed and idempotent/fail-safe
                        if self.task_manager.can_retry(tid):
                            self.task_manager.set_status(tid, TaskStatus.QUEUED, reason="retry_scheduled")
                            self.task_manager.set_status(tid, TaskStatus.VALIDATED, reason="retry_validated")
                            self.task_manager.set_status(tid, TaskStatus.RUNNING, reason="retry_running")
                            self.task_manager.increment_attempt(tid)
                            result2 = agent.execute(task, ctx)
                            results[-1] = result2
                            if result2.status in {AgentRunStatus.COMPLETED, AgentRunStatus.PENDING_APPROVAL, AgentRunStatus.PARTIALLY_COMPLETED}:
                                map_s = {AgentRunStatus.COMPLETED: TaskStatus.COMPLETED, AgentRunStatus.PENDING_APPROVAL: TaskStatus.PENDING_APPROVAL, AgentRunStatus.PARTIALLY_COMPLETED: TaskStatus.PARTIALLY_COMPLETED}
                                self.task_manager.mark_result(tid, agent.serialize_result(result2), map_s[result2.status])
                                completed_ids.add(tid)
                            else:
                                self.task_manager.mark_result(tid, agent.serialize_result(result2), TaskStatus.FAILED, error=";".join(result2.errors))
                        else:
                            self.task_manager.mark_result(tid, agent.serialize_result(result), TaskStatus.FAILED, error=";".join(result.errors))

            agg = self.aggregator.aggregate(results)
            all_statuses = [r.status for r in results]
            if results and all(s == AgentRunStatus.COMPLETED for s in all_statuses):
                status = "completed"
            elif results and any(s == AgentRunStatus.COMPLETED for s in all_statuses):
                status = "partially_completed"
            elif results and any(s == AgentRunStatus.PENDING_APPROVAL for s in all_statuses):
                status = "pending_approval"
            elif results and all(s == AgentRunStatus.BLOCKED for s in all_statuses):
                status = "blocked"
            elif results:
                status = "failed"
            else:
                status = "no_tasks"

            ev = self._audit(business_id, actor, "orchestration_complete", f"report:{report_id}", "ok", {"status": status, "task_count": len(results)})
            if ev:
                audit_ids.append(ev)
            brief = ExecutionBrief(
                brief_id=str(uuid.uuid4()),
                business_id=business_id,
                objective=objective,
                strategy=strategy,
                summary=agg.get("summary", ""),
                planned_tasks=[t.model_dump() for t in task_objs],
                completed_task_ids=[r.task_id for r in results if r.status == AgentRunStatus.COMPLETED],
                failed_task_ids=[r.task_id for r in results if r.status == AgentRunStatus.FAILED],
                blocked_task_ids=[r.task_id for r in results if r.status == AgentRunStatus.BLOCKED],
                pending_approval_task_ids=agg.get("pending_approval_task_ids", []),
                key_findings=agg.get("findings", [])[:25],
                recommendations=agg.get("recommendations", [])[:25],
                risks=agg.get("risks", []) + agg.get("conflicts", []),
                audit_event_ids=audit_ids,
            )
            return OrchestrationReport(
                report_id=report_id,
                business_id=business_id,
                objective=objective,
                status=status,
                strategy=strategy,
                task_count=len(task_objs),
                results=[r.model_dump() for r in results],
                brief=brief,
                errors=agg.get("errors", []),
                audit_event_ids=audit_ids,
                metadata={"preflight": pre, "schedule": schedule, "ranked_opportunities": ranked, "conflicts": agg.get("conflicts", [])},
            )
        except Exception as exc:  # noqa: BLE001
            ev = self._audit(business_id, actor, "orchestration_failed", f"report:{report_id}", "error", {"error": str(exc)})
            if ev:
                audit_ids.append(ev)
            return OrchestrationReport(
                report_id=report_id,
                business_id=business_id,
                objective=objective,
                status="failed",
                strategy=strategy,
                task_count=len(tasks),
                results=[],
                brief=None,
                errors=[str(exc)],
                audit_event_ids=audit_ids,
                metadata={},
            )
