import { create } from "zustand";
import { UserProfile } from "@/types";
import { MOCK_USER } from "@/lib/fixtures";

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, token?: string) => void;
  logout: () => void;
  switchBusiness: (businessId: string, businessName: string) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: MOCK_USER,
  token: "dev_mock_jwt_session",
  isAuthenticated: true,
  login: (email: string, token = "dev_token_session") => {
    set({
      user: {
        ...MOCK_USER,
        email,
      },
      token,
      isAuthenticated: true,
    });
  },
  logout: () => {
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },
  switchBusiness: (businessId: string, businessName: string) => {
    set((state) => ({
      user: state.user
        ? {
            ...state.user,
            businessId,
            businessName,
          }
        : null,
    }));
  },
}));

