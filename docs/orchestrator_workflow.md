# Orchestrator Workflow (Phase 3)

## Responsibilities
The Orchestrator is the single coordination layer. It does **not** override governance and does **not** let the LLM decide permissions/actions.

## Execution flow
1. Accept business goal/objective, tasks, optional signals/opportunities, execution context.
2. Validate `business_id` and tenant context (fail closed).
3. Run preflight (reported in metadata; fail-closed behavior can be enforced by callers/config).
4. Check global/business kill switch.
5. Verify orchestrator permissions (default-deny model).
6. Normalize/validate tasks (Pydantic `Task` schema; business isolation per task).
7. Register tasks in `TaskManager` with idempotency-key deduplication.
8. Generate deterministic execution plan (`dependency_based` default, also `sequential`, `priority_based`).
9. Rank opportunities deterministically using existing `governance.scoring.score_opportunity`.
10. Execute eligible tasks in plan order; dependency batches are handled sequentially to respect shared inference concurrency (default 1). No 8 simultaneous LLM requests.
11. For each task: validate status transitions, select agent, run agent through governed `BaseAgent.execute` (agent enforces kill switch/permissions/budget/policy/injection/output checks/audit).
12. On failure, capture errors, do not lose completed results, apply bounded deterministic retry when allowed; avoid repeated execution via idempotency/task state.
13. Aggregate results, detect simple conflicts, collect pending approvals.
14. Create `ExecutionBrief` and `OrchestrationReport` with structured results, errors, and audit references.
15. Record orchestration audit events.

## Task statuses
`queued → validated → running → completed|partially_completed|failed|blocked|pending_approval|cancelled` (validated transitions in `schemas.task`).

## Strategies
- **dependency_based** (default): topological batches from dependencies, priority-ordered.
- **sequential**: priority-ordered single chain.
- **priority_based**: priority-ordered tasks, executed one by one.

## Shared model/concurrency
Uses shared `ModelManager`/provider. `ExecutionContext.model_manager` allows BaseAgent to route structured calls through `ModelManager.run_with_fallback` (concurrency slot + fallback). Hardware-constrained default: concurrency 1.

## Partial failure
Report is factual (`completed|partially_completed|pending_approval|blocked|failed|no_tasks`). Completed results are preserved; failed/blocked tasks include errors.

## API readiness
Phase 3 provides Python domain contracts (`schemas/*`, orchestrator/agents/services). FastAPI/database multi-tenant API layer is Phase 5; frontend integration should use backend-confirmed contracts only.
