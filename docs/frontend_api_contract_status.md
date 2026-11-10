# Frontend API Contract Status

## Overview
Status of API contracts between the Next.js frontend and the Python backend for Phase 4. All contracts are typed with Zod/TanStack Query and have development fixture fallbacks.

## Available Endpoints

### ✅ GET /api/v1/brand-os
- **Response**: `ApiResponse<BrandOSData>`
- **Fixtures**: `MOCK_BRAND_OS` development fixture
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getBrandOS()` in BrandOSPage
- **Notes**: Returns development fixture when backend unavailable; clearly labelled with `isDevFixture: true`

### ✅ PUT /api/v1/brand-os
- **Request**: `Partial<BrandOSData>` (JSON body)
- **Response**: `ApiResponse<BrandOSData>`
- **Fixtures**: Merged `({ ...MOCK_BRAND_OS, ...data })`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.updateBrandOS(data)` 
- **Notes**: Used for UI editing; merges changes with fixture

### ✅ GET /api/v1/governance/killswitch
- **Response**: `ApiResponse<KillSwitchStatus>`
- **Fixtures**: `MOCK_KILL_SWITCH`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getKillSwitchStatus()`, `apiClient.toggleKillSwitch(engaged, reason)`
- **Notes**: governance block distinctly shown in UI when engaged

### ✅ GET /api/v1/governance/audit
- **Response**: `ApiResponse<{ entries: AuditLogEntry[]; chainValid: boolean }>`
- **Fixtures**: `MOCK_AUDIT_LOGS` + `chainValid: true`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getAuditLogs()`, `apiClient.verifyAuditChain()`
- **Notes**: Chain verification shown in UI; audit entries per business

### ✅ GET /api/v1/ai/hardware
- **Response**: `ApiResponse<HardwareTelemetry>`
- **Fixtures**: `MOCK_HARDWARE_TELEMETRY`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getHardwareTelemetry()`
- **Notes**: Hardware telemetry for control center dashboard

### ✅ GET /api/v1/ai/health
- **Response**: `ApiResponse<OllamaRuntimeHealth>`
- **Fixtures**: `MOCK_OLLAMA_HEALTH`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getOllamaHealth()`
- **Notes**: Ollama runtime health check

### ✅ GET /api/v1/ai/models
- **Response**: `ApiResponse<OllamaModelInfo[]>`
- **Fixtures**: `MOCK_OLLAMA_MODELS`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getOllamaModels()`
- **Notes**: Model registry presentation

### ✅ GET /api/v1/seo/rankings
- **Response**: `ApiResponse<{ keywords: KeywordRanking[]; visibilityScore: number }>`
- **Fixtures**: `MOCK_KEYWORDS` + visibilityScore: 84.6
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getSEOIntelligence()`
- **Notes**: SEO keyword rankings with mock data

### ✅ GET /api/v1/intelligence/competitors
- **Response**: `ApiResponse<CompetitorProfile[]>`
- **Fixtures**: `MOCK_COMPETITORS`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getCompetitorIntelligence()`
- **Notes**: Competitor intelligence with mock profiles

### ✅ GET /api/v1/auth/me
- **Response**: `ApiResponse<UserProfile>`
- **Fixtures**: `MOCK_USER`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getCurrentUser()`
- **Notes**: User profile for authenticated sessions

### ✅ POST /api/v1/auth/login
- **Request**: `{ email: string; password: string }`
- **Response**: `ApiResponse<{ token: string; user: UserProfile }>`
- **Fixtures**: `{ token: "dev_mock_jwt_token..."; user: MOCK_USER }`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.login()`
- **Notes**: Development mock JWT token

### ✅ GET /api/v1/agents
- **Response**: `ApiResponse<AgentDetails[]>`
- **Fixtures**: `MOCK_AGENTS`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getAgents()`
- **Notes**: Agent list with details

### ✅ GET /api/v1/budget
- **Response**: `ApiResponse<BudgetOverview>`
- **Fixtures**: `MOCK_BUDGET`
- **Status**: Available and operational
- **Frontend usage**: `apiClient.getBudgetOverview()`
- **Notes**: Budget overview with channel breakdown

## Partially Available Endpoints

### ⚠️ GET /api/v1/brand-os (with create/edit)
- Exists and functional for read operations
- Update endpoint exists (PUT)
- No CREATE endpoint implemented in backend (Phase 4 focus on knowledge repo, not CRUD API expansion)
- Frontend `updateBrandOS()` works; create would need backend endpoint

### ⚠️ Various agent execution endpoints
- Agent task triggering exists (`/api/v1/agents/{id}/execute`)
- Returns task_id, status "queued" in dev fixture mode
- Full eight-agent real-inference workflow not yet validated (Phase 3 baseline: 58 passed, 2 skipped)
- Not a Phase 4 introduction - pre-existing status

## Fixture/Development Mode Status

### Development Fixtures - All Strongly Typed
All API responses have strongly typed development fixtures in `frontend/src/fixtures.ts`:

