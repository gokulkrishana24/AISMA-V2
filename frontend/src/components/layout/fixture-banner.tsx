"use client";

import { useGovernanceStore } from "@/stores/governance-store";
import { AlertCircle, CheckCircle2, ShieldAlert, Cpu } from "lucide-react";

export function FixtureBanner() {
  const { isBackendConnected, killSwitch, backendUrl } = useGovernanceStore();

  return (
    <div className="flex flex-col">
      {killSwitch.engaged && (
        <div className="bg-rose-950/90 border-b border-rose-500/50 px-4 py-2 text-xs font-medium text-rose-200 flex items-center justify-between backdrop-blur-md">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />
            <span className="font-bold tracking-wide">
              GOVERNANCE KILL SWITCH ENGAGED ({killSwitch.scope.toUpperCase()}):
            </span>
            <span>{killSwitch.reason}</span>
          </div>
          <span className="text-rose-300/80 text-[11px]">
            Updated by: {killSwitch.updated_by} at {killSwitch.updated_at}
          </span>
        </div>
      )}

      {!isBackendConnected ? (
        <div className="bg-amber-950/70 border-b border-amber-500/30 px-4 py-1.5 text-xs text-amber-200/90 flex items-center justify-between backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="font-semibold text-amber-300">
              DEVELOPMENT FIXTURE MODE:
            </span>
            <span>
              FastAPI backend ({backendUrl}) is offline. Displaying typed dev fixtures. Never represented as live production data.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/20 text-[10px] text-amber-300 border border-amber-500/30">
              <Cpu className="w-3 h-3" /> Mock In-Memory Loop
            </span>
          </div>
        </div>
      ) : (
        <div className="bg-emerald-950/70 border-b border-emerald-500/30 px-4 py-1.5 text-xs text-emerald-200/90 flex items-center justify-between backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="font-semibold text-emerald-300">
              GOVERNANCE BACKEND CONNECTED:
            </span>
            <span>Active FastAPI endpoint at {backendUrl}</span>
          </div>
        </div>
      )}
    </div>
  );
}

