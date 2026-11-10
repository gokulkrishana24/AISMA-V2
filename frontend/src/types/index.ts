export type AgentId =
  | "search_visibility"
  | "market_radar"
  | "content_engine"
  | "creative_studio"
  | "publishing_social"
  | "reviews_reputation"
  | "leads_conversations"
  | "results_roi";

export type AgentStatus = "active" | "running" | "idle" | "paused" | "error" | "blocked";

export interface AgentMetric {
  label: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down" | "neutral";
}

export interface AgentTask {
  id: string;
  agentId: AgentId;
  title: string;
  status: "queued" | "running" | "completed" | "failed" | "awaiting_approval";
  startedAt: string;
  completedAt?: string;
  inputData: Record<string, any>;
  outputData?: Record<string, any>;
  tokensUsed?: number;
  latencyMs?: number;
  error?: string;
}

export interface AgentDetails {
  id: AgentId;
  name: string;
  codename: string;
  description: string;
  category: string;
  status: AgentStatus;
  currentTask?: string;
  lastExecution: string;
  lastOutputSummary?: string;
  successRate: number;
  totalExecutions: number;
  errorCount: number;
  avgLatencyMs: number;
  permissions: string[];
  config: {
    model: string;
    temperature: number;
    maxTokens: number;
    autonomousMode: boolean;
    frequency: string;
  };
  metrics: AgentMetric[];
  recentTasks: AgentTask[];
}

export type SocialChannel =
  | "linkedin"
  | "twitter"
  | "instagram"
  | "facebook"
  | "tiktok"
  | "youtube";

export type ContentStatus =
  | "draft"
  | "in_review"
  | "pending_approval"
  | "approved"
  | "scheduled"
  | "published"
  | "rejected";

export interface ContentHookOption {
  id: string;
  text: string;
  angle: "curiosity" | "data_driven" | "contrarian" | "storytelling";
  score: number;
}

export interface ContentDraft {
  id: string;
  title: string;
  channel: SocialChannel;
  content: string;
  characterCount: number;
  maxCharacterCount: number;
  hookOptions: ContentHookOption[];
  selectedHookId?: string;
  brandVoiceValidation: {
    score: number;
    isCompliant: boolean;
    toneMatch: string[];
    feedback: string;
  };
  seoSuggestions: {
    keywords: string[];
    hashtags: string[];
    estimatedReachScore: number;
  };
  status: ContentStatus;
  scheduledFor?: string;
  authorAgent?: AgentId;
  approverId?: string;
  createdAt: string;
  updatedAt: string;
  imagePrompt?: string;
  imageUrl?: string;
}

export interface ApprovalRequest {
  id: string;
  title: string;
  type: "content_publish" | "ad_spend" | "reply_escalation" | "schedule_change";
  status: "pending" | "approved" | "rejected";
  urgency: "low" | "medium" | "high" | "critical";
  channel?: SocialChannel;
  agentId: AgentId;
  contentPreview: string;
  submittedAt: string;
  policyViolations: string[];
  budgetWarnings: string[];
  riskScore: number; // 0 - 100
  metadata: Record<string, any>;
  decisionNote?: string;
  decidedAt?: string;
  decidedBy?: string;
}

export interface ReviewItem {
  id: string;
  author: string;
  platform: "google" | "yelp" | "trustpilot" | "g2";
  rating: number;
  sentiment: "positive" | "neutral" | "negative";
  text: string;
  createdAt: string;
  status: "new" | "drafted" | "approved" | "replied";
  suggestedResponse?: string;
  alert: boolean;
}

export interface LeadConversation {
  id: string;
  customerName: string;
  customerHandle: string;
  platform: SocialChannel | "website";
  intent: "high_intent" | "support" | "pricing_inquiry" | "general";
  leadScore: number; // 0 - 100
  lastMessage: string;
  lastMessageAt: string;
  status: "open" | "draft_ready" | "replied" | "escalated";
  draftReply?: string;
  highIntentAlert: boolean;
  history: Array<{
    sender: "customer" | "agent" | "human";
    text: string;
    timestamp: string;
  }>;
}

export interface KeywordRanking {
  keyword: string;
  currentRank: number;
  previousRank: number;
  searchDemand: "very_high" | "high" | "medium" | "low";
  searchVolume: number;
  visibilityScore: number;
  difficulty: number;
  trend: "up" | "down" | "stable";
}

export interface CompetitorProfile {
  id: string;
  name: string;
  website: string;
  trackedChannels: SocialChannel[];
  marketShareEstimate: string;
  recentPromotion: {
    title: string;
    description: string;
    detectedAt: string;
    urgency: "high" | "medium" | "low";
  };
  keyDifferentiators: string[];
  shareOfVoice: number;
}

