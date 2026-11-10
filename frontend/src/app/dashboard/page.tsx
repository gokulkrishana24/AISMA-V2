"use client";

import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { formatCurrency, formatNumber } from "@/lib/utils";
import {
  TrendingUp,
  Users,
  Eye,
  DollarSign,
  ShieldAlert,
  ArrowUpRight,
  ArrowRight,
  Clock,
  Sparkles,
  CheckCircle,
  FileText,
  Activity,
  Bot,
  Layers,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

const PERFORMANCE_DATA = [
  { day: "Mon", impressions: 42000, engagement: 3100, leads: 18 },
  { day: "Tue", impressions: 58000, engagement: 4400, leads: 24 },
  { day: "Wed", impressions: 63000, engagement: 5200, leads: 32 },
  { day: "Thu", impressions: 84000, engagement: 6900, leads: 41 },
  { day: "Fri", impressions: 92000, engagement: 7400, leads: 48 },
  { day: "Sat", impressions: 71000, engagement: 5100, leads: 26 },
  { day: "Sun", impressions: 68000, engagement: 4800, leads: 22 },
];

export default function DashboardPage() {
  const { data: agentsRes, isLoading: agentsLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiClient.getAgents(),
  });

  const { data: approvalsRes } = useQuery({
    queryKey: ["approvals"],
    queryFn: () => apiClient.getApprovals(),
  });

  const { data: budgetRes } = useQuery({
    queryKey: ["budget"],
    queryFn: () => apiClient.getBudgetOverview(),
  });

  const { data: auditRes } = useQuery({
    queryKey: ["auditLogs"],
    queryFn: () => apiClient.getAuditLogs(),
  });

  const agents = agentsRes?.data || [];
  const approvals = approvalsRes?.data || [];
  const budget = budgetRes?.data;
  const auditLogs = auditRes?.data?.entries || [];

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header Hero Banner */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="default" className="text-[10px] tracking-wider uppercase font-bold">
                Operations Deck
              </Badge>
              <span className="text-xs text-slate-400">Live Telemetry & Multi-Agent Coordination</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              AI Marketing Operations Command
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/content-studio">
              <Button size="sm" className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue gap-2 text-xs">
                <Sparkles className="w-3.5 h-3.5" />
                Generate Campaign
              </Button>
            </Link>
            <Link href="/approvals">
              <Button size="sm" variant="outline" className="gap-2 text-xs">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                Review Approvals ({approvals.filter((a) => a.status === "pending").length})
              </Button>
            </Link>
          </div>
        </div>

        {/* 4 Executive KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="hover:border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Monthly Net Reach
              </CardTitle>
              <Eye className="w-4 h-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">478.2K</div>
              <div className="flex items-center text-xs text-emerald-400 mt-1">
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                +24.8% vs last month
              </div>
            </CardContent>
          </Card>

          <Card className="hover:border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Inbound Qualified Leads
              </CardTitle>
              <Users className="w-4 h-4 text-cyan-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">211</div>
              <div className="flex items-center text-xs text-emerald-400 mt-1">
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                +38 leads this week
              </div>
            </CardContent>
          </Card>

          <Card className="hover:border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Attributed Revenue
              </CardTitle>
              <DollarSign className="w-4 h-4 text-emerald-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">$184,200</div>
              <div className="flex items-center text-xs text-emerald-400 mt-1">
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                4.12x Aggregate ROAS
              </div>
            </CardContent>
          </Card>

          <Card className="hover:border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Agent Success Rate
              </CardTitle>
              <CheckCircle className="w-4 h-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">99.4%</div>
              <div className="text-xs text-slate-400 mt-1">
                Zero governance violations
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Mid-Row: Interactive Performance Chart & Active Agent Radar Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart Section */}
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-base font-bold text-white">
                  Multi-Channel Engagement & Inbound Velocity
                </CardTitle>
                <CardDescription>
                  Daily impressions and inbound inquiry conversions over the trailing 7 days
                </CardDescription>
              </div>
              <Badge variant="cyan" className="text-xs font-mono">
                Live Stream
              </Badge>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="h-[280px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={PERFORMANCE_DATA}>
                    <defs>
                      <linearGradient id="colorImpressions" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorLeads" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="day" stroke="#64748B" fontSize={12} tickLine={false} />
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
                      dataKey="impressions"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorImpressions)"
                      name="Impressions"
                    />
                    <Area
                      type="monotone"
                      dataKey="engagement"
                      stroke="#06B6D4"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorLeads)"
                      name="Engagement"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Quick Agent Status Deck */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                  <Bot className="w-4 h-4 text-blue-400" />
                  Agent Team (8 Total)
                </CardTitle>
                <CardDescription>Real-time autonomous status</CardDescription>
              </div>
              <Link href="/agents">
                <Button variant="ghost" size="sm" className="text-xs text-blue-400 p-0 h-auto">
                  View All
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3 pt-1">
              {agents.slice(0, 5).map((agent) => (
                <Link
                  key={agent.id}
                  href={`/agents/${agent.id.replace("_", "-")}`}
                  className="p-2.5 rounded-lg border border-slate-800/80 bg-navy-950/60 hover:bg-slate-800/40 hover:border-slate-700 transition-all flex items-center justify-between group block"
                >
                  <div className="space-y-0.5">
                    <div className="text-xs font-semibold text-white group-hover:text-blue-400 transition-colors flex items-center gap-1.5">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          agent.status === "active"
                            ? "bg-emerald-400 animate-pulse"
                            : agent.status === "running"
                            ? "bg-cyan-400 animate-ping"
                            : "bg-slate-500"
                        }`}
                      />
                      {agent.name}
                    </div>
                    <p className="text-[11px] text-slate-400 truncate max-w-[200px]">
                      {agent.currentTask || agent.description}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
                </Link>
              ))}

              <Link href="/agents" className="block pt-2">
                <Button variant="outline" size="sm" className="w-full text-xs">
                  Open Agent Command Center ({agents.length} Agents)
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Bottom Split: Pending Approvals & Hash-Chain Audit Snapshot */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pending Approvals */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  Pending Approvals
                </CardTitle>
                <CardDescription>
                  Requires human verification before public dispatch
                </CardDescription>
              </div>
              <Link href="/approvals">
                <Button variant="ghost" size="sm" className="text-xs text-blue-400 p-0 h-auto">
                  Go to Approvals ({approvals.length})
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3 pt-1">
              {approvals.slice(0, 3).map((item) => (
                <div
                  key={item.id}
                  className="p-3.5 rounded-lg border border-slate-800/80 bg-navy-950/60 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <Badge variant="warning" className="text-[10px] uppercase font-bold">
                      {(item.type || "content_draft").replace("_", " ")}
                    </Badge>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {item.submittedAt ? new Date(item.submittedAt).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      }) : "Recent"}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-white">{item.title}</p>
                  <p className="text-[11px] text-slate-400 line-clamp-2 italic">
                    "{item.contentPreview || (item as any).content || ""}"
                  </p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[11px] text-blue-400 font-mono">
                      Agent: {item.agentId}
                    </span>
                    <Link href="/approvals">
                      <Button size="sm" className="h-7 text-xs px-3">
                        Review & Sign
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Budget & Spend Guardrails */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                  Budget & Hard Cap Guardrails
                </CardTitle>
                <CardDescription>
                  Live spending against monthly enterprise cap
                </CardDescription>
              </div>
              <Link href="/budget">
                <Button variant="ghost" size="sm" className="text-xs text-blue-400 p-0 h-auto">
                  Manage Limits
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-4 pt-1">
              {budget && (
                <>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">Current Monthly Spend</span>
                      <span className="font-bold text-white">
                        {formatCurrency(budget.currentSpend)} / {formatCurrency(budget.monthlyBudget)}
                      </span>
                    </div>
                    {/* Progress Bar */}
                    <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full"
                        style={{
                          width: `${
                            budget.monthlyBudget > 0
                              ? Math.min(100, (budget.currentSpend / budget.monthlyBudget) * 100)
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-500">
                      <span>Threshold Alert at {formatCurrency(budget.capAlertThreshold)}</span>
                      <span className="text-emerald-400">Within Safe Limits</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 space-y-2">
                    <div className="text-xs font-semibold text-slate-300">
                      Channel Spending Breakdown:
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {(budget.channelBreakdown || []).map((ch) => (
                        <div
                          key={ch.channel}
                          className="p-2 rounded bg-navy-950/70 border border-slate-800"
                        >
                          <div className="text-slate-400 text-[11px] truncate">
                            {ch.channel}
                          </div>
                          <div className="font-bold text-white mt-0.5">
                            {formatCurrency(ch.spent)}
                          </div>
                          <div className="text-[10px] text-emerald-400">
                            {ch.roas}x ROAS
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}

