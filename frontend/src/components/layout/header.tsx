"use client";

import { useState, useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useGovernanceStore } from "@/stores/governance-store";
import { apiClient } from "@/lib/api-client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  Building2,
  ChevronDown,
  Power,
  Check,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";

export function Header() {
  const queryClient = useQueryClient();
  const { user, switchBusiness } = useAuthStore();
  const { killSwitch, setKillSwitch, setBackendConnected } = useGovernanceStore();
  const [killModalOpen, setKillModalOpen] = useState(false);
  const [orgMenuOpen, setOrgMenuOpen] = useState(false);
  const [notifMenuOpen, setNotifMenuOpen] = useState(false);
  const [reasonInput, setReasonInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [killError, setKillError] = useState<string | null>(null);

  const { data: ksRes } = useQuery({
    queryKey: ["killswitch", user?.businessId],
    queryFn: () => apiClient.getKillSwitchStatus(),
  });

  useEffect(() => {
    if (ksRes?.data) {
      setKillSwitch(ksRes.data);
      setBackendConnected(!ksRes.isDevFixture);
    }
  }, [ksRes, setKillSwitch, setBackendConnected]);

  const { data: orgsRes } = useQuery({
    queryKey: ["organizations"],
    queryFn: () => apiClient.getOrganizations(),
  });

  const { data: notifsRes } = useQuery({
    queryKey: ["notifications", user?.businessId],
    queryFn: () => apiClient.getNotifications(false),
  });

  const orgs = orgsRes?.data || [];
  const notifications = notifsRes?.data || [];
  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleSelectWorkspace = (bizId: string, bizName: string) => {
    apiClient.setBusinessId(bizId);
    switchBusiness(bizId, bizName);
    setOrgMenuOpen(false);
    queryClient.invalidateQueries();
  };

  const handleMarkRead = async (id: string) => {
    try {
      await apiClient.markNotificationRead(id);
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    } catch {
      // Ignore if backend unavailable
    }
  };

  const handleToggleKillSwitch = async () => {
    setIsSubmitting(true);
    setKillError(null);
    const newStatus = !killSwitch.engaged;
    const reason =
      reasonInput.trim() ||
      (newStatus
        ? "Emergency operational shutdown triggered by human operator."
        : "Operational clearance verified by authorized human admin.");
    try {
      const res = await apiClient.toggleKillSwitch(newStatus, reason);
      setKillSwitch(res.data);
      queryClient.invalidateQueries({ queryKey: ["killswitch"] });
      queryClient.invalidateQueries({ queryKey: ["auditLogs"] });
      setKillModalOpen(false);
      setReasonInput("");
    } catch (err: any) {
      setKillError(err?.message || "Failed to update backend Kill Switch state.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-navy-900/60 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Workspace Switcher & Fleet Indicator */}
      <div className="flex items-center gap-4 relative">
        <button
          type="button"
          onClick={() => setOrgMenuOpen((prev) => !prev)}
          aria-label="Switch organization workspace"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-800/80 border border-slate-700/60 hover:border-blue-500/50 text-xs transition-colors"
        >
          <Building2 className="w-4 h-4 text-blue-400" />
          <span className="font-semibold text-white max-w-[200px] truncate">
            {user?.businessName || "Apex Multi-Channel Enterprise"}
          </span>
          <span className="text-slate-500 font-mono text-[11px] hidden sm:inline">
            [{user?.businessId || "biz_apex_enterprises"}]
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        </button>

        {orgMenuOpen && (
          <div className="absolute left-0 top-12 w-72 rounded-xl border border-slate-700 bg-navy-900 shadow-2xl p-2 z-50">
            <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Authorized Workspaces ({orgs.length || 1})
            </div>
            {orgs.length > 0 ? (
              orgs.map((org) => (
                <button
                  key={org.id}
                  type="button"
                  onClick={() => handleSelectWorkspace(org.id, org.name)}
                  className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-navy-800 flex items-center justify-between text-xs text-slate-200"
                >
                  <div className="truncate pr-2">
                    <div className="font-semibold text-white truncate">{org.name}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{org.id} • {org.user_role}</div>
                  </div>
                  {user?.businessId === org.id && <Check className="w-3.5 h-3.5 text-cyan-400 shrink-0" />}
                </button>
              ))
            ) : (
              <div className="px-2.5 py-2 text-xs text-slate-400">
                Current: {user?.businessName || "Apex Multi-Channel Enterprise"}
              </div>
            )}
          </div>
        )}

        <Badge variant="cyan" className="hidden sm:inline-flex gap-1 text-[11px]">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
          8 Agents Synchronized
        </Badge>
      </div>

      {/* Right Controls: Notifications, Kill Switch, User */}
      <div className="flex items-center gap-3 relative">
        {/* Notifications Bell */}
        <button
          type="button"
          onClick={() => setNotifMenuOpen((prev) => !prev)}
          aria-label="Open notifications"
          className="relative p-2 rounded-lg border border-slate-700/70 bg-navy-900/80 text-slate-300 hover:text-white hover:border-blue-500/50 transition-colors"
        >
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 h-4 min-w-[16px] px-1 rounded-full bg-blue-600 text-[10px] font-bold text-white flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </button>

        {notifMenuOpen && (
          <div className="absolute right-0 top-12 w-80 rounded-xl border border-slate-700 bg-navy-900 shadow-2xl p-3 z-50 space-y-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-bold text-white">Notifications</span>
              <span className="text-[11px] text-slate-400">{unreadCount} unread</span>
            </div>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {notifications.length === 0 ? (
                <div className="text-xs text-slate-400 py-4 text-center">No notifications yet.</div>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`p-2.5 rounded-lg border text-xs space-y-1 ${
                      n.read ? "border-slate-800 bg-navy-950/40 text-slate-400" : "border-blue-500/30 bg-blue-950/20 text-slate-200"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-white">{n.title}</span>
                      {!n.read && (
                        <button
                          type="button"
                          onClick={() => handleMarkRead(n.id)}
                          className="text-[10px] text-cyan-400 hover:underline"
                        >
                          Mark read
                        </button>
                      )}
                    </div>
                    <p className="text-[11px]">{n.message}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Fail-closed Killswitch Trigger */}
        <Button
          variant={killSwitch.engaged ? "destructive" : "outline"}
          size="sm"
          onClick={() => setKillModalOpen(true)}
          className={
            killSwitch.engaged
              ? "animate-pulse font-bold text-xs shadow-glow-rose"
              : "border-slate-700 text-xs text-rose-300 hover:text-white hover:bg-rose-950/60 hover:border-rose-700"
          }
        >
          <Power className="w-3.5 h-3.5 mr-1.5 text-rose-400" />
          {killSwitch.engaged ? "KILL SWITCH ACTIVE" : "EMERGENCY HALT"}
        </Button>

        {/* User Badge */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-800">
          <div className="h-8 w-8 rounded-full bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-xs font-semibold text-blue-300">
            {user?.name?.slice(0, 2).toUpperCase() || "MV"}
          </div>
          <div className="hidden md:block text-left text-xs leading-tight">
            <div className="font-semibold text-white">{user?.name}</div>
            <div className="text-slate-400 capitalize">{user?.role}</div>
          </div>
        </div>
      </div>

      {/* Kill Switch Engagement Modal */}
      <Modal
        isOpen={killModalOpen}
        onClose={() => setKillModalOpen(false)}
        title={
          killSwitch.engaged
            ? "Disengage Fail-Closed Kill Switch"
            : "Engage Global Fail-Closed Kill Switch"
        }
        description={
          killSwitch.engaged
            ? "Resume all 8 autonomous marketing agents and publishing queue operations."
            : "Instantly halt all agent runs, API dispatches, and LLM completions. Fail-closed architecture halts all automated activity."
        }
      >
        <div className="space-y-4">
          {killError && (
            <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-500/40 text-xs text-rose-200 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              {killError}
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Reason for Action (Recorded to Immutable Audit Hash Chain):
            </label>
            <textarea
              value={reasonInput}
              onChange={(e) => setReasonInput(e.target.value)}
              placeholder="e.g., Routine maintenance, sudden regulatory change, budget verification..."
              className="w-full h-24 rounded-lg border border-slate-700 bg-navy-950/80 p-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button variant="outline" size="sm" onClick={() => setKillModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={killSwitch.engaged ? "default" : "destructive"}
              size="sm"
              disabled={isSubmitting}
              onClick={handleToggleKillSwitch}
            >
              {killSwitch.engaged ? "Confirm Resume Agents" : "HALT ALL AGENTS NOW"}
            </Button>
          </div>
        </div>
      </Modal>
    </header>
  );
}
