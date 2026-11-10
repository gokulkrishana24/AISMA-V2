"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Bot,
  FileEdit,
  Palette,
  Calendar,
  ShieldCheck,
  Star,
  MessageSquare,
  Search,
  Radar,
  BarChart3,
  BookOpen,
  DollarSign,
  ScrollText,
  Settings,
  ChevronDown,
  Layers,
  Cpu,
} from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";

const NAV_GROUPS = [
  {
    title: "OPERATIONS",
    items: [
      { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
      {
        name: "Agent Command Center",
        href: "/agents",
        icon: Bot,
        subItems: [
          { name: "Search Visibility", href: "/agents/search-visibility" },
          { name: "Market Radar", href: "/agents/market-radar" },
          { name: "Content Engine", href: "/agents/content-engine" },
          { name: "Creative Studio", href: "/agents/creative-studio" },
          { name: "Publishing & Social", href: "/agents/publishing-social" },
          { name: "Reviews & Reputation", href: "/agents/reviews-reputation" },
          { name: "Leads & Conversations", href: "/agents/leads-conversations" },
          { name: "Results & ROI", href: "/agents/results-roi" },
        ],
      },
      {
        name: "Approval Center",
        href: "/approvals",
        icon: ShieldCheck,
        badge: "3",
        badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/30",
      },
    ],
  },
  {
    title: "CREATIVE & PUBLISHING",
    items: [
      { name: "Content Studio", href: "/content-studio", icon: FileEdit },
      { name: "Creative Studio", href: "/creative-studio", icon: Palette },
      { name: "Content Calendar", href: "/calendar", icon: Calendar },
    ],
  },
  {
    title: "GROWTH & SENTINEL",
    items: [
      {
        name: "Leads & Inbox",
        href: "/conversations",
        icon: MessageSquare,
        badge: "VIP",
        badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/30",
      },
      { name: "Reviews & Reputation", href: "/reviews", icon: Star },
      { name: "SEO Intelligence", href: "/seo", icon: Search },
      { name: "Competitor Radar", href: "/competitor", icon: Radar },
      { name: "Analytics & ROI", href: "/analytics", icon: BarChart3 },
    ],
  },
  {
    title: "GOVERNANCE & SYSTEM",
    items: [
      {
        name: "Local AI Infrastructure",
        href: "/infrastructure",
        icon: Cpu,
        badge: "OLLAMA",
        badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
      },
      { name: "Brand OS", href: "/brand-os", icon: BookOpen },
      { name: "Budget & Limits", href: "/budget", icon: DollarSign },
      { name: "Audit Trail", href: "/audit", icon: ScrollText },
      { name: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [agentsOpen, setAgentsOpen] = useState(
    pathname.startsWith("/agents")
  );

  const { data: approvalsRes } = useQuery({
    queryKey: ["approvals"],
    queryFn: () => apiClient.getApprovals(),
  });
  const pendingApprovalsCount = (approvalsRes?.data || []).filter(
    (a) => a.status === "pending"
  ).length;

  return (
    <aside className="w-64 shrink-0 border-r border-slate-800/80 bg-navy-900/90 backdrop-blur-xl flex flex-col h-screen sticky top-0 z-40 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-5 border-b border-slate-800/80 gap-3">
        <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center shadow-glow-blue">
          <Layers className="h-5 w-5 text-white" />
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-blue-400">
            Agent Team v2
          </div>
          <div className="text-sm font-bold text-white tracking-tight leading-none">
            AI Operations Hub
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="space-y-1">
            <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              {group.title}
            </div>
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/dashboard"
                  ? pathname === "/dashboard" || pathname === "/"
                  : pathname.startsWith(item.href);

              if (item.subItems) {
                return (
                  <div key={item.name} className="space-y-1">
                    <button
                      onClick={() => setAgentsOpen(!agentsOpen)}
                      className={cn(
                        "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                        isActive
                          ? "bg-blue-600/15 text-blue-400 font-semibold"
                          : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
                      )}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className="w-4 h-4 text-blue-400" />
                        <span>{item.name}</span>
                      </div>
                      <ChevronDown
                        className={cn(
                          "w-4 h-4 text-slate-400 transition-transform duration-200",
                          agentsOpen && "rotate-180 text-blue-400"
                        )}
                      />
                    </button>
                    {agentsOpen && (
                      <div className="pl-7 pr-2 py-1 space-y-1 border-l border-slate-800/80 ml-5">
                        <Link
                          href="/agents"
                          className={cn(
                            "block px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors",
                            pathname === "/agents"
                              ? "bg-blue-600/20 text-blue-300 font-semibold"
                              : "text-slate-400 hover:text-white hover:bg-slate-800/40"
                          )}
                        >
                          Command Grid (All 8)
                        </Link>
                        {item.subItems.map((sub) => {
                          const isSubActive = pathname === sub.href;
                          return (
                            <Link
                              key={sub.name}
                              href={sub.href}
                              className={cn(
                                "block px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors",
                                isSubActive
                                  ? "bg-blue-600/20 text-blue-300 font-semibold"
                                  : "text-slate-400 hover:text-white hover:bg-slate-800/40"
                              )}
                            >
                              {sub.name}
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              }

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors group",
                    isActive
                      ? "bg-blue-600/15 text-blue-400 font-semibold"
                      : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        "w-4 h-4 transition-colors",
                        isActive
                          ? "text-blue-400"
                          : "text-slate-400 group-hover:text-blue-400"
                      )}
                    />
                    <span>{item.name}</span>
                  </div>
                  {(item.href === "/approvals" ? pendingApprovalsCount > 0 : Boolean(item.badge)) && (
                    <span
                      className={cn(
                        "px-1.5 py-0.5 text-[10px] font-bold rounded border",
                        item.badgeColor
                      )}
                    >
                      {item.href === "/approvals" ? String(pendingApprovalsCount) : item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* Footer System Status */}
      <div className="p-3 border-t border-slate-800/80 bg-navy-950/40">
        <div className="flex items-center justify-between px-2 py-1 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            Governance v2.0
          </span>
          <span className="font-mono text-[10px] text-slate-500">SHA-256</span>
        </div>
      </div>
    </aside>
  );
}

