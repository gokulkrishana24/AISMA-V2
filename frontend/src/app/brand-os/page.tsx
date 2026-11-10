"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  BookOpen,
  CheckCircle2,
  XCircle,
  Shield,
  Layers,
  Sparkles,
  Users,
  Target,
  FileCheck,
  Save,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function BrandOSPage() {
  const [activeTab, setActiveTab] = useState<"identity" | "voice" | "messaging" | "proofs" | "audience">("identity");

  const { data: brandRes, isLoading } = useQuery({
    queryKey: ["brandOS"],
    queryFn: () => apiClient.getBrandOS(),
  });

  const brand = brandRes?.data;

  if (!brand) {
    return (
      <AppLayout>
        <div className="py-12 text-center text-slate-400">Loading Brand OS Knowledge Vault...</div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Governance Ground Truth
              </Badge>
              <span className="text-xs text-slate-400">
                Single Source of Truth (SSOT) Ingested by All 8 Agents
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Brand Operating System (Brand OS)
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="success" className="gap-1.5 text-xs font-mono">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Verified & Locked
            </Badge>
          </div>
        </div>

        {/* Tab Buttons */}
        <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium overflow-x-auto">
          {[
            { id: "identity", label: "Identity & Positioning" },
            { id: "voice", label: "Brand Voice & Guidelines" },
            { id: "messaging", label: "Messaging Bank" },
            { id: "proofs", label: "Approved Proof Points" },
            { id: "audience", label: "Target Personas" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "border-b-2 border-blue-500 text-white font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 1: Identity & Positioning */}
        {activeTab === "identity" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base text-white">Brand Identity Core</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div>
                  <span className="text-slate-400 block uppercase font-bold text-[10px]">Brand Name</span>
                  <span className="text-lg font-bold text-white">{brand.identity.brandName}</span>
                </div>
                <div>
                  <span className="text-slate-400 block uppercase font-bold text-[10px]">Tagline</span>
                  <span className="text-sm font-semibold text-blue-300">"{brand.identity.tagline}"</span>
                </div>
                <div>
                  <span className="text-slate-400 block uppercase font-bold text-[10px]">Mission Statement</span>
                  <p className="text-slate-300 leading-relaxed mt-0.5">{brand.identity.mission}</p>
                </div>
                <div>
                  <span className="text-slate-400 block uppercase font-bold text-[10px] mb-1.5">Core Values</span>
                  <div className="flex flex-wrap gap-1.5">
                    {brand.identity.coreValues.map((v) => (
                      <Badge key={v} variant="secondary" className="text-xs">
                        {v}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base text-white">Positioning & Promise</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div>
                  <span className="text-slate-400 block uppercase font-bold text-[10px]">Category Definition</span>
                  <span className="text-sm font-semibold text-white">{brand.positioning.category}</span>
                </div>
                <div>
                  <span className="text-slate-400 block uppercase font-bold text-[10px]">Target Segment</span>
                  <span className="text-sm text-cyan-300">{brand.positioning.targetSegment}</span>
                </div>
                <div>
                  <span className="text-slate-400 block uppercase font-bold text-[10px]">Primary Brand Promise</span>
                  <p className="text-slate-300 leading-relaxed mt-0.5 font-medium">{brand.positioning.primaryPromise}</p>
                </div>
                <div>
                  <span className="text-slate-400 block uppercase font-bold text-[10px] mb-1">Reasons to Believe</span>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    {brand.positioning.reasonsToBelieve.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab 2: Brand Voice */}
        {activeTab === "voice" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base text-white">Brand Voice Archetype: {brand.voice.archetype}</CardTitle>
                  <Badge variant="cyan" className="text-xs font-mono">
                    {brand.voice.readingLevel}
                  </Badge>
                </div>
                <CardDescription>
                  Enforced during real-time copy validation in Content Engine
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-2">Tone Descriptors:</span>
                  <div className="flex flex-wrap gap-2">
                    {brand.voice.toneKeywords.map((kw) => (
                      <span
                        key={kw}
                        className="px-3 py-1 rounded-lg bg-blue-950/80 border border-blue-500/40 text-blue-300 text-xs font-medium"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2 text-xs">
                    <div className="font-bold text-emerald-300 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      Strict DOs
                    </div>
                    <ul className="space-y-1.5 text-slate-300">
                      {brand.voice.dos.map((d, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-emerald-400 font-bold">•</span>
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 space-y-2 text-xs">
                    <div className="font-bold text-rose-300 flex items-center gap-1.5">
                      <XCircle className="w-4 h-4 text-rose-400" />
                      Strict DONTs (Violations Trigger Approval Block)
                    </div>
                    <ul className="space-y-1.5 text-slate-300">
                      {brand.voice.donts.map((d, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-rose-400 font-bold">•</span>
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab 3: Messaging Bank */}
        {activeTab === "messaging" && (
          <div className="space-y-4">
            {brand.messagingBank.map((pillar) => (
              <Card key={pillar.pillar} className="p-6 space-y-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-blue-400" />
                  Pillar: {pillar.pillar}
                </h3>
                <div className="space-y-2 text-xs">
                  <span className="font-semibold text-slate-400 block">Approved Key Phrases:</span>
                  <div className="space-y-1.5">
                    {pillar.approvedPhrases.map((phrase, i) => (
                      <div
                        key={i}
                        className="p-2.5 rounded-lg bg-navy-950 border border-slate-800 text-slate-200 italic"
                      >
                        "{phrase}"
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Tab 4: Proof Points */}
        {activeTab === "proofs" && (
          <div className="space-y-4">
            <div className="text-xs text-slate-400">
              Only verified claims in this repository can be cited by agents without human escalation.
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {brand.approvedProofPoints.map((pp, i) => (
                <Card key={i} className="p-5 space-y-2 border-emerald-500/30">
                  <div className="flex items-center justify-between">
                    <Badge variant="success" className="text-[10px] gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Verified Truth
                    </Badge>
                  </div>
                  <p className="text-xs font-semibold text-white leading-relaxed">
                    "{pp.claim}"
                  </p>
                  <p className="text-[11px] text-slate-400 font-mono">
                    Citation: {pp.citation}
                  </p>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Tab 5: Audience Personas */}
        {activeTab === "audience" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {brand.audience.map((aud, i) => (
              <Card key={i} className="p-6 space-y-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center font-bold text-blue-300">
                    <Users className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">{aud.persona}</h3>
                    <p className="text-xs text-slate-400">{aud.title}</p>
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <span className="font-semibold text-rose-400 uppercase text-[10px] block">
                    Core Pain Points:
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    {aud.painPoints.map((p, idx) => (
                      <li key={idx}>{p}</li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-2 text-xs pt-2 border-t border-slate-800">
                  <span className="font-semibold text-emerald-400 uppercase text-[10px] block">
                    Key Aspirations:
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    {aud.keyAspirations.map((a, idx) => (
                      <li key={idx}>{a}</li>
                    ))}
                  </ul>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}

