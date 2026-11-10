# AISMA v2 — External Integration Verification Report

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Platform Adapter Verification Status

We strictly separate **sandbox-verified adapter logic** from **live production platform authorization**:

| Platform | Adapter Module | Verified Level | OAuth / Webhook Controls | Remaining External Owner Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | `src/integrations/linkedin.py` | **Sandbox & Contract Tested** | OAuth CSRF `state`, Fernet storage, HMAC webhook verified | Requires LinkedIn Developer App review (`w_member_social` / Community Management API). |
| **Meta (FB / IG)** | `src/integrations/meta.py` | **Sandbox & Contract Tested** | OAuth CSRF `state`, Fernet storage, HMAC webhook verified | Requires Meta App Review (`pages_manage_posts`, `instagram_content_publish`). |
| **X (Twitter v2)** | `src/integrations/x_twitter.py` | **Sandbox & Contract Tested** | Bearer token fail-closed guard | Requires X Developer Portal Basic/Pro tier credentials. |
| **Google Search Console** | `src/integrations/google_search_console.py` | **Sandbox & Contract Tested** | Site URL scoping | Requires Google Cloud Service Account JSON (`GOOGLE_APPLICATION_CREDENTIALS`). |
| **Google Analytics 4** | `src/integrations/google_analytics.py` | **Sandbox & Contract Tested** | Property ID scoping | Requires GA4 Property Viewer Service Account. |
| **Reviews (GBP / G2)** | `src/integrations/reviews.py` | **Sandbox & Contract Tested** | Public response & sentiment framing | Requires Google Business Profile API access. |

---

## 2. Fail-Closed Guarantees Verified
- Calling live publish (`is_sandbox=False`) without valid OAuth tokens returns explicit `success=False` fail-closed rejection (`Fail-closed: Missing access token`).
- Tampered OAuth `state` parameters reject with `400 Bad Request`.
- Missing or invalid `X-AISMA-Signature` HMAC-SHA256 webhook headers reject with `401 Unauthorized`.