export interface BrandOSData {
  identity: {
    brandName: string;
    tagline: string;
    mission: string;
    coreValues: string[];
  };
  voice: {
    archetype: string;
    toneKeywords: string[];
    dos: string[];
    donts: string[];
    readingLevel: string;
  };
  positioning: {
    category: string;
    targetSegment: string;
    primaryPromise: string;
    reasonsToBelieve: string[];
  };
  audience: Array<{
    persona: string;
    title: string;
    painPoints: string[];
    keyAspirations: string[];
  }>;
  messagingBank: Array<{
    pillar: string;
    approvedPhrases: string[];
    proofPoints: string[];
  }>;
  approvedProofPoints: Array<{
    claim: string;
    citation: string;
    verified: boolean;
  }>;
  faqs: Array<{
    question: string;
    approvedAnswer: string;
    category: string;
  }>;
  visualGuidelines: {
    primaryColor: string;
    accentColor: string;
    fontFamily: string;
    imageryRules: string[];
  };
}

export interface BudgetOverview {
  monthlyBudget: number;
  currentSpend: number;
  forecastSpend: number;
  isOverCap: boolean;
  capAlertThreshold: number;
  channelBreakdown: Array<{
    channel: string;
    allocated: number;
    spent: number;
    roas: number;
  }>;
  agentSpendBreakdown: Array<{
    agentId: AgentId;
    spent: number;
    tokenCost: number;
  }>;
  recentTransactions: Array<{
    id: string;
    date: string;
    category: string;
    description: string;
    amount: number;
    approvedBy: string;
  }>;
}

export interface AuditLogEntry {
  timestamp: string;
  business_id: string;
  actor: string;
  action: string;
  resource: string;
  outcome: "success" | "denied" | "blocked" | "error";
  details: Record<string, any>;
  prev_hash: string;
  entry_hash: string;
}

export interface KillSwitchStatus {
  engaged: boolean;
  scope: string;
  reason: string;
  updated_at: string;
  updated_by: string;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: "admin" | "marketing_manager" | "content_creator" | "viewer";
  businessId: string;
  businessName: string;
  avatarUrl?: string;
}

// Local AI Infrastructure & Ollama Control Center Types
export interface HardwareTelemetry {
  cpu_count: number;
  cpu_utilization_percent: number;
  ram_total_mb: number;
  ram_available_mb: number;
  ram_used_mb: number;
  gpu_name: string | null;
  vram_total_mb: number | null;
  vram_free_mb: number | null;
  vram_used_mb: number | null;
  nvidia_smi_available: boolean;
  inference_active: boolean;
}

export interface OllamaModelInfo {
  name: string;
  tag: string;
  size_bytes: number;
  size_formatted: string;
  modified_at: string;
  digest: string;
  family: string;
  parameter_size: string;
  quantization: string;
  context_length: number;
  license: string;
  is_active: boolean;
  is_fallback: boolean;
  available: boolean;
  strengths: string[];
  notes?: string;
}

export interface OllamaRuntimeHealth {
  ok: boolean;
  status: "connected" | "disconnected" | "degraded";
  provider: "ollama";
  endpoint: string;
  version?: string;
  error?: string;
  latency_ms: number;
  last_checked: string;
  active_model: string;
  fallback_model: string;
  concurrency_limit: number;
  hardware: {
    cpu_count: number;
    ram_total_mb: number;
    ram_available_mb: number;
    gpu_name: string | null;
    vram_total_mb: number | null;
    vram_free_mb: number | null;
    nvidia_smi_available: boolean;
  };
}

export interface InferenceTelemetry {
  requests_processed: number;
  avg_latency_ms: number;
  tokens_generated: number;
  error_count: number;
  active_slots: number;
  concurrency_limit: number;
  p95_latency_ms: number;
  hourly_throughput: Array<{
    hour: string;
    tokens: number;
    requests: number;
  }>;
}

export interface LocalAIConfig {
  ollama_endpoint: string;
  default_model: string;
  fallback_model: string;
  request_timeout_seconds: number;
  max_tokens: number;
  context_length: number;
  temperature: number;
  concurrency_limit: number;
  gpu_preference: "auto" | "prefer_gpu" | "cpu_only";
  gpu_memory_budget_mb: number;
  cpu_fallback_enabled: boolean;
  allow_model_pull: boolean;
  max_input_chars: number;
  streaming_enabled: boolean;
}

export interface ModelBenchmarkResult {
  model_tag: string;
  parameter_size: string;
  tokens_per_second: number | null;
  ttft_ms: number | null;
  memory_used_mb: number | null;
  quality_score: number | null;
  license: string;
  strengths: string[];
  recommendation_status: "optimal" | "acceptable" | "constrained" | "unsupported";
  provenance: {
    hardware: string;
    timestamp: string | null;
    prompt: string | null;
    elapsed_sec: number | null;
    status: "measured" | "not_benchmarked" | "timed_out";
    notes: string;
  };
}

export interface RegistryCandidate {
  tag: string;
  family: string;
  parameter_size: string;
  license: string;
  quantization: string;
  context_length: number;
  approximate_size_gb: number;
  min_ram_gb: number;
  min_vram_gb: number;
  strengths: string[];
  notes: string;
  installed: boolean;
}

export interface AgentModelAssignment {
  agent_id: AgentId;
  agent_name: string;
  codename: string;
  assigned_model: string;
  fallback_model: string;
  is_model_available: boolean;
  max_tokens: number;
  temperature: number;
  status: AgentStatus;
}


