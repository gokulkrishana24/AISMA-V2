"use client";

import { useState, useEffect } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useAuthStore } from "@/stores/auth-store";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  Building,
  Users,
  Cpu,
  Plug,
  Bell,
  CheckCircle2,
  Save,
  Database,
  Download,
  RotateCcw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"business" | "models" | "users" | "integrations" | "beta">("business");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data: hwRes } = useQuery({
    queryKey: ["hardwareTelemetry"],
    queryFn: () => apiClient.getHardwareTelemetry(),
  });

  const { data: cfgRes } = useQuery({
    queryKey: ["localAIConfig"],
    queryFn: () => apiClient.getLocalAIConfig(),
  });

  const { data: integRes } = useQuery({
    queryKey: ["integrations"],
    queryFn: () => apiClient.getIntegrations(),
  });

  const { data: subRes } = useQuery({
    queryKey: ["billingSubscription", user?.businessId],
    queryFn: () => apiClient.getSubscriptionStatus(),
  });

  const hw = hwRes?.data;
  const aiCfg = cfgRes?.data;
  const integrations = integRes?.data || [];
  const subscription = subRes?.data;

  const [businessSettings, setBusinessSettings] = useState({
    businessName: user?.businessName || "Apex Multi-Channel Enterprise",
    businessId: user?.businessId || "biz_apex_enterprises",
    timezone: "UTC (Coordinated Universal Time)",
  });

  const [localModelSettings, setLocalModelSettings] = useState({
    primaryModel: "phi3.5:latest",
    fallbackModel: "qwen3.5:4b",
    contextLength: 4096,
    temperature: 0.2,
  });

  useEffect(() => {
    if (aiCfg) {
      setLocalModelSettings({
        primaryModel: aiCfg.default_model || "phi3.5:latest",
        fallbackModel: aiCfg.fallback_model || "qwen3.5:4b",
        contextLength: aiCfg.context_length || 4096,
        temperature: aiCfg.temperature ?? 0.2,
      });
    }
  }, [aiCfg]);

  const handleSave = async () => {
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      await apiClient.updateLocalAIConfig({
        default_model: localModelSettings.primaryModel,
        fallback_model: localModelSettings.fallbackModel,
        context_length: Number(localModelSettings.contextLength),
        temperature: Number(localModelSettings.temperature),
      });
      queryClient.invalidateQueries({ queryKey: ["localAIConfig"] });
      setStatusMessage("Configuration synchronized cleanly with local backend.");
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to save settings to backend.");
    }
  };

  const handleSeedDemo = async () => {
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const res = await apiClient.seedDemoWorkspace();
      queryClient.invalidateQueries();
      setStatusMessage(`Synthetic Demo seeded: ${res.data.business_name} (${res.data.business_id})`);
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to seed demo workspace.");
    }
  };

  const handleResetDemo = async () => {
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      await apiClient.resetDemoWorkspace();
      queryClient.invalidateQueries();
      setStatusMessage("Synthetic Demo workspace reset cleanly. Real user records preserved.");
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to reset demo workspace.");
    }
  };

  const handlePrivacyExport = async () => {
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const res = await apiClient.exportTenantData();
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `aisma_export_${user?.businessId || "tenant"}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setStatusMessage("GDPR / CCPA JSON data portability export generated.");
    } catch (err: any) {
      setErrorMessage(err?.message || "Data export failed.");
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Platform Administration
              </Badge>
              <span className="text-xs text-slate-400">
                Multi-Tenant Configuration, Local AI Runners, Billing Quotas & Beta Controls
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              System Settings
            </h1>
          </div>

          <Button
            size="sm"
            onClick={handleSave}
            className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue gap-1.5 text-xs font-semibold"
          >
            <Save className="w-3.5 h-3.5" />
            Save AI Configuration
          </Button>
        </div>

        {statusMessage && (
          <div className="p-3 rounded-lg border border-emerald-500/40 bg-emerald-950/30 text-xs text-emerald-300">
            {statusMessage}
          </div>
        )}
        {errorMessage && (
          <div className="p-3 rounded-lg border border-rose-500/40 bg-rose-950/30 text-xs text-rose-300">
            {errorMessage}
          </div>
        )}

        {/* Tab Buttons */}
        <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium overflow-x-auto">
          {[
            { id: "business", label: "Business & Plan", icon: Building },
            { id: "models", label: "Local AI Models", icon: Cpu },
            { id: "users", label: "Roles & Privacy", icon: Users },
            { id: "integrations", label: "Channel Integrations", icon: Plug },
            { id: "beta", label: "Local Beta & Demo Data", icon: Bell },
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

        {/* Tab 1: Business Details & Subscription */}
        {activeTab === "business" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white">Tenant Profile & Usage Plan</CardTitle>
              <CardDescription>Live organization metadata and subscription quota overview</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 max-w-xl">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-slate-300">Organization Name</label>
                <Input
                  value={businessSettings.businessName}
                  onChange={(e) => setBusinessSettings({ ...businessSettings, businessName: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-slate-300">Tenant Identifier</label>
                <Input value={user?.businessId || businessSettings.businessId} readOnly />
              </div>
              {subscription && (
                <div className="p-4 rounded-xl border border-slate-800 bg-navy-950/60 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{subscription.plan?.name}</span>
                    <Badge variant="success">{subscription.status}</Badge>
                  </div>
                  <div className="text-slate-400">
                    Monthly Agent Executions: <strong className="text-white">{subscription.usage?.agent_executions ?? 0}</strong> / {subscription.plan?.max_monthly_executions}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Tab 2: Local AI Model Settings (Honest Hardware Telemetry) */}
        {activeTab === "models" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-400" />
                Local Ollama Runtime Configuration
              </CardTitle>
              <CardDescription>Real hardware telemetry & verified local model bindings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 max-w-xl">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-slate-300">Primary Model</label>
                <Input
                  value={localModelSettings.primaryModel}
                  onChange={(e) => setLocalModelSettings({ ...localModelSettings, primaryModel: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase text-slate-300">Fallback Model</label>
                <Input
                  value={localModelSettings.fallbackModel}
                  onChange={(e) => setLocalModelSettings({ ...localModelSettings, fallbackModel: e.target.value })}
                />
              </div>
              <div className="p-3 rounded-lg border border-cyan-500/30 bg-cyan-950/20 text-xs text-cyan-200 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                {hw
                  ? `Detected Hardware: ${hw.gpu_name || "CPU Mode"} (${hw.vram_total_mb ? (hw.vram_total_mb / 1024).toFixed(1) : 0} GB VRAM) • ${(hw.ram_total_mb / 1024).toFixed(1)} GB System RAM • ${hw.cpu_count} Logical Cores`
                  : "Hardware telemetry loading..."}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tab 3: Team & Privacy */}
        {activeTab === "users" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white">Active Operator & GDPR Data Portability</CardTitle>
              <CardDescription>Export tenant data cleanly or inspect current RBAC identity</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="p-3 rounded-lg border border-slate-800 bg-navy-950/70 flex items-center justify-between">
                <div>
                  <div className="font-bold text-white">{user?.name}</div>
                  <div className="text-slate-400">{user?.email}</div>
                </div>
                <Badge variant="cyan">{user?.role}</Badge>
              </div>
              <Button size="sm" variant="outline" onClick={handlePrivacyExport} className="gap-2 text-xs">
                <Download className="w-3.5 h-3.5" />
                Export Tenant Data (GDPR JSON)
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Tab 4: Channel Integrations (Honest Sandbox vs Connected Status) */}
        {activeTab === "integrations" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {integrations.map((integ) => (
              <Card key={integ.platform} className="p-4 flex items-center justify-between">
                <div>
                  <div className="font-bold text-white text-sm capitalize">{integ.platform}</div>
                  <div className="text-slate-400 text-[11px] mt-0.5">
                    {integ.status} ({integ.latency_ms}ms)
                  </div>
                </div>
                <Badge variant={integ.is_sandbox ? "warning" : "success"} className="text-[10px]">
                  {integ.is_sandbox ? "Sandbox Mode" : "Live Connected"}
                </Badge>
              </Card>
            ))}
          </div>
        )}

        {/* Tab 5: Local Beta Controls */}
        {activeTab === "beta" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white">Local Beta Simulation & Reset Controls</CardTitle>
              <CardDescription>
                Seed or safely reset strictly isolated synthetic [DEMO] workspace records (biz_demo_nova_saas). Never touches real customer data.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              <Button size="sm" onClick={handleSeedDemo} className="gap-1.5 text-xs">
                <Database className="w-3.5 h-3.5" />
                Seed Synthetic [DEMO] Workspace
              </Button>
              <Button size="sm" variant="outline" onClick={handleResetDemo} className="gap-1.5 text-xs text-amber-300 border-amber-500/40">
                <RotateCcw className="w-3.5 h-3.5" />
                Safely Reset Demo Data Only
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
