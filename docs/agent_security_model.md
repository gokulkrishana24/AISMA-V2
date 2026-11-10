# Agent Security Model (Phase 3)

## Security boundaries
- **Code enforces security**; prompts/system messages are not a security boundary.
- **LLM outputs are untrusted data**: validated/parsed; never executed as code/shell; never grant permissions or trigger privileged actions directly.
- **Governance is outside the LLM**: permissions, policy, kill switch, budget, and approval decisions are deterministic/backend-controlled.

## Mandatory controls (reused Phase 1 / extended Phase 3)
| Control | Implementation |
|---|---|
| Default deny / least privilege | `governance.permissions.PermissionManager` + per-agent required actions (`Action` enum). Unknown actions denied. |
| Tenant/business isolation | Task/context business IDs must match; `PermissionContext.actor_business_id` isolation; `BrandContextService` rejects unauthorized business access. |
| Kill switch | Global/per-business kill switch checked by BaseAgent and Orchestrator (fail closed on corrupt state). |
| Budget enforcement | `BudgetEnforcer.check_and_reserve` before agent execution; strict config mode fails closed. |
| Hash-chained audit | `AuditLogger` records agent/orchestration events with PII redaction and chain verification. |
| Untrusted input scanning | `governance.injection.scan_untrusted_text` applied to external/user fields; injection patterns fail closed. Inputs isolated before LLM use. |
| Output validation | `governance.linters.lint_text` checks agent output; high/critical findings fail closed. |
| Policy / human approval | `PolicyEngine` default-denies publishing; sensitive actions require approval. Publishing agent cannot report real publication and requires approval/integration/credentials/state. Negative review/complaint responses require approval. |
| Idempotency | Task `idempotency_key` dedup in `TaskManager`; deterministic planning/execution. |
| No arbitrary execution | No shell/FS/network execution from LLM output. No hidden external API calls. |

## Sensitive action rules
- **Publishing:** prepare/validate/schedule only. Actual publish requires human approval, valid permissions, active kill-switch state clear, policy approval, valid publishing credentials, approved content state, and real integration confirmation. Missing integration returns `integration_not_configured`.
- **Reviews/complaints:** drafts only; no auto-publish. Negative/complaint/sensitive cases escalate to human approval.
- **Leads:** no invented pricing/availability/delivery/contract commitments; deterministic escalation for high intent/complaints.
- **ROI:** calculations in Python only; missing data explicit.

## Prompt-injection handling
External text (reviews, comments, messages, web/imported content, competitor descriptions, etc.) is scanned and isolated. System/brand instructions remain controlled by backend. Model responses are treated as untrusted and schema/validation checked.

## Limitations
Phase 3 is not a production FastAPI service, has no live social/search/competitor platform integrations, and real LLM inference is constrained on 4GB VRAM (mocked tests for full suite; controlled real tests only).
