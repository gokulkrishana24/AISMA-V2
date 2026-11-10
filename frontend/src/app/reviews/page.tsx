"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ReviewItem } from "@/types";
import {
  Star,
  ShieldCheck,
  AlertTriangle,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Clock,
  Send,
  CheckCircle2,
  Filter,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function ReviewsReputationPage() {
  const [filterSentiment, setFilterSentiment] = useState<string>("all");

  const { data: reviewsRes, isLoading } = useQuery({
    queryKey: ["reviews"],
    queryFn: () => apiClient.getReviews(),
  });

  const reviews = reviewsRes?.data || [];
  const filteredReviews = reviews.filter((r) =>
    filterSentiment === "all" ? true : r.sentiment === filterSentiment
  );

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Reviews & Reputation Sentinel
              </Badge>
              <span className="text-xs text-slate-400">
                Multi-Platform Customer Voice & Response Orchestration
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Reviews & Reputation
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Badge variant="success" className="gap-1.5 text-xs font-mono">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Auto-Monitoring 4 Platforms
            </Badge>
          </div>
        </div>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Composite Rating
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-white">4.86</span>
                <span className="text-slate-400 text-sm">/ 5.0</span>
              </div>
              <div className="flex items-center gap-1 text-amber-400 mt-1">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star key={s} className="w-4 h-4 fill-amber-400" />
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Positive Sentiment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-emerald-400">92.4%</div>
              <p className="text-xs text-slate-400 mt-1">
                +1.8% shift over the past 30 days
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-semibold uppercase text-slate-400">
                Response Coverage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-blue-400">98.9%</div>
              <p className="text-xs text-slate-400 mt-1">
                Average reply draft latency: 2.1 minutes
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Reviews Feed with AI Drafted Responses */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-blue-400" />
              Customer Reviews & AI Response Drafts
            </h2>

            {/* Filter buttons */}
            <div className="flex items-center gap-2 text-xs">
              {["all", "positive", "negative"].map((s) => (
                <button
                  key={s}
                  onClick={() => setFilterSentiment(s)}
                  className={`px-3 py-1 rounded-md font-medium capitalize transition-colors ${
                    filterSentiment === s
                      ? "bg-blue-600/20 text-blue-300 border border-blue-500/30"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            {filteredReviews.map((rev) => (
              <Card key={rev.id} className="p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-full bg-slate-800 flex items-center justify-center font-bold text-xs text-slate-200">
                      {rev.author.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-semibold text-white text-sm flex items-center gap-2">
                        {rev.author}
                        <Badge variant="secondary" className="capitalize text-[10px]">
                          {rev.platform}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-1 mt-0.5">
                        {Array.from({ length: rev.rating }).map((_, i) => (
                          <Star key={i} className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {rev.alert && (
                      <Badge variant="destructive" className="text-[10px] uppercase font-bold animate-pulse">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        Negative Alert
                      </Badge>
                    )}
                    <span className="text-xs text-slate-500">
                      {new Date(rev.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-200 leading-relaxed font-sans">
                  "{rev.text}"
                </p>

                {/* AI Drafted Response Box */}
                {rev.suggestedResponse && (
                  <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-950/20 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-blue-300 flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                        AI Agent Suggested Response:
                      </span>
                      <Badge
                        variant={rev.status === "replied" ? "success" : "warning"}
                        className="text-[9px] uppercase font-mono"
                      >
                        {rev.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-300 italic leading-relaxed">
                      "{rev.suggestedResponse}"
                    </p>

                    {rev.status !== "replied" && (
                      <div className="pt-2 flex justify-end gap-2">
                        <Button
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue text-xs h-7 px-3"
                          onClick={() => alert("Response authorized and queued for delivery!")}
                        >
                          <Send className="w-3 h-3 mr-1" />
                          Approve & Publish Response
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

