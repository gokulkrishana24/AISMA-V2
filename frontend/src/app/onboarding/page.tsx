"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import {
  Layers,
  Building,
  Globe,
  DollarSign,
  Share2,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export default function OnboardingPage() {
  const router = useRouter();
  const { switchBusiness } = useAuthStore();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    businessName: "Apex Multi-Channel Enterprise",
    domain: "apexmarketing.ai",
    channels: ["linkedin", "twitter", "instagram"],
    monthlyBudget: "25000",
    toneArchetype: "Strategic Architect",
  });

  const toggleChannel = (channel: string) => {
    setFormData((prev) => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter((c) => c !== channel)
        : [...prev.channels, channel],
    }));
  };

  const handleFinish = () => {
    switchBusiness("biz_apex_enterprises", formData.businessName);
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen bg-navy-950 flex flex-col justify-center items-center px-4 relative overflow-hidden py-12">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-blue-600/10 blur-[150px] pointer-events-none rounded-full" />

      <div className="w-full max-w-xl relative z-10 space-y-8">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-cyan-400 shadow-glow-blue mb-2">
            <Layers className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Tenant Initialization Wizard
          </h1>
          <p className="text-sm text-slate-400">
            Configure enterprise Brand OS and governance boundaries for your 8 agents
          </p>

          <div className="flex items-center justify-center gap-2 pt-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  s === step
                    ? "w-8 bg-blue-500 shadow-glow-blue"
                    : s < step
                    ? "w-8 bg-emerald-500"
                    : "w-4 bg-slate-800"
                }`}
              />
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-navy-900/85 backdrop-blur-xl p-8 shadow-glass space-y-6">
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Building className="w-4 h-4 text-blue-400" />
                Step 1: Business Identity & Web Presence
              </h2>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-slate-300">
                  Legal Business / Brand Name
                </label>
                <Input
                  value={formData.businessName}
                  onChange={(e) =>
                    setFormData({ ...formData, businessName: e.target.value })
                  }
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-slate-300 flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-blue-400" />
                  Primary Domain (for SEO Sentinel)
                </label>
                <Input
                  value={formData.domain}
                  onChange={(e) =>
                    setFormData({ ...formData, domain: e.target.value })
                  }
                />
              </div>

              <div className="pt-4 flex justify-end">
                <Button onClick={() => setStep(2)}>
                  Next: Social Channels & Voice <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Share2 className="w-4 h-4 text-blue-400" />
                Step 2: Social Channels & Tone Archetype
              </h2>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-300 block mb-2">
                  Target Social Channels
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {[
                    { id: "linkedin", name: "LinkedIn" },
                    { id: "twitter", name: "Twitter / X" },
                    { id: "instagram", name: "Instagram" },
                    { id: "facebook", name: "Facebook" },
                    { id: "tiktok", name: "TikTok" },
                    { id: "youtube", name: "YouTube" },
                  ].map((ch) => {
                    const isSelected = formData.channels.includes(ch.id);
                    return (
                      <button
                        key={ch.id}
                        type="button"
                        onClick={() => toggleChannel(ch.id)}
                        className={`p-3 rounded-lg border text-xs font-medium text-left transition-all ${
                          isSelected
                            ? "border-blue-500 bg-blue-600/20 text-blue-300 shadow-glow-blue"
                            : "border-slate-800 bg-navy-950/60 text-slate-400 hover:border-slate-700"
                        }`}
                      >
                        {isSelected && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 mb-1" />
                        )}
                        {ch.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-1.5 pt-2">
                <label className="text-xs font-semibold uppercase text-slate-300">
                  Brand Voice Archetype
                </label>
                <select
                  value={formData.toneArchetype}
                  onChange={(e) =>
                    setFormData({ ...formData, toneArchetype: e.target.value })
                  }
                  className="w-full h-10 rounded-lg border border-slate-700/80 bg-navy-900 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Strategic Architect">The Strategic Architect (Analytical, Authoritative)</option>
                  <option value="Visionary Disruptor">The Visionary Disruptor (Bold, Forward-Thinking)</option>
                  <option value="Trusted Partner">The Trusted Partner (Empathetic, Rigorous)</option>
                  <option value="Technical Leader">The Technical Leader (Data-Driven, Deep Dive)</option>
                </select>
              </div>

              <div className="pt-4 flex justify-between">
                <Button variant="outline" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button onClick={() => setStep(3)}>
                  Next: Budget & Governance <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                Step 3: Financial Guardrails & Verification
              </h2>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-slate-300">
                  Monthly Hard Spending Cap ($ USD)
                </label>
                <Input
                  type="number"
                  value={formData.monthlyBudget}
                  onChange={(e) =>
                    setFormData({ ...formData, monthlyBudget: e.target.value })
                  }
                />
                <p className="text-[11px] text-slate-400">
                  Agents are automatically blocked from ad-spend or high-token inference if spend approaches 95% of cap.
                </p>
              </div>

              <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-300 space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Genesis Audit Block Ready
                </div>
                <p className="text-emerald-400/80 text-[11px]">
                  All 8 agents will be initialized with strict fail-closed governance, default-deny publishing permissions, and SHA-256 hash chaining.
                </p>
              </div>

              <div className="pt-4 flex justify-between">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button
                  onClick={handleFinish}
                  className="bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 shadow-glow-blue"
                >
                  Complete Onboarding & Enter Command Deck
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

