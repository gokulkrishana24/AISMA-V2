import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const FRONTEND_DIR = path.resolve(import.meta.dirname, "..");

test("Next.js App Router Structure & All 8 Agent Routes", () => {
  const pages = [
    "src/app/page.tsx",
    "src/app/dashboard/page.tsx",
    "src/app/login/page.tsx",
    "src/app/register/page.tsx",
    "src/app/forgot-password/page.tsx",
    "src/app/onboarding/page.tsx",
    "src/app/agents/page.tsx",
    "src/app/agents/[slug]/page.tsx",
    "src/app/content-studio/page.tsx",
    "src/app/creative-studio/page.tsx",
    "src/app/calendar/page.tsx",
    "src/app/approvals/page.tsx",
    "src/app/reviews/page.tsx",
    "src/app/conversations/page.tsx",
    "src/app/seo/page.tsx",
    "src/app/competitor/page.tsx",
    "src/app/analytics/page.tsx",
    "src/app/brand-os/page.tsx",
    "src/app/budget/page.tsx",
    "src/app/audit/page.tsx",
    "src/app/settings/page.tsx",
    "src/app/infrastructure/page.tsx",
  ];

  for (const pagePath of pages) {
    const full = path.join(FRONTEND_DIR, pagePath);
    assert.ok(fs.existsSync(full), `Required page missing: ${pagePath}`);
  }
});

test("Agent Command Center Config & Governance Restrictions", () => {
  const dynamicAgentPage = fs.readFileSync(
    path.join(FRONTEND_DIR, "src/app/agents/[slug]/page.tsx"),
    "utf-8"
  );

  const expectedAgents = [
    "search-visibility",
    "market-radar",
    "content-engine",
    "creative-studio",
    "publishing-social",
    "reviews-reputation",
    "leads-conversations",
    "results-roi",
  ];

  for (const slug of expectedAgents) {
    assert.ok(
      dynamicAgentPage.includes(slug),
      `Dynamic agent router must map agent slug: ${slug}`
    );
  }
});

test("API Client Governance Enforcement (No Frontend Bypass)", () => {
  const apiClientCode = fs.readFileSync(
    path.join(FRONTEND_DIR, "src/lib/api-client.ts"),
    "utf-8"
  );

  // Verify NEXT_PUBLIC_API_BASE_URL is utilized
  assert.ok(
    apiClientCode.includes("NEXT_PUBLIC_API_BASE_URL"),
    "Must support NEXT_PUBLIC_API_BASE_URL environment variable"
  );

  // Verify approval submission routes to backend
  assert.ok(
    apiClientCode.includes("/api/v1/approvals/"),
    "Approval decision must route through backend authority endpoint"
  );

  // Verify kill switch endpoint
  assert.ok(
    apiClientCode.includes("/api/v1/governance/killswitch"),
    "Kill switch must route to backend governance endpoint"
  );

  // Verify SHA-256 verification endpoint
  assert.ok(
    apiClientCode.includes("/api/v1/governance/audit/verify"),
    "Audit chain verification must connect to backend SHA-256 verifier"
  );
});

test("Design System Navy Theme & Tailwind Tokens", () => {
  const tailwindConfig = fs.readFileSync(
    path.join(FRONTEND_DIR, "tailwind.config.ts"),
    "utf-8"
  );

  assert.ok(tailwindConfig.includes("navy"), "Must define enterprise dark navy palette");
  assert.ok(tailwindConfig.includes("glow-blue"), "Must define subtle glow accents");

  const globalsCss = fs.readFileSync(
    path.join(FRONTEND_DIR, "src/styles/globals.css"),
    "utf-8"
  );
  assert.ok(globalsCss.includes("glass-panel"), "Must define glass effect classes");
});

test("Local AI Infrastructure & Unified LLMProvider Contract", () => {
  const infraPage = fs.readFileSync(
    path.join(FRONTEND_DIR, "src/app/infrastructure/page.tsx"),
    "utf-8"
  );

  // Check required components
  assert.ok(infraPage.includes("Model Manager"), "Must contain Model Manager section");
  assert.ok(infraPage.includes("Hardware & VRAM Monitor"), "Must contain Hardware & VRAM monitor");
  assert.ok(infraPage.includes("Ollama Runtime Engine"), "Must contain Ollama runtime engine section");
  assert.ok(infraPage.includes("Inference Token Throughput"), "Must contain Inference monitor telemetry");
  assert.ok(infraPage.includes("Provider Configuration"), "Must contain Provider configuration");
  assert.ok(infraPage.includes("Model Benchmark"), "Must contain Model Benchmark comparison");
  assert.ok(infraPage.includes("Fleet Model Assignment Matrix"), "Must contain Agent Model Assignment matrix");

  // Check API client contract integration
  const apiClientCode = fs.readFileSync(
    path.join(FRONTEND_DIR, "src/lib/api-client.ts"),
    "utf-8"
  );
  assert.ok(apiClientCode.includes("/api/v1/ai/hardware"), "Must connect to hardware telemetry endpoint");
  assert.ok(apiClientCode.includes("/api/v1/ai/health"), "Must connect to Ollama health endpoint");
  assert.ok(apiClientCode.includes("/api/v1/ai/models"), "Must connect to Ollama models endpoint");
  assert.ok(apiClientCode.includes("/api/v1/ai/telemetry"), "Must connect to inference telemetry endpoint");
  assert.ok(apiClientCode.includes("/api/v1/ai/config"), "Must connect to AI config endpoint");
  assert.ok(apiClientCode.includes("/api/v1/ai/agent-assignments"), "Must connect to agent assignments endpoint");
  assert.ok(apiClientCode.includes("/api/v1/ai/benchmarks"), "Must connect to model benchmarks endpoint");
});