| Fixture | Description |
|---------|-------------|
| `MOCK_BRAND_OS` | Full BrandOSData with all 27 template fields |
| `MOCK_KILL_SWITCH` | engaged/scope/reason/updated_at/updated_by |
| `MOCK_AUDIT_LOGS` | Array of audit log entries with chain metadata |
| `MOCK_HARDWARE_TELEMETRY` | CPU/RAM/GPU metrics |
| `MOCK_OLLAMA_HEALTH` | ok/status/active_model/fallback_model |
| `MOCK_OLLAMA_MODELS` | Model info array with names, sizes, contexts |
| `MOCK_OLLAMA_CONFIG` | LocalAIConfig with all settings |
| `MOCK_LOCAL_AI_CONFIG` | Same as Ollama config |
| `MOCK_MODEL_BENCHMARKS` | Model benchmark results |
| `MOCK_AGENT_MODEL_ASSIGNMENTS` | Agent-model assignments |
| `MOCK_REGISTRY_CANDIDATES` | Registry candidate models |
| `MOCK_AGENTS` | Agent details array |
| `MOCK_BUDGET` | Budget overview with spend breakdown |
| `MOCK_COMPETITORS` | Competitor profiles array |
| `MOCK_USER` | User profile with businessId, businessName |
| `MOCK_AGENTS` | Agent details |
| `MOCK_DRAFTS` | Content drafts |
| `MOCK_LEADS` | Lead conversations |
| `MOCK_REVIEWS` | Review items |
| `MOCK_KEYWORDS` | Keyword rankings |
| `MOCK_APPROVALS` | Approval requests |

### Fixture Labelling
- All fixtures have `// Development fixture: Strongly typed, strictly labelled development fallback` comment
- `ApiResponse` has `isDevFixture?: boolean` field
- API client warns when using fixtures: `[API] Backend unavailable at ${url} (${err.message}). Using typed development fixture for UI development.`
- `console.warn` when falling back to fixtures from `request()` method
- Never silently fall back to fixtures in production (explicit check in code)

### When Fixtures Are Used
1. Backend returns 404 endpoint not found
2. Backend connection fails (network error, timeout)
3. Development mode without backend server
4. Explicit test mode with mock data

### When Real Backend Is Used
1. Set `NEXT_PUBLIC_API_BASE_URL` environment variable
2. `apiClient` connects to `http://localhost:8000` (or custom port)
3. All endpoints return real data
4. Fixture fallback still available if endpoint temporarily unavailable
5. `isDevFixture` flag checks possible for backward compatibility

## API Contract Compliance Status

| Contract | Status | Notes |
|----------|--------|-------|
| BrandOSData type compatibility | ✅ Passes | Matches backend schemas exactly |
| TanStack Query integration | ✅ Passes | `useQuery` + `queryKey` working |
| Fixture fallback mechanism | ✅ Passes | Clearly labelled, never silent |
| API base URL configuration | ✅ Passes | `NEXT_PUBLIC_API_BASE_URL` env var |
| Error handling (404/503) | ✅ Passes | Fixture fallback with warning |
| TypeScript strict mode | ✅ Passes | No type errors |
| Production build | ✅ Passes | `npm run build` succeeds |
| No breaking changes to existing routes | ✅ Passes | All 15+ existing routes preserved |

## Contracts Requiring Backend Implementation

| Endpoint | Required Backend | Phase | Priority |
|----------|----------------|-------|----------|
| POST /api/v1/brand-os (create) | FastAPI route + handler | Future | Optional - Phase 5 |
| Agent task execution (full) | Engine execution | Pre-existing | Phase 3 |
| Full eight-agent inference | LLM inference pipeline | Pre-existing | Not validated yet |
| Budget agent spend tracking | Budget enforcer integration | Pre-existing | Phase 1 |

## Development Workflow

### Adding a New API Contract

1. Define TypeScript interface in `frontend/src/types/index.ts`
2. Add fixture in `frontend/src/fixtures.ts` (if development mode needed)
3. Add method to `ApiClient` class in `frontend/src/lib/api-client.ts`
4. Update `BrandOSPage` or relevant component to use new endpoint
5. Run `npm run type-check` and `npm run build` to verify
6. Run `npm test` to ensure no regressions

### Verifying Contract Compliance

```bash
# TypeScript
cd frontend && npm run type-check

# Lint
cd frontend && npm run lint

# Build
cd frontend && npm run build

# Test
cd frontend && npm test

# Check backend imports clean
cd src && python -m pytest tests/ --ignore=tests/integration -q

# Check ruff
python -m ruff check src tests
```

## Summary

### Contracts Available (13+)
- All read endpoints operational with fixture fallbacks
- Brand OS read/write endpoints functional
- Governance endpoints (killswitch, audit) working
- AI infrastructure endpoints operational
- SEO/competitor intelligence available

### Contracts Partially Available
- Create-brand-os endpoint (no backend route, but update works)
- Full agent execution (pre-existing, not Phase 4 work)

### No Breaking Changes
- All existing 15+ routes preserved
- No type errors introduced
- Production build succeeds
- All existing tests pass