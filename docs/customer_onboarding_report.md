# AISMA v2 — Customer Onboarding Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. End-to-End Onboarding Workflow

1. **Account Registration (`POST /api/v1/auth/register`):** Validates unique email, hashes password with `bcrypt` (12 rounds), assigns default business or creates a new workspace slug safely, issues HS256 access & refresh JWTs.
2. **Workspace Setup Wizard (`POST /api/v1/onboarding/setup`):** Creates `Business` entity, links `Membership` (`role="admin"`), attaches chosen `SubscriptionPlan` (`starter`, `professional`, `agency`, `enterprise`).
3. **Team Invitations (`POST /api/v1/organizations/current/invites`):** Issues expiring 7-day `OrganizationInvite` records scoped by `business_id` and assigned role (`admin`, `operator`, `viewer`).
4. **Channel OAuth Connection (`GET /api/v1/integrations/{platform}/oauth/start`):** Generates CSRF `state` token and stores Fernet-encrypted credentials in `SocialAccount` upon callback.
5. **Frontend Onboarding Experience:** Route `/onboarding` compiled cleanly in Next.js App Router and wired to `apiClient.completeOnboarding()`.

---

## 2. Verification Evidence
Verified by automated execution in `tests/integration/test_saas_productization.py::test_customer_onboarding_and_org_provisioning` (PASSED).

