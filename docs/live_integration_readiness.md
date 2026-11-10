# AISMA v2 — Official Social & Analytics Live-Integration Readiness

**Date:** November 10, 2026  
**System:** AI-Native Social Media Agent Team v2 (AISMA v2)  

---

## 1. Platform Configuration & Approval Checklist

All adapters operate strictly in **Sandbox Mode** (`is_sandbox=True`) locally; zero real social content was published.

| Platform | Portal / API | Required Env Variables | Required Scopes / Permissions | Approval / Restriction Notes |
| :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | LinkedIn Developer Portal (`/v2/ugcPosts`) | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` | `w_member_social`, `w_organization_social`, `r_organization_social` | Organization posting requires LinkedIn Community Management API app review. |
| **Meta (FB / IG)** | Meta for Developers (`graph.facebook.com/v19.0`) | `META_APP_ID`, `META_APP_SECRET` | `pages_manage_posts`, `pages_read_engagement`, `instagram_content_publish` | Meta App Review required for live business publishing; Instagram requires linked FB Page + Business IG account. |
| **X (Twitter v2)** | X Developer Portal (`/2/tweets`) | `X_API_BEARER_TOKEN` | `tweet.read`, `tweet.write`, `users.read` | Basic or Pro tier required for sustained tweet writes and rate limits. |
| **Google Search Console** | Google Cloud Console | `GOOGLE_APPLICATION_CREDENTIALS` | `https://www.googleapis.com/auth/webmasters.readonly` | Service account email must be added as Verified User in GSC property. |
| **Google Analytics 4** | Google Cloud Console (Data API v1) | `GOOGLE_APPLICATION_CREDENTIALS` | `https://www.googleapis.com/auth/analytics.readonly` | Service account requires Viewer access on GA4 Property ID. |
| **Reviews (GBP)** | Google Business Profile API | `GOOGLE_APPLICATION_CREDENTIALS` | `https://www.googleapis.com/auth/business.manage` | Google Business Profile API requires explicit Google access request approval. |

---

## 2. Verified Sandbox Security Controls
- OAuth CSRF `state` token issuance & validation (`GET /oauth/start`, `POST /oauth/callback`) verified.
- Access tokens encrypted at rest via `CredentialVault` (Fernet) in `SocialAccount`.
- Webhook signature check (`POST /webhook` + `X-AISMA-Signature` HMAC-SHA256) verified.

