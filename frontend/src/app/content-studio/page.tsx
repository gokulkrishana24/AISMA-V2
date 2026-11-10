"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ContentDraft, ContentHookOption, SocialChannel } from "@/types";
import {
  FileEdit,
  Sparkles,
  Share2,
  CheckCircle2,
  AlertCircle,
  Hash,
  Send,
  Save,
  Clock,
  Search,
  Eye,
  Check,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const CHANNELS: Array<{ id: SocialChannel; name: string; maxChars: number }> = [
  { id: "linkedin", name: "LinkedIn", maxChars: 3000 },
  { id: "twitter", name: "Twitter / X", maxChars: 280 },
  { id: "instagram", name: "Instagram", maxChars: 2200 },
  { id: "facebook", name: "Facebook", maxChars: 5000 },
  { id: "tiktok", name: "TikTok", maxChars: 2200 },
  { id: "youtube", name: "YouTube", maxChars: 5000 },
];

export default function ContentStudioPage() {
  const queryClient = useQueryClient();

  // Form State
  const [topic, setTopic] = useState("Why AI Governance Outperforms Raw Speed in Enterprise Marketing");
  const [channel, setChannel] = useState<SocialChannel>("linkedin");
  const [bodyContent, setBodyContent] = useState(
    `When autonomous marketing agents run 24/7 across multiple channels, "trust me" isn't an enterprise strategy.\n\nHere is what real governance requires:\n1. Every prompt and generated output must be hash-chained via SHA-256.\n2. PII must be scrubbed automatically before logging.\n3. Fail-closed kill switches must halt runaway agents instantly.\n\nAutonomous speed without verifiable governance is just liability at scale.`
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedHookId, setSelectedHookId] = useState("hook_1");

  const [hooks, setHooks] = useState<ContentHookOption[]>([
    {
      id: "hook_1",
      text: "Autonomous speed without verifiable governance is just liability at scale.",
      angle: "contrarian",
      score: 96,
    },
    {
      id: "hook_2",
      text: "How our multi-agent team generated 400+ qualified leads with zero human publishing errors.",
      angle: "data_driven",
      score: 91,
    },
    {
      id: "hook_3",
      text: "The exact reason 90% of AI marketing deployments fail in enterprise compliance audits.",
      angle: "curiosity",
      score: 88,
    },
  ]);

  const { data: draftsRes } = useQuery({
    queryKey: ["drafts"],
    queryFn: () => apiClient.getDrafts(),
  });

  const drafts = draftsRes?.data || [];
  const currentChannelConfig = CHANNELS.find((c) => c.id === channel) || CHANNELS[0];
  const charCount = bodyContent.length;
  const isOverLimit = charCount > currentChannelConfig.maxChars;

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setHooks([
        {
          id: `hook_${Date.now()}_1`,
          text: `Stop chasing vanity metrics with generic bots. Specialization is the only moat in 2027.`,
          angle: "contrarian",
          score: 95,
        },
        {
          id: `hook_${Date.now()}_2`,
          text: `We analyzed 10,000 automated marketing posts. Here is why hash-chain governance drove 4.1x higher trust.`,
          angle: "data_driven",
          score: 93,
        },
        {
          id: `hook_${Date.now()}_3`,
          text: `Are your autonomous social agents leaking customer PII? Here is how to test it in 60 seconds.`,
          angle: "curiosity",
          score: 89,
        },
      ]);
      setIsGenerating(false);
    }, 800);
  };

  const handleSaveDraft = async () => {
    await apiClient.createDraft({
      title: topic,
      channel,
      content: bodyContent,
      characterCount: charCount,
      maxCharacterCount: currentChannelConfig.maxChars,
      hookOptions: hooks,
      selectedHookId,
      status: "draft",
    });
    queryClient.invalidateQueries({ queryKey: ["drafts"] });
    alert("Draft saved successfully to workspace repository!");
  };

  const handleSubmitForApproval = async () => {
    await apiClient.createDraft({
      title: topic,
      channel,
      content: bodyContent,
      characterCount: charCount,
      maxCharacterCount: currentChannelConfig.maxChars,
      hookOptions: hooks,
      selectedHookId,
      status: "pending_approval",
    });
    queryClient.invalidateQueries({ queryKey: ["drafts"] });
    alert("Draft submitted to Approval Center for human verification!");
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Content Engine
              </Badge>
              <span className="text-xs text-slate-400">
                Multi-Channel AI Copywriting & Brand Voice Alignment
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Content Studio
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveDraft}
              className="gap-1.5 text-xs border-slate-700"
            >
              <Save className="w-3.5 h-3.5 text-blue-400" />
              Save Draft
            </Button>
            <Button
              size="sm"
              onClick={handleSubmitForApproval}
              className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue gap-1.5 text-xs font-semibold"
            >
              <Send className="w-3.5 h-3.5" />
              Submit to Approvals
            </Button>
          </div>
        </div>

        {/* 2-Column Studio Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Generation Controls & Content Editor */}
          <div className="lg:col-span-7 space-y-6">
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-base text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-blue-400" />
                  Generation Parameters
                </CardTitle>
                <CardDescription>
                  Direct the Content Engine agent with topic, angle, and channel
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Topic / Prompt */}
                <div>
                  <label className="text-xs font-semibold uppercase text-slate-300 block mb-1.5">
                    Core Campaign Topic / Theme
                  </label>
                  <Input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Enter campaign subject or angle..."
                  />
                </div>

                {/* Channel Selector */}
                <div>
                  <label className="text-xs font-semibold uppercase text-slate-300 block mb-2">
                    Target Publishing Channel
                  </label>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                    {CHANNELS.map((ch) => (
                      <button
                        key={ch.id}
                        type="button"
                        onClick={() => setChannel(ch.id)}
                        className={`p-2 rounded-lg border text-xs font-semibold transition-all ${
                          channel === ch.id
                            ? "border-blue-500 bg-blue-600/20 text-blue-300 shadow-glow-blue"
                            : "border-slate-800 bg-navy-950/60 text-slate-400 hover:border-slate-700"
                        }`}
                      >
                        {ch.name}
                      </button>
                    ))}
                  </div>
                </div>

                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="w-full bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-xs h-9"
                >
                  <Zap className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
                  {isGenerating ? "Synthesizing Copy..." : "Generate AI Hook Variations"}
                </Button>
              </CardContent>
            </Card>

            {/* Hook Selector (3 Options) */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base text-white">
                    Three Strategic Hook Options
                  </CardTitle>
                  <span className="text-xs text-slate-400">Select preferred angle</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {hooks.map((hk) => {
                  const isSelected = selectedHookId === hk.id;
                  return (
                    <div
                      key={hk.id}
                      onClick={() => {
                        setSelectedHookId(hk.id);
                        setBodyContent(`${hk.text}\n\n${bodyContent}`);
                      }}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? "border-blue-500 bg-blue-600/15 shadow-glow-blue"
                          : "border-slate-800 bg-navy-950/70 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <Badge
                          variant={hk.angle === "contrarian" ? "destructive" : "cyan"}
                          className="text-[10px] uppercase font-bold"
                        >
                          {hk.angle.replace("_", " ")}
                        </Badge>
                        <span className="text-[11px] font-mono text-emerald-400 font-semibold">
                          {hk.score}% Hook Score
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 font-medium leading-relaxed">
                        "{hk.text}"
                      </p>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Copy Body Editor */}
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base text-white">
                    Generated Copy Editor
                  </CardTitle>
                  <div
                    className={`text-xs font-mono font-semibold ${
                      isOverLimit ? "text-rose-400" : "text-slate-400"
                    }`}
                  >
                    {charCount} / {currentChannelConfig.maxChars} chars
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={bodyContent}
                  onChange={(e) => setBodyContent(e.target.value)}
                  className="min-h-[220px] font-sans text-sm leading-relaxed"
                />
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Live Mockup, Brand Voice Validation & SEO */}
          <div className="lg:col-span-5 space-y-6">
            {/* Live Social Preview */}
            <Card className="border-blue-500/30">
              <CardHeader className="pb-3 border-b border-slate-800">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Eye className="w-3.5 h-3.5 text-blue-400" />
                    {currentChannelConfig.name} Feed Simulation
                  </div>
                  <Badge variant="cyan" className="text-[10px] font-mono">
                    Preview
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white text-xs">
                    AM
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white">Apex Marketing</div>
                    <div className="text-[11px] text-slate-400">Autonomous Enterprise • Just now</div>
                  </div>
                </div>

                <div className="text-xs text-slate-200 whitespace-pre-line leading-relaxed font-sans">
                  {bodyContent}
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>👍 84</span>
                  <span>💬 19 Comments</span>
                  <span>🔁 12 Reposts</span>
                </div>
              </CardContent>
            </Card>

            {/* Brand Voice Validation Card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-white flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Brand Voice Compliance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Alignment Score:</span>
                  <span className="text-sm font-bold text-emerald-400 font-mono">98% Match</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full w-[98%]" />
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {["Authoritative", "Enterprise-Ready", "Technically Rigorous"].map((t) => (
                    <Badge key={t} variant="secondary" className="text-[10px]">
                      {t}
                    </Badge>
                  ))}
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed pt-1">
                  Zero forbidden fluff detected. Claims match verified proof points in Brand OS.
                </p>
              </CardContent>
            </Card>

            {/* SEO & Discovery Recommendations */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-white flex items-center gap-2">
                  <Hash className="w-4 h-4 text-blue-400" />
                  SEO & Discovery Signals
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-[11px] text-slate-400 mb-1.5">Recommended Keywords:</div>
                  <div className="flex flex-wrap gap-1">
                    {["ai governance", "hash-chain audit", "autonomous marketing"].map((k) => (
                      <span
                        key={k}
                        className="px-2 py-0.5 rounded bg-blue-950/80 border border-blue-500/30 text-blue-300 text-[10px] font-mono"
                      >
                        {k}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] text-slate-400 mb-1.5">Algorithmic Reach Potential:</div>
                  <div className="text-sm font-bold text-white">Estimated 45,000+ Impressions</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

