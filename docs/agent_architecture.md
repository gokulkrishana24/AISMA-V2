# Agent Architecture (Phase 3)

## Overview
Phase 3 adds a modular, governed multi-agent marketing system on top of the existing Phase 1 governance foundation and Phase 2 local AI infrastructure.

- **8 specialized agents** + **1 central Orchestrator**
- **Shared runtime**: one `LLMProvider` interface, one shared `ModelManager` / Ollama inference service (no 8 separate model processes)
- **Shared governance**: kill switch, permissions, policy, budget, audit, injection scanning, linting, deterministic scoring/triggers
- **Typed contracts**: Pydantic schemas for tasks, agent results, briefs, and orchestration reports

## Module layout
```text
src/
  agents/           BaseAgent, registry, 8 specialized agents
  orchestrator/     Orchestrator, planner, scheduler, task manager, ranker, aggregator
  schemas/          task.py, agent.py, brief.py, results.py
  services/         brand_context.py, agent_execution.py
  ai/               (Phase 2, unchanged) provider/model manager/Ollama
  governance/       (Phase 1, unchanged) policy/permissions/audit/etc.
tests/
  agents/           Base/registry/governance/specialized mocked tests
  orchestrator/     Planner/task/orchestrator mocked tests
  integration/      Optional real Ollama test (disabled by default)
```

## BaseAgent contract
Every agent exposes: `agent_id`, `agent_name`, `description`, `capabilities`, `supported_task_types`, `required_permissions`, `health_check()`, `validate_task()`, `execute(task, context)`, `serialize_result()`.

`execute()` enforces, in order: task validation, tenant context validation, kill switch, permissions (default-deny), budget, policy, untrusted-input scanning/isolation, agent logic (restricted prompt + shared LLM), output validation, audit events, structured `AgentResult`. Governance/security failures fail closed.

## AgentResult
`task_id, agent_id, status, summary, findings, recommendations, evidence, confidence, risks, requires_human_approval, created_at, execution_duration, model_used, errors, output`.

## Shared inference
Agents receive a shared `LLMProvider` (and may use `ExecutionContext.model_manager` for concurrency/selection). Orchestrator uses the shared `ModelManager` and default strategy respects Phase 2 concurrency (default 1). **Do not run 8 LLM requests simultaneously.**

## Hardware constraints
Designed for constrained local hardware (observed: RTX 3050 4GB VRAM, ~16GB RAM with pressure). Real inference is slow; mocked tests cover the full suite. Real inference should be limited to controlled, single-request integration checks (phi3.5 verified in Phase 2 recovery).
