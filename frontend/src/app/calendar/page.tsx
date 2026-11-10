"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  Filter,
  Clock,
  Plus,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";

const DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function CalendarPage() {
  const queryClient = useQueryClient();
  const [selectedChannel, setSelectedChannel] = useState<string>("all");
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [channelInput, setChannelInput] = useState("linkedin");
  const [contentInput, setContentInput] = useState("");
  const [dateTimeInput, setDateTimeInput] = useState("2026-11-12T10:00");
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [scheduleSuccess, setScheduleSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: scheduledRes, isLoading } = useQuery({
    queryKey: ["scheduledPosts"],
    queryFn: () => apiClient.getScheduledPosts(),
  });

  const { data: draftsRes } = useQuery({
    queryKey: ["drafts"],
    queryFn: () => apiClient.getDrafts(),
  });

  const scheduledPosts = scheduledRes?.data || [];
  const drafts = draftsRes?.data || [];

  const getWeekdayName = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      const dayIdx = (d.getDay() + 6) % 7; // Monday=0 .. Sunday=6
      return DAYS_OF_WEEK[dayIdx] || "Monday";
    } catch {
      return "Monday";
    }
  };

  const getFormattedTime = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toISOString().slice(11, 16) + " UTC";
    } catch {
      return "10:00 UTC";
    }
  };

  const calendarItems = [
    ...scheduledPosts.map((p) => ({
      id: p.id,
      day: getWeekdayName(p.scheduled_time),
      time: getFormattedTime(p.scheduled_time),
      channel: p.channel,
      title: p.content,
      status: p.status,
      source: "Scheduler",
    })),
    ...drafts.map((d, idx) => ({
      id: `draft_${d.id}`,
      day: DAYS_OF_WEEK[(idx + 2) % 7],
      time: "Unscheduled",
      channel: d.channel,
      title: d.title,
      status: d.status,
      source: "Content Draft",
    })),
  ];

  const filteredItems = calendarItems.filter((item) =>
    selectedChannel === "all" ? true : item.channel.toLowerCase() === selectedChannel
  );

  const handleSchedulePost = async () => {
    if (!contentInput.trim()) {
      setScheduleError("Post content cannot be empty.");
      return;
    }
    setIsSubmitting(true);
    setScheduleError(null);
    setScheduleSuccess(null);
    try {
      const isoDate = new Date(dateTimeInput).toISOString();
      const res = await apiClient.schedulePost({
        channel: channelInput,
        content: contentInput.trim(),
        scheduled_time: isoDate,
      });
      setScheduleSuccess(`Scheduled post ${res.data.id} cleanly on ${channelInput}.`);
      setContentInput("");
      queryClient.invalidateQueries({ queryKey: ["scheduledPosts"] });
      setTimeout(() => setScheduleOpen(false), 800);
    } catch (err: any) {
      setScheduleError(err?.message || "Failed to schedule post.");
    } finally {
      setIsSubmitting(false);
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
                Publishing Queue
              </Badge>
              <span className="text-xs text-slate-400">
                Live Cross-Platform Schedule ({scheduledPosts.length} Scheduled, {drafts.length} Drafts)
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Content Calendar
            </h1>
          </div>

          <Button
            size="sm"
            onClick={() => {
              setScheduleError(null);
              setScheduleSuccess(null);
              setScheduleOpen(true);
            }}
            className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue gap-1.5 text-xs font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            Schedule Post
          </Button>
        </div>

        {/* Filter Bar */}
        <div className="flex items-center justify-between p-3 rounded-xl border border-slate-800/80 bg-navy-900/80 text-xs">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold text-slate-300">Filter by Channel:</span>
            {["all", "linkedin", "twitter", "meta"].map((ch) => (
              <button
                key={ch}
                onClick={() => setSelectedChannel(ch)}
                className={`px-2.5 py-1 rounded-md font-medium capitalize transition-colors ${
                  selectedChannel === ch
                    ? "bg-blue-600/20 text-blue-300 border border-blue-500/30"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {ch}
              </button>
            ))}
          </div>

          <div className="text-slate-400 font-mono text-[11px]">
            {isLoading ? "Syncing..." : "Backend Synchronized"}
          </div>
        </div>

        {/* Weekly Calendar Grid */}
        <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
          {DAYS_OF_WEEK.map((day) => {
            const dayItems = filteredItems.filter((i) => i.day === day);
            const isToday = day === "Tuesday";

            return (
              <div
                key={day}
                className={`rounded-xl border flex flex-col min-h-[380px] p-3 transition-colors ${
                  isToday
                    ? "border-blue-500/40 bg-navy-900/90 shadow-glass"
                    : "border-slate-800/80 bg-navy-950/60"
                }`}
              >
                <div className="flex items-center justify-between pb-2 border-b border-slate-800/80 mb-3">
                  <span
                    className={`text-xs font-bold uppercase tracking-wider ${
                      isToday ? "text-blue-400" : "text-slate-400"
                    }`}
                  >
                    {day.slice(0, 3)}
                  </span>
                  {isToday && (
                    <Badge variant="cyan" className="text-[9px] px-1 py-0">
                      Today
                    </Badge>
                  )}
                </div>

                <div className="space-y-2.5 flex-1">
                  {dayItems.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-[11px] text-slate-600">
                      No slots
                    </div>
                  ) : (
                    dayItems.map((item) => (
                      <div
                        key={item.id}
                        className="p-2.5 rounded-lg border border-slate-800 bg-navy-900/90 text-xs space-y-2 hover:border-slate-700 transition-all shadow-sm"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[10px] text-slate-400 flex items-center gap-1">
                            <Clock className="w-3 h-3 text-blue-400" />
                            {item.time}
                          </span>
                          <Badge
                            variant={
                              item.status === "pending" || item.status === "scheduled"
                                ? "success"
                                : item.status === "approved"
                                ? "cyan"
                                : "warning"
                            }
                            className="text-[9px] uppercase px-1 py-0"
                          >
                            {item.status.replace("_", " ")}
                          </Badge>
                        </div>

                        <p className="font-semibold text-slate-200 line-clamp-2 text-[11px]">
                          {item.title}
                        </p>

                        <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] text-slate-400">
                          <span className="capitalize">{item.channel}</span>
                          <span className="text-blue-400">{item.source}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Schedule Post Modal */}
        <Modal
          isOpen={scheduleOpen}
          onClose={() => setScheduleOpen(false)}
          title="Schedule Post to Publishing Queue"
          description="Duplicate posts and posts submitted while Kill Switch is engaged are blocked fail-closed."
        >
          <div className="space-y-4">
            {scheduleError && (
              <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-500/40 text-xs text-rose-200 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                {scheduleError}
              </div>
            )}
            {scheduleSuccess && (
              <div className="p-2.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-xs text-emerald-200 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                {scheduleSuccess}
              </div>
            )}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Channel</label>
              <select
                aria-label="Channel"
                value={channelInput}
                onChange={(e) => setChannelInput(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-white"
              >
                <option value="linkedin">LinkedIn</option>
                <option value="twitter">X / Twitter</option>
                <option value="meta">Meta (Facebook / Instagram)</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Scheduled Date & Time (UTC)</label>
              <input
                type="datetime-local"
                value={dateTimeInput}
                onChange={(e) => setDateTimeInput(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-white"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Post Copy</label>
              <textarea
                value={contentInput}
                onChange={(e) => setContentInput(e.target.value)}
                placeholder="Write post copy..."
                className="w-full h-24 rounded-lg border border-slate-700 bg-navy-950 p-3 text-sm text-white"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setScheduleOpen(false)}>
                Cancel
              </Button>
              <Button size="sm" disabled={isSubmitting} onClick={handleSchedulePost}>
                {isSubmitting ? "Scheduling..." : "Confirm Schedule"}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </AppLayout>
  );
}
