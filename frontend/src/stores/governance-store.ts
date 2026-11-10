import { create } from "zustand";
import { KillSwitchStatus } from "@/types";
import { MOCK_KILL_SWITCH } from "@/lib/fixtures";

interface GovernanceState {
  killSwitch: KillSwitchStatus;
  isBackendConnected: boolean;
  backendUrl: string;
  setKillSwitch: (status: KillSwitchStatus) => void;
  setBackendConnected: (connected: boolean) => void;
}

export const useGovernanceStore = create<GovernanceState>((set) => ({
  killSwitch: MOCK_KILL_SWITCH,
  isBackendConnected: false,
  backendUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  setKillSwitch: (status: KillSwitchStatus) => set({ killSwitch: status }),
  setBackendConnected: (connected: boolean) => set({ isBackendConnected: connected }),
}));

