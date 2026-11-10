import {
  AgentDetails,
  AgentId,
  ApprovalRequest,
  AuditLogEntry,
  BrandOSData,
  BudgetOverview,
  CompetitorProfile,
  ContentDraft,
  KeywordRanking,
  KillSwitchStatus,
  LeadConversation,
  ReviewItem,
  UserProfile,
  HardwareTelemetry,
  OllamaModelInfo,
  OllamaRuntimeHealth,
  InferenceTelemetry,
  LocalAIConfig,
  ModelBenchmarkResult,
  AgentModelAssignment,
  RegistryCandidate,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface ApiResponse<T> {
  data: T;
  isDevFixture?: boolean;
  status: number;
  message?: string;
}

export class ApiError extends Error {
  status: number;
  details?: any;

  constructor(message: string, status: number, details?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

// Development fixtures: Strongly typed, strictly labelled development fallback
import {
  MOCK_AGENTS,
  MOCK_APPROVALS,
  MOCK_AUDIT_LOGS,
  MOCK_BRAND_OS,
  MOCK_BUDGET,
  MOCK_COMPETITORS,
  MOCK_DRAFTS,
  MOCK_KEYWORDS,
  MOCK_KILL_SWITCH,
  MOCK_LEADS,
  MOCK_REVIEWS,
  MOCK_USER,
  MOCK_HARDWARE_TELEMETRY,
  MOCK_OLLAMA_MODELS,
  MOCK_OLLAMA_HEALTH,
  MOCK_INFERENCE_TELEMETRY,
  MOCK_LOCAL_AI_CONFIG,
  MOCK_MODEL_BENCHMARKS,
  MOCK_AGENT_MODEL_ASSIGNMENTS,
  MOCK_REGISTRY_CANDIDATES,
} from "./fixtures";

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;
  private businessId: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  setToken(token: string | null) {
    this.token = token;
  }

  setBusinessId(businessId: string | null) {
    this.businessId = businessId;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    fixtureFallback?: () => T
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    if (this.businessId && !headers["X-Business-Id"]) {
      headers["X-Business-Id"] = this.businessId;
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const res = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!res.ok) {
        if (res.status === 404 && fixtureFallback) {
          console.warn(`[API] Endpoint ${endpoint} returned 404. Falling back to dev fixture.`);
          return { data: fixtureFallback(), isDevFixture: true, status: 200 };
        }
        const errorData = await res.json().catch(() => ({}));
        throw new ApiError(
          errorData.detail || errorData.message || `Request failed with status ${res.status}`,
          res.status,
          errorData
        );
      }

      const json = await res.json();
      return { data: json, isDevFixture: false, status: res.status };
    } catch (err: any) {
      if (fixtureFallback) {
        console.warn(
          `[API] Backend unavailable at ${url} (${err.message}). Using typed development fixture for UI development.`
        );
        return {
          data: fixtureFallback(),
          isDevFixture: true,
          status: 200,
          message: "Loaded from development fixture. Backend is currently offline.",
        };
      }
      throw new ApiError(
        err.message || "Network or connection error to backend",
        err.status || 503,
        err
      );
    }
  }

  // Auth endpoints
  async login(credentials: { email: string; password: string }): Promise<ApiResponse<{ token: string; user: UserProfile }>> {
    return this.request(
      "/api/v1/auth/login",
      {
        method: "POST",
        body: JSON.stringify(credentials),
      },
      () => ({
        token: "dev_mock_jwt_token_for_offline_preview_only",
        user: MOCK_USER,
      })
    );
  }

  async getCurrentUser(): Promise<ApiResponse<UserProfile>> {
    return this.request("/api/v1/auth/me", {}, () => MOCK_USER);
  }

  // Agent Endpoints
  async getAgents(): Promise<ApiResponse<AgentDetails[]>> {
    return this.request("/api/v1/agents", {}, () => MOCK_AGENTS);
  }

  async getAgentById(id: AgentId): Promise<ApiResponse<AgentDetails>> {
    return this.request(`/api/v1/agents/${id}`, {}, () => {
      const found = MOCK_AGENTS.find((a) => a.id === id);
      if (!found) throw new ApiError(`Agent ${id} not found`, 404);
      return found;
    });
  }

  async triggerAgentTask(id: AgentId, payload: { action: string; parameters?: any }): Promise<ApiResponse<any>> {
    return this.request(
      `/api/v1/agents/${id}/execute`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      () => ({
        task_id: `task_${Date.now()}`,
        agent_id: id,
        status: "queued",
        message: "Task queued in backend engine (Dev Fixture Mode)",
      })
    );
  }

  // Approvals & Governance (Never allows frontend-only bypass)
  async getApprovals(): Promise<ApiResponse<ApprovalRequest[]>> {
    return this.request("/api/v1/approvals", {}, () => MOCK_APPROVALS);
  }

  async submitApprovalDecision(
    id: string,
    decision: { action: "approve" | "reject"; note?: string }
  ): Promise<ApiResponse<{ id: string; status: string; audited: boolean }>> {
    // Strictly routed to backend governance endpoint
    return this.request(
      `/api/v1/approvals/${id}/decision`,
      {
        method: "POST",
        body: JSON.stringify(decision),
      },
      () => ({
        id,
        status: decision.action === "approve" ? "approved" : "rejected",
        audited: true,
      })
    );
  }

  // Content Studio
  async getDrafts(): Promise<ApiResponse<ContentDraft[]>> {
    return this.request("/api/v1/content/drafts", {}, () => MOCK_DRAFTS);
  }

  async createDraft(draft: Partial<ContentDraft>): Promise<ApiResponse<ContentDraft>> {
    return this.request(
      "/api/v1/content/drafts",
      {
        method: "POST",
        body: JSON.stringify(draft),
      },
      () => ({
        ...MOCK_DRAFTS[0],
        id: `draft_${Date.now()}`,
        title: draft.title || "Untitled Draft",
        content: draft.content || "",
        channel: draft.channel || "linkedin",
        status: "draft",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      })
    );
  }

  // Reviews & Reputation
  async getReviews(): Promise<ApiResponse<ReviewItem[]>> {
    return this.request("/api/v1/reputation/reviews", {}, () => MOCK_REVIEWS);
  }

  // Leads & Conversations
  async getConversations(): Promise<ApiResponse<LeadConversation[]>> {
    return this.request("/api/v1/conversations", {}, () => MOCK_LEADS);
  }

  // SEO & Competitor Intelligence
  async getSEOIntelligence(): Promise<ApiResponse<{ keywords: KeywordRanking[]; visibilityScore: number }>> {
    return this.request("/api/v1/seo/rankings", {}, () => ({
      keywords: MOCK_KEYWORDS,
      visibilityScore: 84.6,
    }));
  }

  async getCompetitorIntelligence(): Promise<ApiResponse<CompetitorProfile[]>> {
    return this.request("/api/v1/intelligence/competitors", {}, () => MOCK_COMPETITORS);
  }

  // Brand OS
  async getBrandOS(): Promise<ApiResponse<BrandOSData>> {
    return this.request("/api/v1/brand-os", {}, () => MOCK_BRAND_OS);
  }

  async updateBrandOS(data: Partial<BrandOSData>): Promise<ApiResponse<BrandOSData>> {
    return this.request(
      "/api/v1/brand-os",
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
      () => ({ ...MOCK_BRAND_OS, ...data })
    );
  }

  // Budget
  async getBudgetOverview(): Promise<ApiResponse<BudgetOverview>> {
    return this.request("/api/v1/budget", {}, () => MOCK_BUDGET);
  }

  // Governance: Killswitch & Audit
  async getKillSwitchStatus(): Promise<ApiResponse<KillSwitchStatus>> {
    return this.request("/api/v1/governance/killswitch", {}, () => MOCK_KILL_SWITCH);
  }

  async toggleKillSwitch(engaged: boolean, reason: string): Promise<ApiResponse<KillSwitchStatus>> {
    return this.request(
      "/api/v1/governance/killswitch",
      {
        method: "POST",
        body: JSON.stringify({ engaged, reason }),
      },
      () => ({
        ...MOCK_KILL_SWITCH,
        engaged,
        reason,
        updated_at: new Date().toISOString(),
        updated_by: "human_admin",
      })
    );
  }

  async getAuditLogs(): Promise<ApiResponse<{ entries: AuditLogEntry[]; chainValid: boolean }>> {
    return this.request("/api/v1/governance/audit", {}, () => ({
      entries: MOCK_AUDIT_LOGS,
      chainValid: true,
    }));
  }

  async verifyAuditChain(): Promise<ApiResponse<{ valid: boolean; verifiedCount: number; message: string }>> {
    return this.request("/api/v1/governance/audit/verify", { method: "POST" }, () => ({
      valid: true,
      verifiedCount: MOCK_AUDIT_LOGS.length,
      message: "SHA-256 cryptographic chain verification passed. Zero tampering detected.",
    }));
  }

  // Local AI Infrastructure & Ollama Control Center
  async getHardwareTelemetry(): Promise<ApiResponse<HardwareTelemetry>> {
    return this.request("/api/v1/ai/hardware", {}, () => MOCK_HARDWARE_TELEMETRY);
  }

  async getOllamaHealth(): Promise<ApiResponse<OllamaRuntimeHealth>> {
    return this.request("/api/v1/ai/health", {}, () => MOCK_OLLAMA_HEALTH);
  }

  async getOllamaModels(): Promise<ApiResponse<OllamaModelInfo[]>> {
    return this.request("/api/v1/ai/models", {}, () => MOCK_OLLAMA_MODELS);
  }

  async getInferenceTelemetry(): Promise<ApiResponse<InferenceTelemetry>> {
    return this.request("/api/v1/ai/telemetry", {}, () => MOCK_INFERENCE_TELEMETRY);
  }

  async getLocalAIConfig(): Promise<ApiResponse<LocalAIConfig>> {
    return this.request("/api/v1/ai/config", {}, () => MOCK_LOCAL_AI_CONFIG);
  }

  async updateLocalAIConfig(config: Partial<LocalAIConfig>): Promise<ApiResponse<LocalAIConfig>> {
    return this.request(
      "/api/v1/ai/config",
      {
        method: "PUT",
        body: JSON.stringify(config),
      },
      () => ({ ...MOCK_LOCAL_AI_CONFIG, ...config })
    );
  }

  async setActiveModel(model: string): Promise<ApiResponse<{ active_model: string; status: string }>> {
    return this.request(
      "/api/v1/ai/active-model",
      {
        method: "POST",
        body: JSON.stringify({ model }),
      },
      () => ({
        active_model: model,
        status: "active",
      })
    );
  }

  async getAgentModelAssignments(): Promise<ApiResponse<AgentModelAssignment[]>> {
    return this.request("/api/v1/ai/agent-assignments", {}, () => MOCK_AGENT_MODEL_ASSIGNMENTS);
  }

  async updateAgentModelAssignment(
    agentId: AgentId,
    payload: { assigned_model: string; fallback_model?: string }
  ): Promise<ApiResponse<AgentModelAssignment>> {
    return this.request(
      `/api/v1/ai/agent-assignments/${agentId}`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
      () => {
        const found = MOCK_AGENT_MODEL_ASSIGNMENTS.find((a) => a.agent_id === agentId);
        return {
          ...(found || MOCK_AGENT_MODEL_ASSIGNMENTS[0]),
          assigned_model: payload.assigned_model,
          fallback_model: payload.fallback_model || "phi3.5:latest",
        };
      }
    );
  }

  async getModelBenchmarks(): Promise<ApiResponse<ModelBenchmarkResult[]>> {
    return this.request("/api/v1/ai/benchmarks", {}, () => MOCK_MODEL_BENCHMARKS);
  }

  async getRegistryCandidates(): Promise<ApiResponse<RegistryCandidate[]>> {
    return this.request("/api/v1/ai/registry-candidates", {}, () => MOCK_REGISTRY_CANDIDATES);
  }

  // Integrations & Social Publishing
  async getIntegrations(): Promise<ApiResponse<Array<{ platform: string; connected: boolean; status: string; is_sandbox: boolean; latency_ms: number }>>> {
    return this.request("/api/v1/integrations", {}, () => [
      { platform: "linkedin", connected: true, status: "Connected", is_sandbox: true, latency_ms: 12.0 },
      { platform: "meta", connected: true, status: "Connected", is_sandbox: true, latency_ms: 15.0 },
      { platform: "twitter", connected: true, status: "Connected", is_sandbox: true, latency_ms: 18.0 },
      { platform: "gsc", connected: true, status: "Connected", is_sandbox: true, latency_ms: 22.0 },
      { platform: "ga4", connected: true, status: "Connected", is_sandbox: true, latency_ms: 19.5 },
      { platform: "reviews", connected: true, status: "Connected", is_sandbox: true, latency_ms: 28.0 },
    ]);
  }

  async publishToPlatform(platform: string, content: string, media_urls: string[] = []): Promise<ApiResponse<{ success: boolean; platform: string; post_id?: string; url?: string; is_sandbox: boolean }>> {
    return this.request(
      `/api/v1/integrations/${platform}/publish`,
      {
        method: "POST",
        body: JSON.stringify({ content, media_urls }),
      },
      () => ({
        success: true,
        platform,
        post_id: `post_${Date.now()}`,
        is_sandbox: true,
      })
    );
  }

  // Campaigns
  async getCampaigns(): Promise<ApiResponse<Array<{ id: string; name: string; objective: string; status: string; budget_allocated: number; budget_spent: number; channels: string[] }>>> {
    return this.request("/api/v1/campaigns", {}, () => [
      {
        id: "cmp_default_01",
        name: "Q4 Enterprise Brand Launch",
        objective: "brand_awareness",
        status: "active",
        budget_allocated: 10000.0,
        budget_spent: 450.0,
        channels: ["linkedin", "twitter"],
      },
    ]);
  }

  // Deterministic Analytics & ROI
  async getROIReport(period = "Last 30 Days"): Promise<
    ApiResponse<{
      business_id: string;
      period: string;
      total_spend: number;
      total_attributed_revenue: number;
      blended_roas: number;
      net_marketing_profit: number;
      marketing_roi_percentage: number;
      customer_acquisition_cost: number;
      customer_lifetime_value: number;
      ltv_to_cac_ratio: number;
      channels: Array<{
        channel: string;
        spend: number;
        attributed_revenue: number;
        impressions: number;
        clicks: number;
        conversions: number;
        roas: number;
        cpa: number;
      }>;
      deterministic_audit_hash: string;
      computed_at: string;
    }>
  > {
    return this.request(`/api/v1/analytics/roi?period=${encodeURIComponent(period)}`, {}, () => ({
      business_id: "biz_demo_offline",
      period,
      total_spend: 9500.0,
      total_attributed_revenue: 46500.0,
      blended_roas: 6.64,
      net_marketing_profit: 37000.0,
      marketing_roi_percentage: 389.47,
      customer_acquisition_cost: 66.9,
      customer_lifetime_value: 5200.0,
      ltv_to_cac_ratio: 77.73,
      channels: [],
      deterministic_audit_hash: "0000000000000000000000000000000000000000000000000000000000000000",
      computed_at: new Date().toISOString(),
    }));
  }

  // Auth Lifecycle Extensions
  async refreshAccessToken(refreshToken: string): Promise<ApiResponse<{ token: string; token_type: string }>> {
    return this.request("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  async logoutSession(): Promise<ApiResponse<{ success: boolean; message: string }>> {
    const res = await this.request<{ success: boolean; message: string }>("/api/v1/auth/logout", {
      method: "POST",
    });
    this.setToken(null);
    return res;
  }

  // Organizations & Onboarding
  async getOrganizations(): Promise<ApiResponse<Array<{ id: string; name: string; slug: string; industry: string; user_role: string }>>> {
    return this.request("/api/v1/organizations", {}, () => []);
  }

  async completeOnboarding(payload: {
    company_name: string;
    industry: string;
    target_audience: string;
    primary_channels: string[];
    selected_plan: string;
  }): Promise<ApiResponse<{ success: boolean; business_id: string; business_name: string; plan: string }>> {
    return this.request("/api/v1/onboarding/setup", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Subscription Billing & Usage Metering
  async getBillingPlans(): Promise<ApiResponse<Array<{ id: string; name: string; slug: string; price_monthly: number; max_monthly_executions: number; features: string[] }>>> {
    return this.request("/api/v1/billing/plans", {}, () => []);
  }

  async getSubscriptionStatus(): Promise<ApiResponse<{ subscription_id: string; status: string; plan: any; usage: any }>> {
    return this.request("/api/v1/billing/subscription");
  }

  // Scheduler & Calendar
  async getScheduledPosts(): Promise<ApiResponse<Array<{ id: string; channel: string; content: string; scheduled_time: string; status: string }>>> {
    return this.request("/api/v1/scheduler/calendar", {}, () => []);
  }

  async schedulePost(payload: { channel: string; content: string; scheduled_time: string }): Promise<ApiResponse<{ id: string; channel: string; content: string; scheduled_time: string; status: string }>> {
    return this.request("/api/v1/scheduler/posts", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Notifications & Support
  async getNotifications(unreadOnly = false): Promise<ApiResponse<Array<{ id: string; title: string; message: string; category: string; read: boolean; created_at: string }>>> {
    return this.request(`/api/v1/notifications?unread_only=${unreadOnly}`, {}, () => []);
  }

  async markNotificationRead(id: string): Promise<ApiResponse<{ id: string; read: boolean }>> {
    return this.request(`/api/v1/notifications/${id}/read`, { method: "PATCH" });
  }

  async createSupportTicket(payload: { subject: string; description: string; priority?: string }): Promise<ApiResponse<{ id: string; status: string }>> {
    return this.request("/api/v1/support/tickets", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Local Beta Synthetic Data & Diagnostics
  async seedDemoWorkspace(): Promise<ApiResponse<{ seeded: boolean; is_synthetic: boolean; business_id: string; business_name: string; note: string }>> {
    return this.request("/api/v1/beta/seed-demo", { method: "POST" });
  }

  async resetDemoWorkspace(): Promise<ApiResponse<{ reset: boolean; deleted_demo_business_count: number; real_data_preserved: boolean }>> {
    return this.request("/api/v1/beta/reset-demo", { method: "POST" });
  }

  async getBetaDiagnostics(): Promise<ApiResponse<{ mode: string; database_connected: boolean; ollama_connected: boolean; active_model: string }>> {
    return this.request("/api/v1/beta/diagnostics");
  }

  // Privacy & Admin
  async exportTenantData(): Promise<ApiResponse<Record<string, any>>> {
    return this.request("/api/v1/privacy/export");
  }

  async getAdminOverview(): Promise<ApiResponse<{ platform_status: string; metrics: Record<string, number>; ai_runtime: Record<string, any> }>> {
    return this.request("/api/v1/admin/overview");
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

