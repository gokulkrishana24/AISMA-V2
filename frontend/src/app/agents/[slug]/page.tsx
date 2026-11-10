"use client";

import { useState } from "react";
import { useParams, notFound } from "next/navigation";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AgentId } from "@/types";
import {
  Bot,
  Play,
  RotateCw,
  CheckCircle2,
  Clock,
  Cpu,
  Layers,
  Shield,
  Activity,
  ArrowLeft,
  Sliders,
  Terminal,
  FileCode,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

const SLUG_TO_ID: Record<string, AgentId> = {
  "search-visibility": "search_visibility",
  "market-radar": "market_radar",
  "content-engine": "content_engine",
  "creative-studio": "creative_studio",
  "publishing-social": "publishing_social",
  "reviews-reputation": "reviews_reputation",
  "leads-conversations": "leads_conversations",
  "results-roi": "results_roi",
};

export default function IndividualAgentPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const agentId = SLUG_TO_ID[slug];

  const [activeTab, setActiveTab] = useState<"tasks" | "config" | "permissions" | "io">("tasks");
  const [selectedTaskIndex, setSelectedTaskIndex] = useState(0);

  const { data: agentRes, isLoading } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => (agentId ? apiClient.getAgentById(agentId) : null),
    enabled: !!agentId,
  });

  if (!agentId) {
    return notFound();
  }

  const agent = agentRes?.data;

  if (isLoading || !agent) {
    return (
      <AppLayout>
        <div className="py-12 text-center text-slate-400">Loading Agent Telemetry...</div>
      </AppLayout>
    );
  }

  const recentTasks = agent.recentTasks || [];
  const currentTask = recentTasks[selectedTaskIndex] || recentTasks[0];

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <Link href="/agents">
              <Button variant="outline" size="sm" className="h-8 px-2.5">
                <ArrowLeft className="w-3.5 h-3.5 mr-1" />
                Fleet Overview
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-blue-400 font-bold uppercase tracking-widest">
                  {agent.codename}
                </span>
                <Badge
                  variant={agent.status === "active" ? "success" : "default"}
                  className="text-[10px] uppercase font-bold"
                >
                  {agent.status}
                </Badge>
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                {agent.name}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="cyan" className="font-mono text-xs">
              <Cpu className="w-3 h-3 mr-1" />
              {agent.config.model.split(" ")[0]}
            </Badge>
          </div>
        </div>

        {/* 4 Performance Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Success Reliability
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{agent.successRate}%</div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {agent.totalExecutions} total invocations
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Average Latency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{agent.avgLatencyMs} ms</div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Sub-second local inference speed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Non-Fatal Retries
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{agent.errorCount}</div>
              <p className="text-[11px] text-emerald-400 mt-0.5">
                Zero security/policy violations
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Execution Frequency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-white">{agent.config.frequency}</div>
              <p className="text-[11px] text-blue-400 mt-0.5">
                Autonomous Loop Active
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium">
          <button
            onClick={() => setActiveTab("tasks")}
            className={`pb-3 transition-colors ${
              activeTab === "tasks"
                ? "border-b-2 border-blue-500 text-white font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Execution History & Logs
          </button>
          <button
            onClick={() => setActiveTab("io")}
            className={`pb-3 transition-colors ${
              activeTab === "io"
                ? "border-b-2 border-blue-500 text-white font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Input / Output Telemetry
          </button>
          <button
            onClick={() => setActiveTab("config")}
            className={`pb-3 transition-colors ${
              activeTab === "config"
                ? "border-b-2 border-blue-500 text-white font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Local Model & Parameters
          </button>
          <button
            onClick={() => setActiveTab("permissions")}
            className={`pb-3 transition-colors ${
              activeTab === "permissions"
                ? "border-b-2 border-blue-500 text-white font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Governance Boundaries
          </button>
        </div>

        {/* Tab 1: Task History */}
        {activeTab === "tasks" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Task List */}
              <div className="space-y-3">
                <div className="text-xs font-semibold uppercase text-slate-400">
                  Recent Executions ({agent.recentTasks.length})
                </div>
                {agent.recentTasks.map((t, idx) => (
                  <button
                    key={t.id}
                    onClick={() => setSelectedTaskIndex(idx)}
                    className={`w-full p-3 rounded-lg border text-left transition-all ${
                      idx === selectedTaskIndex
                        ? "border-blue-500 bg-blue-600/15 shadow-glow-blue"
                        : "border-slate-800 bg-navy-950/60 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="font-mono text-blue-400 font-semibold">{t.id}</span>
                      <Badge variant="success" className="text-[9px] py-0">
                        {t.status}
                      </Badge>
                    </div>
                    <div className="text-xs font-semibold text-white truncate">{t.title}</div>
                    <div className="text-[10px] text-slate-500 mt-1 flex items-center justify-between">
                      <span>{new Date(t.startedAt).toLocaleTimeString()}</span>
                      {t.tokensUsed && <span>{t.tokensUsed} tokens</span>}
                    </div>
                  </button>
                ))}
              </div>

              {/* Task Details Display */}
              <div className="md:col-span-2 space-y-4">
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-bold text-white">
                        {currentTask?.title}
                      </CardTitle>
                      <Badge variant="cyan" className="font-mono text-xs">
                        Task #{currentTask?.id}
                      </Badge>
                    </div>
                    <CardDescription>
                      Dispatched at {currentTask?.startedAt} • Latency: {currentTask?.latencyMs || 240}ms
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="text-xs font-semibold text-slate-400 mb-1.5 flex items-center gap-1.5">
                        <Terminal className="w-3.5 h-3.5 text-blue-400" />
                        Input Parameters
                      </div>
                      <pre className="p-3 rounded-lg bg-navy-950 border border-slate-800 font-mono text-xs text-blue-200 overflow-x-auto">
                        {JSON.stringify(currentTask?.inputData, null, 2)}
                      </pre>
                    </div>

                    <div>
                      <div className="text-xs font-semibold text-slate-400 mb-1.5 flex items-center gap-1.5">
                        <FileCode className="w-3.5 h-3.5 text-emerald-400" />
                        Generated Output Data
                      </div>
                      <pre className="p-3 rounded-lg bg-navy-950 border border-slate-800 font-mono text-xs text-emerald-200 overflow-x-auto">
                        {JSON.stringify(currentTask?.outputData || { status: "running", progress: "45%" }, null, 2)}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Input / Output Telemetry */}
        {activeTab === "io" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white">Real-Time IO Telemetry</CardTitle>
              <CardDescription>
                Live input prompt templates and output tensors generated by this agent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-lg bg-navy-950 border border-slate-800 space-y-2">
                <div className="text-xs font-semibold text-slate-300">System Instruction Signature:</div>
                <p className="text-xs text-slate-400 font-mono">
                  You are {agent.name} [{agent.codename}]. Your responsibility is {agent.description}. You operate under strict default-deny governance with zero unauthorized publishing authority.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tab 3: Configuration */}
        {activeTab === "config" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-blue-400" />
                Local LLM Inference Configuration
              </CardTitle>
              <CardDescription>
                Parameters passed to Ollama / vLLM / local model runner
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-navy-950 border border-slate-800">
                  <span className="text-xs text-slate-400 block">Model Weight</span>
                  <span className="text-sm font-semibold text-white font-mono">{agent.config.model}</span>
                </div>
                <div className="p-3 rounded-lg bg-navy-950 border border-slate-800">
                  <span className="text-xs text-slate-400 block">Temperature</span>
                  <span className="text-sm font-semibold text-white font-mono">{agent.config.temperature}</span>
                </div>
                <div className="p-3 rounded-lg bg-navy-950 border border-slate-800">
                  <span className="text-xs text-slate-400 block">Max Tokens</span>
                  <span className="text-sm font-semibold text-white font-mono">{agent.config.maxTokens}</span>
                </div>
                <div className="p-3 rounded-lg bg-navy-950 border border-slate-800">
                  <span className="text-xs text-slate-400 block">Autonomous Loop</span>
                  <span className="text-sm font-semibold text-emerald-400">
                    {agent.config.autonomousMode ? "Enabled (Managed)" : "Human-Dispatched"}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tab 4: Permissions */}
        {activeTab === "permissions" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-400" />
                Backend Governance Permissions (AGENT_PERMISSIONS)
              </CardTitle>
              <CardDescription>
                Strictly enforced by Python permissions engine. Prompts are not a security boundary.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {agent.permissions.map((perm) => (
                  <div
                    key={perm}
                    className="p-2.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-xs font-mono text-emerald-300 flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{perm}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}

