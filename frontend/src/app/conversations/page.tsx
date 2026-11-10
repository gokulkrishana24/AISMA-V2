"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { LeadConversation } from "@/types";
import {
  MessageSquare,
  Zap,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Send,
  User,
  ArrowUpRight,
  ShieldAlert,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

export default function ConversationsPage() {
  const [selectedConvId, setSelectedConvId] = useState<string>("conv_001");
  const [customReply, setCustomReply] = useState("");

  const { data: convsRes, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => apiClient.getConversations(),
  });

  const conversations = convsRes?.data || [];
  const activeConv = conversations.find((c) => c.id === selectedConvId) || conversations[0];

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Leads & Conversations
              </Badge>
              <span className="text-xs text-slate-400">
                Inbound Lead Triage, Intent Scoring & Escalation Deck
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Inbound Inquiries & Lead Qualification
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="cyan" className="gap-1.5 text-xs font-mono">
              <Zap className="w-3.5 h-3.5" />
              Real-time Inbound Scanner Active
            </Badge>
          </div>
        </div>

        {/* 2-Pane Conversation Inbox */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[600px]">
          {/* Left Pane: Conversation List */}
          <div className="lg:col-span-4 space-y-3">
            <div className="text-xs font-semibold uppercase text-slate-400 px-1">
              Active Conversations ({conversations.length})
            </div>

            {conversations.map((conv) => {
              const isSelected = conv.id === activeConv?.id;

              return (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConvId(conv.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "border-blue-500 bg-blue-600/15 shadow-glow-blue"
                      : "border-slate-800 bg-navy-900/70 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <div className="h-7 w-7 rounded-full bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-xs font-bold text-blue-300">
                        {conv.customerName.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white leading-none">
                          {conv.customerName}
                        </div>
                        <div className="text-[10px] text-slate-400">{conv.customerHandle}</div>
                      </div>
                    </div>

                    <Badge
                      variant={conv.intent === "high_intent" ? "destructive" : "cyan"}
                      className="text-[9px] uppercase font-bold"
                    >
                      {conv.intent.replace("_", " ")}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {conv.lastMessage}
                  </p>

                  <div className="flex items-center justify-between pt-2 mt-1 border-t border-slate-800/60 text-[10px] text-slate-500">
                    <span>Score: <strong className="text-emerald-400">{conv.leadScore}/100</strong></span>
                    <span className="capitalize">{conv.platform}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Pane: Conversation Details, Intent Intelligence & Reply Composer */}
          <div className="lg:col-span-8 space-y-6">
            {activeConv && (
              <>
                <Card>
                  <CardHeader className="pb-3 border-b border-slate-800">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center font-bold text-blue-300">
                          {activeConv.customerName.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <CardTitle className="text-base text-white">
                            {activeConv.customerName}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            {activeConv.customerHandle} • Platform: <strong className="capitalize text-white">{activeConv.platform}</strong>
                          </CardDescription>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {activeConv.highIntentAlert && (
                          <Badge variant="destructive" className="text-xs font-bold animate-pulse">
                            <Zap className="w-3.5 h-3.5 mr-1" />
                            High Intent Alert ($50k+ Deal Potential)
                          </Badge>
                        )}
                        <Badge variant="success" className="font-mono text-xs">
                          Lead Score: {activeConv.leadScore}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="pt-4 space-y-4">
                    {/* Chat Bubble Thread */}
                    <div className="space-y-3 min-h-[160px] p-3 rounded-xl bg-navy-950/60 border border-slate-800">
                      {activeConv.history.map((msg, idx) => (
                        <div
                          key={idx}
                          className={`flex flex-col ${
                            msg.sender === "customer" ? "items-start" : "items-end"
                          }`}
                        >
                          <div
                            className={`p-3 rounded-xl text-xs max-w-[80%] leading-relaxed ${
                              msg.sender === "customer"
                                ? "bg-navy-900 border border-slate-700/80 text-slate-100"
                                : "bg-blue-600/30 border border-blue-500/40 text-blue-100"
                            }`}
                          >
                            {msg.text}
                          </div>
                          <span className="text-[10px] text-slate-500 mt-0.5 px-1">
                            {msg.sender === "customer" ? activeConv.customerName : "AI Agent"} • {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* AI Suggested Response Box */}
                    {activeConv.draftReply && (
                      <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-950/20 space-y-2">
                        <div className="flex items-center justify-between text-xs font-bold text-blue-300">
                          <span className="flex items-center gap-1.5">
                            <Zap className="w-3.5 h-3.5 text-blue-400" />
                            Agent Draft Reply (Verified Against Brand OS):
                          </span>
                          <span className="text-[10px] text-slate-400">Ready for Human Signoff</span>
                        </div>
                        <p className="text-xs text-slate-200 italic leading-relaxed">
                          "{activeConv.draftReply}"
                        </p>
                        <div className="pt-2 flex justify-end gap-2">
                          <Button
                            size="sm"
                            className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue text-xs h-8"
                            onClick={() => alert("Reply signed and dispatched to social inbox!")}
                          >
                            <Send className="w-3 h-3 mr-1.5" />
                            Authorize & Send Reply
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

