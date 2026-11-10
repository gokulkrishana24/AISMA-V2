"use client";

import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Sliders,
  Cpu,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";

export default function BudgetPage() {
  const { data: budgetRes } = useQuery({
    queryKey: ["budget"],
    queryFn: () => apiClient.getBudgetOverview(),
  });

  const budget = budgetRes?.data;

  if (!budget) {
    return (
      <AppLayout>
        <div className="py-12 text-center text-slate-400">Loading Financial Ledger...</div>
      </AppLayout>
    );
  }

  const spendPercent =
    budget.monthlyBudget > 0
      ? Math.round((budget.currentSpend / budget.monthlyBudget) * 100)
      : 0;

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Financial Guardrails
              </Badge>
              <span className="text-xs text-slate-400">
                Automated Spending Limits, Ad Spend Reconciliation & Token Accounting
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Budget Management & Hard Caps
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="success" className="font-mono text-xs">
              Spending Status: Normal ({spendPercent}% Allocated)
            </Badge>
          </div>
        </div>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Hard Monthly Cap
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-white">
                {formatCurrency(budget.monthlyBudget)}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Enforced by backend governance engine
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Current Spend (MTD)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-cyan-400">
                {formatCurrency(budget.currentSpend)}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Remaining: {formatCurrency(budget.monthlyBudget - budget.currentSpend)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Projected End-of-Month
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-emerald-400">
                {formatCurrency(budget.forecastSpend)}
              </div>
              <p className="text-xs text-emerald-400/90 mt-1">
                Within approved safety threshold
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Hard Cap Progress Indicator */}
        <Card className="p-6 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-slate-300">Monthly Spending Velocity</span>
            <span className="text-white font-mono">{spendPercent}% Used</span>
          </div>

          <div className="h-4 w-full bg-slate-800 rounded-full overflow-hidden p-0.5">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-500 shadow-glow-blue"
              style={{ width: `${spendPercent}%` }}
            />
          </div>

          <div className="flex justify-between text-[11px] text-slate-400 pt-1">
            <span>$0.00 Genesis</span>
            <span className="text-amber-400">Threshold Alert: {formatCurrency(budget.capAlertThreshold)}</span>
            <span className="text-rose-400">Hard Cap: {formatCurrency(budget.monthlyBudget)}</span>
          </div>
        </Card>

        {/* 2-Column Split: Channel Allocation & Per-Agent Compute Ledger */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Channel Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white">Channel Ad Budget Allocations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(budget.channelBreakdown || []).map((ch) => (
                <div
                  key={ch.channel}
                  className="p-3 rounded-lg border border-slate-800 bg-navy-950/70 flex items-center justify-between text-xs"
                >
                  <div className="space-y-0.5">
                    <span className="font-semibold text-white">{ch.channel}</span>
                    <span className="text-[11px] text-slate-400 block">
                      Allocated: {formatCurrency(ch.allocated)}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-white block">{formatCurrency(ch.spent)}</span>
                    <span className="text-[10px] text-emerald-400">{ch.roas}x ROAS</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Agent Spend Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white">Agent Inference & Token Ledger</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(budget.agentSpendBreakdown || []).map((agent) => (
                <div
                  key={agent.agentId}
                  className="p-2.5 rounded-lg border border-slate-800 bg-navy-950/70 flex items-center justify-between text-xs"
                >
                  <span className="font-mono text-blue-400">{agent.agentId}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-400 text-[11px]">Token Cost: ${agent.tokenCost}</span>
                    <span className="font-bold text-white">{formatCurrency(agent.spent)}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}

