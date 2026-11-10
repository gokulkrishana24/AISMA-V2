"use client";

import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  Search,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  BarChart2,
  Sparkles,
  ExternalLink,
  Target,
  Globe,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatNumber } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function SEOIntelligencePage() {
  const { data: seoRes, isLoading } = useQuery({
    queryKey: ["seo"],
    queryFn: () => apiClient.getSEOIntelligence(),
  });

  const keywords = seoRes?.data?.keywords || [];
  const visibilityScore = seoRes?.data?.visibilityScore || 84.6;

  const CHART_DATA = keywords.map((k) => ({
    name: k.keyword.split(" ").slice(0, 2).join(" "),
    volume: k.searchVolume,
    visibility: k.visibilityScore,
  }));

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Search Visibility Sentinel
              </Badge>
              <span className="text-xs text-slate-400">
                SERP Matrix, Keyword Demand & Organic Discovery
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              SEO Intelligence & Demand Radar
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="success" className="font-mono text-xs">
              Visibility Index: {visibilityScore} / 100
            </Badge>
          </div>
        </div>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Aggregate Visibility Index
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">{visibilityScore}%</div>
              <div className="flex items-center text-xs text-emerald-400 mt-1">
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                +6.2% net organic gain this month
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Target Keywords in Top 3
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-cyan-400">42 Terms</div>
              <p className="text-xs text-slate-400 mt-1">
                8 terms took #1 position on Google & Bing
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Tracked Monthly Search Demand
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-400">44,000+</div>
              <p className="text-xs text-slate-400 mt-1">
                Commercial and transactional intent queries
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Search Demand Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-white">Search Volume by Keyword Cluster</CardTitle>
            <CardDescription>Monthly estimated search impressions across Google Search</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[240px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={CHART_DATA}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="name" stroke="#64748B" fontSize={12} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0F172A",
                      borderColor: "#334155",
                      borderRadius: "8px",
                      color: "#F8FAFC",
                    }}
                  />
                  <Bar dataKey="volume" fill="#3B82F6" radius={[4, 4, 0, 0]} name="Search Volume" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Keyword Ranking Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-white">Core Keyword Positioning Matrix</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-navy-950/70 text-slate-400 font-semibold uppercase tracking-wider">
                    <th className="p-3 pl-6">Keyword Phrase</th>
                    <th className="p-3">Current Rank</th>
                    <th className="p-3">Previous</th>
                    <th className="p-3">Search Demand</th>
                    <th className="p-3">Volume</th>
                    <th className="p-3">Difficulty</th>
                    <th className="p-3 pr-6">Trend</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {keywords.map((kw) => (
                    <tr key={kw.keyword} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-3 pl-6 font-semibold text-white">{kw.keyword}</td>
                      <td className="p-3">
                        <span className="font-mono font-bold text-emerald-400">#{kw.currentRank}</span>
                      </td>
                      <td className="p-3 font-mono text-slate-400">#{kw.previousRank}</td>
                      <td className="p-3">
                        <Badge variant="cyan" className="text-[10px] uppercase font-bold">
                          {kw.searchDemand.replace("_", " ")}
                        </Badge>
                      </td>
                      <td className="p-3 font-mono text-slate-200">{formatNumber(kw.searchVolume)}</td>
                      <td className="p-3 font-mono text-slate-400">{kw.difficulty}/100</td>
                      <td className="p-3 pr-6">
                        {kw.trend === "up" ? (
                          <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                            <ArrowUpRight className="w-3.5 h-3.5" /> Gaining
                          </span>
                        ) : (
                          <span className="text-slate-400">Stable</span>
                        )}
                      </td>
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

