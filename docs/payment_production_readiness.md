# AISMA v2 — Payment & Subscription Production Readiness

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Billing Capabilities Verified Locally (No Live Charges)

| Capability | Endpoint / Module | Verification Evidence |
| :--- | :--- | :--- |
| **Plan Catalog & Limits** | `GET /api/v1/billing/plans` | Starter, Professional, Agency, Enterprise tiers verified. |
| **Subscription & Quota Enforcement** | `GET /api/v1/billing/subscription`, `/quota` | Monthly `UsageMeter` tracking + 80% warning / 100% hard stop verified. |
| **Upgrade / Cancel Lifecycle** | `POST /api/v1/billing/upgrade`, `/cancel` | Plan switching and `cancel_at_period_end=True` flag verified. |
| **Webhook Signature Verification** | `POST /api/v1/billing/webhook` | Missing/invalid `X-Billing-Signature` rejected with `401 Unauthorized`. |
| **Duplicate Webhook Idempotency** | `POST /api/v1/billing/webhook` | Repeated `event_id` returns `duplicate_ignored: True` without mutating subscription twice (`test_billing_webhook_hmac_and_idempotency`). |
| **Payment Failure / Recovery** | `invoice.payment_failed` -> `past_due`, `invoice.paid` -> `active` | Verified state transitions in automated tests without card storage. |

---

## 2. Commercial Activation Prerequisite (Owner Approval Required)
- Live payment processing (Stripe/Paddle merchant keys) remains disabled. Zero raw card data is stored in any database table or log.

