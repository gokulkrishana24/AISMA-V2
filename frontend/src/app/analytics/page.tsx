"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  ArrowUpRight,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function AnalyticsROIPage() {
  const [period, setPeriod] = useState("Last 30 Days");

  const { data: roiRes, isLoading, refetch } = useQuery({
    queryKey: ["roiReport", period],
    queryFn: () => apiClient.getROIReport(period),
  });

  const roi = roiRes?.data;
  const channels = roi?.channels || [];
  const totalConversions = channels.reduce((acc, c) => acc + c.conversions, 0);

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Deterministic Python ROI Engine
              </Badge>
              <span className="text-xs text-slate-400">
                Verified Unit Economics & Channel Attribution (Zero LLM Estimation)
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Analytics & Return on Investment (ROI)
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              aria-label="Select reporting period"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="rounded-lg border border-slate-700 bg-navy-900 px-3 py-1.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Last 30 Days">Last 30 Days</option>
              <option value="Last 90 Days">Last 90 Days</option>
              <option value="Q4 Quarter">Q4 Quarter</option>
            </select>

            <Button size="sm" variant="outline" onClick={() => refetch()} className="text-xs gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" />
              Recalculate
            </Button>

            <Badge variant="success" className="font-mono text-xs">
              Blended ROAS: {roi ? `${roi.blended_roas}x` : "—"}
            </Badge>
          </div>
        </div>

        {/* 4 Deterministic Financial KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Total Attributed Revenue
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {isLoading ? "Loading..." : formatCurrency(roi?.total_attributed_revenue ?? 0)}
              </div>
              <div className="flex items-center text-xs text-emerald-400 mt-1">
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                Total Spend: {formatCurrency(roi?.total_spend ?? 0)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Customer Acquisition Cost (CAC)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-cyan-400">
                {isLoading ? "Loading..." : formatCurrency(roi?.customer_acquisition_cost ?? 0)}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                LTV:CAC Ratio: {roi?.ltv_to_cac_ratio ?? 0}x
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Net Marketing ROI %
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-emerald-400">
                {isLoading ? "Loading..." : `${roi?.marketing_roi_percentage ?? 0}%`}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Net Profit: {formatCurrency(roi?.net_marketing_profit ?? 0)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Attributed Conversions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-400">
                {isLoading ? "Loading..." : totalConversions}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                CLTV Baseline: {formatCurrency(roi?.customer_lifetime_value ?? 0)}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Attribution Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-white">Attributed Revenue by Channel</CardTitle>
            <CardDescription>
              Multi-touch channel metrics computed by DeterministicROIEngine ({period})
            </CardDescription>
          </CardHeader>
          <CardContent>
            {channels.length === 0 ? (
              <div className="h-[240px] flex items-center justify-center text-sm text-slate-400">
                {isLoading ? "Computing deterministic attribution..." : "No channel attribution rows available."}
              </div>
            ) : (
              <div className="h-[280px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={channels}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="channel" stroke="#64748B" fontSize={12} tickLine={false} />
                    <YAxis stroke="#64748B" fontSize={12} tickLine={false} />
                    <Tooltip
                      formatter={(val: number) => formatCurrency(val)}
                      contentStyle={{
                        backgroundColor: "#0F172A",
                        borderColor: "#334155",
                        borderRadius: "8px",
                        color: "#F8FAFC",
                      }}
                    />
                    <Bar dataKey="attributed_revenue" fill="#3B82F6" radius={[4, 4, 0, 0]} name="Attributed Revenue" />
                    <Bar dataKey="spend" fill="#06B6D4" radius={[4, 4, 0, 0]} name="Channel Spend" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Channel Breakdown Table & Audit Hash */}
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <CardTitle className="text-base text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Deterministic Calculation Audit Ledger
                </CardTitle>
                <CardDescription>
                  Every financial figure is verified via SHA-256 checksum
                </CardDescription>
              </div>
              {roi?.deterministic_audit_hash && (
                <Badge variant="outline" className="font-mono text-[10px] text-cyan-300 border-cyan-500/30">
                  SHA-256: {roi.deterministic_audit_hash.slice(0, 16)}...
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-slate-400 uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-2 pr-4">Channel</th>
                    <th className="py-2 px-4">Spend</th>
                    <th className="py-2 px-4">Attributed Revenue</th>
                    <th className="py-2 px-4">Conversions</th>
                    <th className="py-2 px-4">ROAS</th>
                    <th className="py-2 pl-4">CPA</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {channels.map((ch) => (
                    <tr key={ch.channel} className="text-slate-200">
                      <td className="py-2.5 pr-4 font-semibold text-white">{ch.channel}</td>
                      <td className="py-2.5 px-4">{formatCurrency(ch.spend)}</td>
                      <td className="py-2.5 px-4 text-emerald-400 font-semibold">{formatCurrency(ch.attributed_revenue)}</td>
                      <td className="py-2.5 px-4">{ch.conversions}</td>
                      <td className="py-2.5 px-4 font-mono">{ch.roas}x</td>
                      <td className="py-2.5 pl-4 font-mono">{formatCurrency(ch.cpa)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
