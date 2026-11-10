# AISMA v2 — External Integrations & Official API Verification Matrix

**Integration Architect:** External Platform Integration & OAuth Specialist  
**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Platform Adapter Verification Classification

Every external platform integration was audited according to five distinct operational levels:
- **Level 1 (Unit Tested):** Adapter classes and payload models tested in isolation.
- **Level 2 (Sandbox Tested):** Simulated API responses verifying status handling, latency reporting, and fail-closed errors.
- **Level 3 (OAuth Framework Ready):** Token encryption at rest via Fernet and header construction ready.
- **Level 4 (Official API Compatible):** Built against official API specifications (REST / Graph API).
- **Level 5 (Live Production Authorized):** Active production client credentials provisioned and live tokens exchanged.

---

## 2. Platform Adapter Matrix

| Channel / Adapter | Current Status | Implemented Adapter | Encryption & Security | Production Prerequisites Needed |
| :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | Level 1–4 Verified | `LinkedInAdapter` (`src/integrations/linkedin.py`) | Fernet-encrypted access tokens; author URN scoping. | Developer App approval for `w_member_social` or Community Management API. |
| **Meta (Instagram / FB)** | Level 1–4 Verified | `MetaAdapter` (`src/integrations/meta.py`) | Fernet encryption; Page ID & IG User ID parameters. | Meta for Developers App review for `pages_manage_posts`, `instagram_content_publish`. |
| **X (Twitter v2)** | Level 1–4 Verified | `XTwitterAdapter` (`src/integrations/x_twitter.py`) | Bearer token authorization; username routing. | X Developer Portal Project with Basic or Pro tier for `tweet.write`. |
| **Google Search Console** | Level 1–4 Verified | `GSCAdapter` (`src/integrations/google_search_console.py`) | Domain inspection; read-only search queries. | Google Cloud Service Account with Search Console Viewer role. |
| **Google Analytics 4** | Level 1–4 Verified | `GA4Adapter` (`src/integrations/google_analytics.py`) | GA4 Data API stream reporting; session metrics. | Google Cloud Service Account with GA4 Viewer permission on Property. |
| **Customer Reviews** | Level 1–4 Verified | `ReviewsAdapter` (`src/integrations/reviews.py`) | Multi-channel review aggregation (GBP / G2 / Trustpilot). | Google Business Profile API or review aggregation webhook keys. |

---

## 3. Fail-Closed Publishing Guarantee

Under no circumstances will AISMA v2 attempt unauthorized live publishing. If `is_sandbox=False` and credentials are missing or expired, the adapter fails closed immediately with an explicit error response (`"Fail-closed: Missing access token"`), never masquerading failure as success.
