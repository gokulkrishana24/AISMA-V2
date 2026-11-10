"use client";

import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  Radar,
  AlertTriangle,
  Globe,
  Share2,
  TrendingUp,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

export default function CompetitorIntelligencePage() {
  const { data: competitorsRes } = useQuery({
    queryKey: ["competitors"],
    queryFn: () => apiClient.getCompetitorIntelligence(),
  });

  const competitors = competitorsRes?.data || [];

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Market Radar Sentinel
              </Badge>
              <span className="text-xs text-slate-400">
                Competitor Telemetry, Promotion Detection & Strategic Gap Analysis
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Competitor Intelligence & Alerts
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="cyan" className="gap-1.5 text-xs font-mono">
              <Radar className="w-3.5 h-3.5 animate-spin" />
              Scanning 8 Rival Entities 24/7
            </Badge>
          </div>
        </div>

        {/* Promotion Alerts Banner */}
        <div className="p-4 rounded-2xl border border-amber-500/40 bg-amber-950/20 shadow-glass flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 mt-0.5">
              <AlertTriangle className="w-5 h-5 animate-pulse" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-sm">
                  Active Competitor Threat Detected: GrowthPulse AI
                </span>
                <Badge variant="destructive" className="text-[9px] uppercase font-bold">
                  High Urgency
                </Badge>
              </div>
              <p className="text-xs text-slate-300">
                Competitor launched "Q4 Flash Promo: 30% Off Annual Enterprise" on LinkedIn & X to capture mid-market B2B software prospects.
              </p>
            </div>
          </div>

          <Link href="/content-studio">
            <Button size="sm" className="bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs h-9 shrink-0">
              <Zap className="w-3.5 h-3.5 mr-1" />
              Draft Counter-Campaign
            </Button>
          </Link>
        </div>

        {/* Competitor Profiles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {competitors.map((comp) => (
            <Card key={comp.id} className="p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">{comp.name}</h3>
                  <a
                    href={comp.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-blue-400 hover:underline flex items-center gap-1 mt-0.5"
                  >
                    <Globe className="w-3 h-3" />
                    {comp.website}
                  </a>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">
                    Share of Voice
                  </span>
                  <span className="text-sm font-bold text-cyan-400 font-mono">
                    {comp.shareOfVoice}%
                  </span>
                </div>
              </div>

              {/* Recent Promotion Box */}
              <div className="p-3.5 rounded-xl border border-slate-800 bg-navy-950/70 text-xs space-y-1.5">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="font-semibold text-slate-300">Detected Promotion:</span>
                  <span className="text-[10px] font-mono">
                    {new Date(comp.recentPromotion.detectedAt).toLocaleDateString()}
                  </span>
                </div>
                <div className="font-bold text-amber-300 text-xs">
                  {comp.recentPromotion.title}
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  {comp.recentPromotion.description}
                </p>
              </div>

              {/* Differentiators */}
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase block mb-1.5">
                  Strategic Positioning Differentiators:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {comp.keyDifferentiators.map((diff) => (
                    <Badge key={diff} variant="secondary" className="text-[11px]">
                      {diff}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Tracked Channels */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span>Tracked Channels:</span>
                <div className="flex items-center gap-2 capitalize text-white font-medium">
                  {comp.trackedChannels.join(", ")}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
