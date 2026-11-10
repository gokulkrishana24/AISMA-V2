# AISMA v2 — Subscription, Billing & Usage Metering Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Subscription Tier Architecture (`src/db/models.py`, `src/services/billing.py`)

Four configurable tiers are seeded idempotently via `init_db()`:

| Plan Slug | Monthly Reference Price | Monthly Agent Executions | Max Social Accounts | Target Segment |
| :--- | :--- | :--- | :--- | :--- |
| `starter` | $49.00 | 500 | 3 | Solo operators & early startups |
| `professional` | $149.00 | 2,500 | 10 | Growing B2B/B2C marketing teams |
| `agency` | $399.00 | 10,000 | 25 | Multi-client agencies |
| `enterprise` | $999.00 | 50,000 | 100 | Enterprise governance deployments |

*(Prices and quotas are configurable seed values, not commercial legal commitments.)*

---

## 2. Usage Metering & Governance Separation
- **Monthly Tracking (`UsageMeter`):** Tracks `agent_executions_count`, `tokens_consumed`, and `published_posts_count` keyed by `(business_id, period_month)`.
- **Quota Enforcement (`BillingService.check_quota`):** Emits soft warnings at `>= 80%` consumption and denies execution at `100%` without modifying or weakening `KillSwitch` or `PermissionManager`.
- **Plan Lifecycle Endpoints (`src/api/routers/billing.py`):** `/plans`, `/subscription`, `/quota`, `/upgrade`, `/cancel`.
- **Payment Processing Status:** **Requires owner approval** — zero raw card storage and no live Stripe/merchant API keys wired.

