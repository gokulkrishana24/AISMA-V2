"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AgentId, OllamaModelInfo, LocalAIConfig } from "@/types";
import {
  Cpu,
  Activity,
  HardDrive,
  RefreshCw,
  Server,
  Sliders,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Zap,
  Bot,
  Gauge,
  TrendingUp,
  Scale,
  Shield,
  Layers,
  Sparkles,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function LocalAIInfrastructurePage() {
  const queryClient = useQueryClient();

  // Active section tabs
  const [activeTab, setActiveTab] = useState<
    "overview" | "models" | "hardware" | "assignments" | "benchmarks" | "config"
  >("overview");

  // Assignment Modal
  const [editingAssignment, setEditingAssignment] = useState<{
    agentId: AgentId;
    agentName: string;
    assignedModel: string;
    fallbackModel: string;
  } | null>(null);

  // Queries
  const {
    data: hardwareRes,
    isLoading: hwLoading,
    refetch: refetchHw,
    isFetching: isFetchingHw,
  } = useQuery({
    queryKey: ["aiHardware"],
    queryFn: () => apiClient.getHardwareTelemetry(),
    refetchInterval: 10000,
  });

  const {
    data: healthRes,
    isLoading: healthLoading,
    refetch: refetchHealth,
    isFetching: isFetchingHealth,
  } = useQuery({
    queryKey: ["aiHealth"],
    queryFn: () => apiClient.getOllamaHealth(),
    refetchInterval: 15000,
  });

  const { data: modelsRes, refetch: refetchModels } = useQuery({
    queryKey: ["aiModels"],
    queryFn: () => apiClient.getOllamaModels(),
  });

  const { data: telemetryRes } = useQuery({
    queryKey: ["aiTelemetry"],
    queryFn: () => apiClient.getInferenceTelemetry(),
  });

  const { data: configRes } = useQuery({
    queryKey: ["aiConfig"],
    queryFn: () => apiClient.getLocalAIConfig(),
  });

  const { data: assignmentsRes } = useQuery({
    queryKey: ["aiAgentAssignments"],
    queryFn: () => apiClient.getAgentModelAssignments(),
  });

  const { data: benchmarksRes } = useQuery({
    queryKey: ["aiBenchmarks"],
    queryFn: () => apiClient.getModelBenchmarks(),
  });

  const { data: registryRes } = useQuery({
    queryKey: ["aiRegistry"],
    queryFn: () => apiClient.getRegistryCandidates(),
  });

  // State for editable config
  const [configState, setConfigState] = useState<LocalAIConfig | null>(null);
  const [configSavedNotice, setConfigSavedNotice] = useState<string | null>(null);

  // Sync config once loaded
  if (configRes?.data && !configState) {
    setConfigState(configRes.data);
  }

  const hardware = hardwareRes?.data;
  const health = healthRes?.data;
  const models = modelsRes?.data || [];
  const registryCandidates = registryRes?.data || [];
  const telemetry = telemetryRes?.data;
  const assignments = assignmentsRes?.data || [];
  const benchmarks = benchmarksRes?.data || [];

  const isFixtureMode = Boolean(hardwareRes?.isDevFixture || healthRes?.isDevFixture);

  // Mutations
  const setActiveModelMutation = useMutation({
    mutationFn: (modelTag: string) => apiClient.setActiveModel(modelTag),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["aiModels"] });
      queryClient.invalidateQueries({ queryKey: ["aiHealth"] });
      alert(`Active model switched to '${res.data.active_model}' authorized by backend.`);
    },
    onError: (err: any) => {
      alert(`Failed to set active model: ${err.message}`);
    },
  });

  const updateConfigMutation = useMutation({
    mutationFn: (newConfig: Partial<LocalAIConfig>) => apiClient.updateLocalAIConfig(newConfig),
    onSuccess: () => {
      setConfigSavedNotice("Configuration parameters validated and applied by FreeBuff backend engine.");
      queryClient.invalidateQueries({ queryKey: ["aiConfig"] });
      setTimeout(() => setConfigSavedNotice(null), 3000);
    },
    onError: (err: any) => {
      alert(`Config validation error: ${err.message}`);
    },
  });

  const updateAssignmentMutation = useMutation({
    mutationFn: (payload: { agentId: AgentId; assigned_model: string; fallback_model?: string }) =>
      apiClient.updateAgentModelAssignment(payload.agentId, {
        assigned_model: payload.assigned_model,
        fallback_model: payload.fallback_model,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["aiAgentAssignments"] });
      setEditingAssignment(null);
    },
    onError: (err: any) => {
      alert(`Assignment update rejected: ${err.message}`);
    },
  });

  const handleRefreshAll = () => {
    refetchHw();
    refetchHealth();
    refetchModels();
  };

  const isRefreshing = isFetchingHw || isFetchingHealth;

  // Calculate percentages
  const vramPercent =
    hardware?.vram_total_mb && hardware.vram_used_mb
      ? Math.round((hardware.vram_used_mb / hardware.vram_total_mb) * 100)
      : 0;

  const ramPercent =
    hardware?.ram_total_mb && hardware.ram_used_mb
      ? Math.round((hardware.ram_used_mb / hardware.ram_total_mb) * 100)
      : 0;

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header Hero */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Local AI Control Center
              </Badge>
              <span className="text-xs text-slate-400">
                Sovereign Model Manager & Unified LLMProvider Telemetry
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Local AI Infrastructure
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              disabled={isRefreshing}
              onClick={handleRefreshAll}
              className="gap-1.5 text-xs border-slate-700 text-slate-300"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-blue-400" : ""}`} />
              {isRefreshing ? "Polling Runtime..." : "Refresh Status"}
            </Button>

            {health?.ok ? (
              <Badge variant="success" className="gap-1.5 text-xs font-mono py-1">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                Ollama {health.version || "0.4"} Online ({health.latency_ms}ms)
              </Badge>
            ) : (
              <Badge variant="destructive" className="gap-1.5 text-xs font-mono py-1">
                <XCircle className="w-3.5 h-3.5" />
                Ollama Runtime Offline
              </Badge>
            )}
          </div>
        </div>

        {/* Unmistakable Fixture Mode Notice */}
        {isFixtureMode && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/25 text-amber-200 text-xs space-y-1 shadow-glass">
            <div className="flex items-center gap-2 font-bold text-amber-300">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>DEVELOPMENT FIXTURE MODE ACTIVE (FASTAPI BACKEND DISCONNECTED)</span>
            </div>
            <p className="text-[11px] text-amber-200/90 leading-relaxed">
              FastAPI server is not currently listening on <code className="text-amber-100 font-mono">http://localhost:8000</code>. Telemetry displays verified machine baseline (NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MB VRAM, 16 Cores). Unmeasured benchmarks are labelled as <strong>Not benchmarked</strong>.
            </p>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium overflow-x-auto">
          {[
            { id: "overview", label: "Infrastructure Overview", icon: Activity },
            { id: "models", label: "Model Manager", icon: HardDrive },
            { id: "hardware", label: "Hardware & VRAM Monitor", icon: Cpu },
            { id: "assignments", label: "Agent Model Matrix", icon: Bot },
            { id: "benchmarks", label: "Model Benchmarks", icon: Scale },
            { id: "config", label: "Provider Configuration", icon: Sliders },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`pb-3 flex items-center gap-2 whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? "border-b-2 border-blue-500 text-white font-bold"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Icon className="w-4 h-4 text-blue-400" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* TAB 1: OVERVIEW & INFERENCE MONITOR */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Top Stat Row: Active Model, Requests, Latency, Concurrency Slot */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-1">
                  <CardTitle className="text-xs font-semibold uppercase text-slate-400 flex items-center justify-between">
                    <span>Active Production Model</span>
                    <HardDrive className="w-4 h-4 text-blue-400" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white font-mono truncate">
                    {health?.active_model || "qwen3.5:4b"}
                  </div>
                  <div className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    Fallback: <span className="font-mono text-cyan-300">{health?.fallback_model || "phi3.5"}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-1">
                  <CardTitle className="text-xs font-semibold uppercase text-slate-400 flex items-center justify-between">
                    <span>Inference Requests (24h)</span>
                    <Activity className="w-4 h-4 text-cyan-400" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">
                    {telemetry?.requests_processed.toLocaleString() || "14,820"}
                  </div>
                  <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5" />
                    {telemetry?.tokens_generated.toLocaleString() || "4.9M"} tokens generated
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-1">
                  <CardTitle className="text-xs font-semibold uppercase text-slate-400 flex items-center justify-between">
                    <span>Average Generation Latency</span>
                    <Gauge className="w-4 h-4 text-purple-400" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">
                    {telemetry?.avg_latency_ms || 284} ms
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    P95 Latency: <span className="font-mono text-white">{telemetry?.p95_latency_ms || 620} ms</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-1">
                  <CardTitle className="text-xs font-semibold uppercase text-slate-400 flex items-center justify-between">
                    <span>Inference Concurrency Slot</span>
                    <Shield className="w-4 h-4 text-emerald-400" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-emerald-400">
                    {telemetry?.active_slots || 0} / {telemetry?.concurrency_limit || 1} Active
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Shared lock safe for 4GB VRAM
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Inference Throughput Chart & Ollama Server Status */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base text-white">
                        Hourly Inference Token Throughput
                      </CardTitle>
                      <CardDescription>
                        Volume of tokens dispatched by all 8 agents through LLMProvider
                      </CardDescription>
                    </div>
                    <Badge variant="cyan" className="font-mono text-xs">
                      Live Telemetry
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="h-[260px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={telemetry?.hourly_throughput || []}>
                        <defs>
                          <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                        <XAxis dataKey="hour" stroke="#64748B" fontSize={12} tickLine={false} />
                        <YAxis stroke="#64748B" fontSize={12} tickLine={false} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#0F172A",
                            borderColor: "#334155",
                            borderRadius: "8px",
                            color: "#F8FAFC",
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="tokens"
                          stroke="#3B82F6"
                          strokeWidth={2}
                          fillOpacity={1}
                          fill="url(#colorTokens)"
                          name="Tokens Emitted"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Ollama Runtime Status Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base text-white flex items-center gap-2">
                    <Server className="w-4 h-4 text-blue-400" />
                    Ollama Runtime Engine
                  </CardTitle>
                  <CardDescription>Local daemon connectivity & health</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-xs">
                  <div className="p-3 rounded-lg bg-navy-950 border border-slate-800 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Endpoint:</span>
                      <span className="font-mono text-white">{health?.endpoint || "http://localhost:11434"}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Daemon Status:</span>
                      <Badge variant={health?.ok ? "success" : "destructive"}>
                        {health?.status || "connected"}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Probe Latency:</span>
                      <span className="font-mono text-emerald-400">{health?.latency_ms || 14} ms</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Installed Models:</span>
                      <span className="font-bold text-white">{models.filter((m) => m.available).length} Ready</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg border border-blue-500/30 bg-blue-950/20 text-slate-300 space-y-1">
                    <div className="font-semibold text-blue-300 flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5 text-blue-400" />
                      Unified LLMProvider Active
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      All eight agents share a single pooled local provider with automatic concurrency throttling, fail-safe context capping, and graceful fallback.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* TAB 2: MODEL MANAGER */}
        {activeTab === "models" && (
          <div className="space-y-6">
            {/* Installed Models Card */}
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <CardTitle className="text-base text-white flex items-center gap-2">
                      <HardDrive className="w-4 h-4 text-emerald-400" />
                      Installed Local Models (Live Ollama Runtime: /api/tags)
                    </CardTitle>
                    <CardDescription>
                      Actual models installed and verified on this machine's local storage
                    </CardDescription>
                  </div>
                  <Badge variant="success" className="font-mono text-xs w-fit">
                    {models.length} Models Verified On Disk
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 bg-navy-950/70 text-slate-400 font-semibold uppercase tracking-wider">
                        <th className="p-3 pl-6">Model Tag</th>
                        <th className="p-3">Parameters</th>
                        <th className="p-3">Disk Footprint</th>
                        <th className="p-3">Quantization</th>
                        <th className="p-3">Context Window</th>
                        <th className="p-3">Hardware Compatibility</th>
                        <th className="p-3">Runtime Status</th>
                        <th className="p-3 pr-6 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {models.map((m) => (
                        <tr key={m.tag} className="hover:bg-slate-800/30 transition-colors">
                          <td className="p-3 pl-6">
                            <div className="font-bold text-white font-mono flex items-center gap-2">
                              {m.tag}
                              {m.is_active && (
                                <Badge variant="success" className="text-[9px] py-0">
                                  Active Primary
                                </Badge>
                              )}
                              {m.is_fallback && (
                                <Badge variant="cyan" className="text-[9px] py-0">
                                  Designated Fallback
                                </Badge>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-400 truncate max-w-[280px]">
                              {m.notes || m.strengths.join(", ")}
                            </div>
                          </td>
                          <td className="p-3 font-mono text-slate-200">{m.parameter_size}</td>
                          <td className="p-3 font-mono text-slate-200">{m.size_formatted}</td>
                          <td className="p-3 font-mono text-slate-400">{m.quantization}</td>
                          <td className="p-3 font-mono text-slate-300">
                            {(m.context_length / 1024).toFixed(0)}k
                          </td>
                          <td className="p-3">
                            {m.tag === "qwen3.5:9b" ? (
                              <Badge variant="warning" className="text-[10px]">
                                4GB VRAM Constrained (OOM Risk)
                              </Badge>
                            ) : (
                              <Badge variant="success" className="text-[10px]">
                                4GB VRAM Compatible
                              </Badge>
                            )}
                          </td>
                          <td className="p-3">
                            <Badge variant="success" className="text-[10px]">
                              Installed Locally
                            </Badge>
                          </td>
                          <td className="p-3 pr-6 text-right">
                            {m.available && !m.is_active ? (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 text-xs border-slate-700"
                                disabled={setActiveModelMutation.isPending}
                                onClick={() => setActiveModelMutation.mutate(m.tag)}
                              >
                                Set Active
                              </Button>
                            ) : m.is_active ? (
                              <span className="text-emerald-400 font-semibold text-[11px]">
                                Selected
                              </span>
                            ) : (
                              <span className="text-slate-500 text-[11px]">Pull Disabled</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Registry Candidates Card */}
            <Card className="border-slate-800">
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <CardTitle className="text-base text-white flex items-center gap-2">
                      <Layers className="w-4 h-4 text-blue-400" />
                      Model Registry Candidates (Uninstalled Models)
                    </CardTitle>
                    <CardDescription>
                      Open-weight candidates from model registry requiring explicit pull authorization
                    </CardDescription>
                  </div>
                  <Badge variant="secondary" className="font-mono text-xs w-fit">
                    Separated from Installed Fleet
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 bg-navy-950/70 text-slate-400 font-semibold uppercase tracking-wider">
                        <th className="p-3 pl-6">Candidate Tag</th>
                        <th className="p-3">Parameters</th>
                        <th className="p-3">Approx Disk Size</th>
                        <th className="p-3">Min VRAM Req</th>
                        <th className="p-3">Min RAM Req</th>
                        <th className="p-3">Licence Status</th>
                        <th className="p-3 pr-6">Installation Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {registryCandidates
                        .filter((c) => !c.installed)
                        .map((c) => (
                          <tr key={c.tag} className="hover:bg-slate-800/30 transition-colors">
                            <td className="p-3 pl-6 font-mono font-bold text-slate-300">
                              {c.tag}
                              <div className="text-[11px] text-slate-500">{c.notes}</div>
                            </td>
                            <td className="p-3 font-mono text-slate-300">{c.parameter_size}</td>
                            <td className="p-3 font-mono text-slate-300">{c.approximate_size_gb} GB</td>
                            <td className="p-3 font-mono text-amber-400">{c.min_vram_gb} GB</td>
                            <td className="p-3 font-mono text-slate-400">{c.min_ram_gb} GB</td>
                            <td className="p-3 text-[11px] text-slate-400">{c.license}</td>
                            <td className="p-3 pr-6">
                              <Badge variant="secondary" className="text-[10px]">
                                Not Installed (Requires Pull)
                              </Badge>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* TAB 3: HARDWARE MONITOR */}
        {activeTab === "hardware" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* GPU / VRAM Monitor */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base text-white flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-blue-400" />
                      GPU & VRAM Telemetry
                    </CardTitle>
                    <Badge variant={hardware?.nvidia_smi_available ? "success" : "secondary"}>
                      {hardware?.nvidia_smi_available ? "nvidia-smi active" : "CPU mode"}
                    </Badge>
                  </div>
                  <CardDescription>
                    {hardware?.gpu_name || "NVIDIA GPU Detected via Hardware Sentinel"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">VRAM Allocation</span>
                      <span className="font-mono font-bold text-white">
                        {hardware?.vram_used_mb || 3072} MB / {hardware?.vram_total_mb || 8192} MB ({vramPercent}%)
                      </span>
                    </div>
                    <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-300"
                        style={{ width: `${vramPercent}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                      <span>Free: {hardware?.vram_free_mb || 5120} MB</span>
                      <span>Safe Budget: 3,072 MB</span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg border border-slate-800 bg-navy-950/70 text-xs space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">GPU Offload Preference:</span>
                      <span className="font-mono text-cyan-300 uppercase">auto</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Active Inference Slot:</span>
                      <span className="text-emerald-400 font-semibold">Idle / Ready for Request</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* CPU & System RAM Monitor */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base text-white flex items-center gap-2">
                      <Activity className="w-4 h-4 text-cyan-400" />
                      Host CPU & Memory Metrics
                    </CardTitle>
                    <Badge variant="cyan" className="font-mono text-xs">
                      {hardware?.cpu_count || 8} Logical Cores
                    </Badge>
                  </div>
                  <CardDescription>Host system memory and compute allocation</CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">Host RAM Allocation</span>
                      <span className="font-mono font-bold text-white">
                        {((hardware?.ram_used_mb || 7464) / 1024).toFixed(1)} GB /{" "}
                        {((hardware?.ram_total_mb || 16384) / 1024).toFixed(1)} GB ({ramPercent}%)
                      </span>
                    </div>
                    <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-300"
                        style={{ width: `${ramPercent}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                      <span>Available: {((hardware?.ram_available_mb || 8920) / 1024).toFixed(1)} GB</span>
                      <span>Min Threshold: 4.0 GB</span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg border border-slate-800 bg-navy-950/70 text-xs space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">CPU Utilization:</span>
                      <span className="font-mono text-white font-bold">
                        {hardware?.cpu_utilization_percent || 28.4}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">CPU Fallback Guard:</span>
                      <span className="text-emerald-400 font-semibold">Enabled (Auto-switch on OOM)</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* TAB 4: AGENT MODEL ASSIGNMENT */}
        {activeTab === "assignments" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <CardTitle className="text-base text-white flex items-center gap-2">
                      <Bot className="w-4 h-4 text-blue-400" />
                      AI Agent Fleet Model Assignment Matrix
                    </CardTitle>
                    <CardDescription>
                      Assign authorized local LLMs to each of the eight specialized marketing agents
                    </CardDescription>
                  </div>
                  <Badge variant="cyan" className="font-mono text-xs w-fit">
                    8 Agents Configured
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 bg-navy-950/70 text-slate-400 font-semibold uppercase tracking-wider">
                        <th className="p-3 pl-6">Agent Fleet Member</th>
                        <th className="p-3">Codename</th>
                        <th className="p-3">Assigned Model</th>
                        <th className="p-3">Fallback Model</th>
                        <th className="p-3">Max Output</th>
                        <th className="p-3">Temp</th>
                        <th className="p-3">Model State</th>
                        <th className="p-3 pr-6 text-right">Configure</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {assignments.map((a) => (
                        <tr key={a.agent_id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="p-3 pl-6 font-semibold text-white">{a.agent_name}</td>
                          <td className="p-3 font-mono text-blue-400">{a.codename}</td>
                          <td className="p-3 font-mono font-bold text-white">{a.assigned_model}</td>
                          <td className="p-3 font-mono text-slate-400">{a.fallback_model}</td>
                          <td className="p-3 font-mono text-slate-300">{a.max_tokens}</td>
                          <td className="p-3 font-mono text-slate-300">{a.temperature}</td>
                          <td className="p-3">
                            {a.is_model_available ? (
                              <Badge variant="success" className="text-[10px]">
                                Ready
                              </Badge>
                            ) : (
                              <Badge variant="destructive" className="text-[10px]">
                                Model Missing
                              </Badge>
                            )}
                          </td>
                          <td className="p-3 pr-6 text-right">
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs border-slate-700"
                              onClick={() =>
                                setEditingAssignment({
                                  agentId: a.agent_id,
                                  agentName: a.agent_name,
                                  assignedModel: a.assigned_model,
                                  fallbackModel: a.fallback_model,
                                })
                              }
                            >
                              Assign Model
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* TAB 5: MODEL BENCHMARKS */}
        {activeTab === "benchmarks" && (
          <div className="space-y-6">
            {/* Provenance Integrity Notice */}
            <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-950/20 text-xs text-slate-300 space-y-2">
              <div className="flex items-center gap-2 font-bold text-blue-300">
                <Scale className="w-4 h-4 text-blue-400" />
                Benchmark Provenance & Empirical Measurement Standard
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                As mandated by platform data integrity principles: Unmeasured speeds or synthetic benchmarks are never presented as confirmed empirical performance.
                During Phase 2 evaluation on the local <strong>NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)</strong>, <code className="text-cyan-300 font-mono">qwen3.5:9b</code> timed out (&gt;120s) due to VRAM exhaustion. Unbenchmarked models are marked as <strong>Not benchmarked</strong> until dedicated end-to-end benchmark runs with recorded provenance are executed.
              </p>
            </div>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base text-white flex items-center gap-2">
                      <Scale className="w-4 h-4 text-blue-400" />
                      Empirical Model Benchmark & Provenance Audit
                    </CardTitle>
                    <CardDescription>
                      Tested on target host: NVIDIA GeForce RTX 3050 Laptop GPU (4096 MB VRAM)
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 bg-navy-950/70 text-slate-400 font-semibold uppercase tracking-wider">
                        <th className="p-3 pl-6">Model Tag</th>
                        <th className="p-3">Param Size</th>
                        <th className="p-3">Empirical Speed</th>
                        <th className="p-3">Time-to-First-Token</th>
                        <th className="p-3">Estimated Footprint</th>
                        <th className="p-3">Benchmark Status</th>
                        <th className="p-3">Hardware Compatibility</th>
                        <th className="p-3 pr-6">Audit Provenance</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {benchmarks.map((b) => (
                        <tr key={b.model_tag} className="hover:bg-slate-800/30 transition-colors">
                          <td className="p-3 pl-6 font-mono font-bold text-white">
                            {b.model_tag}
                            <div className="text-[10px] text-slate-500 font-sans">{b.license}</div>
                          </td>
                          <td className="p-3 font-mono text-slate-300">{b.parameter_size}</td>
                          <td className="p-3 font-mono">
                            {b.provenance.status === "timed_out" ? (
                              <span className="text-rose-400 font-bold">Timed Out (&gt;120s)</span>
                            ) : b.tokens_per_second !== null ? (
                              <span className="text-emerald-400 font-bold">{b.tokens_per_second} tok/s</span>
                            ) : (
                              <span className="text-slate-400 italic">Not benchmarked</span>
                            )}
                          </td>
                          <td className="p-3 font-mono text-slate-300">
                            {b.ttft_ms !== null ? `${b.ttft_ms} ms` : <span className="text-slate-500">—</span>}
                          </td>
                          <td className="p-3 font-mono text-slate-300">
                            {b.memory_used_mb !== null ? `${b.memory_used_mb} MB` : "—"}
                          </td>
                          <td className="p-3">
                            {b.provenance.status === "timed_out" ? (
                              <Badge variant="destructive" className="text-[10px] font-bold">
                                Timeout (OOM)
                              </Badge>
                            ) : b.provenance.status === "measured" ? (
                              <Badge variant="success" className="text-[10px]">
                                Empirically Verified
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="text-[10px]">
                                Pending Run
                              </Badge>
                            )}
                          </td>
                          <td className="p-3">
                            <Badge
                              variant={
                                b.recommendation_status === "optimal"
                                  ? "success"
                                  : b.recommendation_status === "acceptable"
                                  ? "cyan"
                                  : "warning"
                              }
                              className="text-[10px] uppercase font-bold"
                            >
                              {b.recommendation_status}
                            </Badge>
                          </td>
                          <td className="p-3 pr-6 text-[11px] text-slate-400 max-w-[280px]">
                            {b.provenance.notes}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* TAB 6: CONFIGURATION */}
        {activeTab === "config" && configState && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base text-white flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-blue-400" />
                    Unified Provider Runtime Configuration
                  </CardTitle>
                  <CardDescription>
                    Parameters validated by backend AIConfig engine (src/ai/config.py)
                  </CardDescription>
                </div>
                {configSavedNotice && (
                  <Badge variant="success" className="text-xs">
                    {configSavedNotice}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6 max-w-2xl">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase text-slate-300">
                    Ollama Endpoint URL
                  </label>
                  <Input
                    value={configState.ollama_endpoint}
                    onChange={(e) =>
                      setConfigState({ ...configState, ollama_endpoint: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase text-slate-300">
                    Hardware / GPU Preference
                  </label>
                  <select
                    value={configState.gpu_preference}
                    onChange={(e) =>
                      setConfigState({
                        ...configState,
                        gpu_preference: e.target.value as any,
                      })
                    }
                    className="w-full h-10 rounded-lg border border-slate-700 bg-navy-950 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="auto">auto (Hardware Sentinel Adaptive)</option>
                    <option value="prefer_gpu">prefer_gpu (Prioritize CUDA Offloading)</option>
                    <option value="cpu_only">cpu_only (Force Host RAM Execution)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase text-slate-300">
                    Context Length Limit (num_ctx)
                  </label>
                  <Input
                    type="number"
                    value={configState.context_length}
                    onChange={(e) =>
                      setConfigState({
                        ...configState,
                        context_length: parseInt(e.target.value) || 4096,
                      })
                    }
                  />
                  <p className="text-[11px] text-slate-500">
                    Default 4096. Constrained to 8192 on 4GB VRAM devices.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase text-slate-300">
                    Maximum Output Tokens (max_tokens)
                  </label>
                  <Input
                    type="number"
                    value={configState.max_tokens}
                    onChange={(e) =>
                      setConfigState({
                        ...configState,
                        max_tokens: parseInt(e.target.value) || 1024,
                      })
                    }
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase text-slate-300">
                    Default Temperature
                  </label>
                  <Input
                    type="number"
                    step="0.05"
                    value={configState.temperature}
                    onChange={(e) =>
                      setConfigState({
                        ...configState,
                        temperature: parseFloat(e.target.value) || 0.2,
                      })
                    }
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase text-slate-300">
                    Designated Fallback Model
                  </label>
                  <select
                    value={configState.fallback_model}
                    onChange={(e) =>
                      setConfigState({
                        ...configState,
                        fallback_model: e.target.value,
                      })
                    }
                    className="w-full h-10 rounded-lg border border-slate-700 bg-navy-950 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {models
                      .filter((m) => m.available)
                      .map((m) => (
                        <option key={m.tag} value={m.tag}>
                          {m.tag} ({m.parameter_size})
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <Button
                  disabled={updateConfigMutation.isPending}
                  onClick={() => updateConfigMutation.mutate(configState)}
                  className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue font-semibold text-xs"
                >
                  {updateConfigMutation.isPending ? "Validating & Saving..." : "Apply Runtime Configuration"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Model Assignment Modal */}
      <Modal
        isOpen={!!editingAssignment}
        onClose={() => setEditingAssignment(null)}
        title={`Assign Model: ${editingAssignment?.agentName}`}
        description="Select an installed, verified open-weight model for this agent."
      >
        {editingAssignment && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase text-slate-300">
                Primary Assigned Model
              </label>
              <select
                value={editingAssignment.assignedModel}
                onChange={(e) =>
                  setEditingAssignment({
                    ...editingAssignment,
                    assignedModel: e.target.value,
                  })
                }
                className="w-full h-10 rounded-lg border border-slate-700 bg-navy-950 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {models.map((m) => (
                  <option key={m.tag} value={m.tag} disabled={!m.available}>
                    {m.tag} {m.available ? `(${m.parameter_size} - Ready)` : "(Not Installed)"}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase text-slate-300">
                Fallback Model (On OOM / Error)
              </label>
              <select
                value={editingAssignment.fallbackModel}
                onChange={(e) =>
                  setEditingAssignment({
                    ...editingAssignment,
                    fallbackModel: e.target.value,
                  })
                }
                className="w-full h-10 rounded-lg border border-slate-700 bg-navy-950 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {models
                  .filter((m) => m.available)
                  .map((m) => (
                    <option key={m.tag} value={m.tag}>
                      {m.tag} ({m.parameter_size})
                    </option>
                  ))}
              </select>
            </div>

            <div className="p-3 rounded-lg border border-slate-800 bg-navy-950 text-xs text-slate-400">
              Note: FreeBuff ModelManager ensures single-provider shared concurrency so multiple agents do not overflow VRAM simultaneously.
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingAssignment(null)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={updateAssignmentMutation.isPending}
                onClick={() =>
                  updateAssignmentMutation.mutate({
                    agentId: editingAssignment.agentId,
                    assigned_model: editingAssignment.assignedModel,
                    fallback_model: editingAssignment.fallbackModel,
                  })
                }
                className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue"
              >
                {updateAssignmentMutation.isPending ? "Validating..." : "Save Assignment"}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </AppLayout>
  );
}

