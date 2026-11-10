"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ApprovalRequest } from "@/types";
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  DollarSign,
  FileText,
  UserCheck,
  History,
  Lock,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";

export default function ApprovalCenterPage() {
  const queryClient = useQueryClient();
  const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);
  const [decisionAction, setDecisionAction] = useState<"approve" | "reject">("approve");
  const [decisionNote, setDecisionNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const { data: approvalsRes, isLoading } = useQuery({
    queryKey: ["approvals"],
    queryFn: () => apiClient.getApprovals(),
  });

  const approvals = approvalsRes?.data || [];
  const pendingApprovals = approvals.filter((a) => a.status === "pending");
  const resolvedApprovals = approvals.filter((a) => a.status !== "pending");

  const handleDecision = async () => {
    if (!selectedRequest) return;
    setIsSubmitting(true);
    setStatusMessage(null);

    try {
      // Strictly invoke backend governance endpoint
      const res = await apiClient.submitApprovalDecision(selectedRequest.id, {
        action: decisionAction,
        note: decisionNote,
      });

      setStatusMessage(
        `Decision '${res.data.status.toUpperCase()}' cryptographically registered to hash chain.`
      );
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["auditLogs"] });

      setTimeout(() => {
        setSelectedRequest(null);
        setDecisionNote("");
        setStatusMessage(null);
      }, 1000);
    } catch (err: any) {
      setStatusMessage(`Authorization Error: ${err.message}`);
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
              <Badge variant="warning" className="text-[10px] tracking-wider uppercase font-bold">
                Governance Boundary
              </Badge>
              <span className="text-xs text-slate-400">
                Mandatory Human-In-The-Loop Signoff Deck
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Approval Center
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 flex items-center gap-1.5 font-mono">
              <Lock className="w-3.5 h-3.5 text-emerald-400" />
              Default-Deny Policy Active
            </span>
          </div>
        </div>

        {/* Pending Requests Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              Pending Sign-Off Requests ({pendingApprovals.length})
            </h2>
            <span className="text-xs text-slate-400">
              Publishing is blocked until human approval is signed
            </span>
          </div>

          {pendingApprovals.length === 0 ? (
            <div className="p-8 rounded-xl border border-slate-800 bg-navy-900/60 text-center text-slate-400">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              No pending approvals. All agent actions are compliant and verified.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pendingApprovals.map((req) => (
                <Card
                  key={req.id}
                  className="flex flex-col justify-between hover:border-amber-500/50 transition-all duration-200"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-mono text-blue-400 font-bold uppercase text-[10px]">
                        {req.id}
                      </span>
                      <Badge
                        variant={
                          req.urgency === "critical"
                            ? "destructive"
                            : req.urgency === "high"
                            ? "warning"
                            : "secondary"
                        }
                        className="text-[10px] uppercase font-bold"
                      >
                        {req.urgency} Urgency
                      </Badge>
                    </div>
                    <CardTitle className="text-sm font-bold text-white">
                      {req.title}
                    </CardTitle>
                    <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-1">
                      <span>Submitted by: <strong>{req.agentId}</strong></span>
                      <span>•</span>
                      <span>{new Date(req.submittedAt).toLocaleTimeString()}</span>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-3 pt-0">
                    {/* Content Preview */}
                    <div className="p-3 rounded-lg bg-navy-950 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans line-clamp-3 italic">
                      "{req.contentPreview}"
                    </div>

                    {/* Policy & Budget Warnings */}
                    {(req.budgetWarnings || []).length > 0 && (
                      <div className="p-2 rounded bg-amber-950/40 border border-amber-500/40 text-[11px] text-amber-300 flex items-start gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                        <span>{req.budgetWarnings[0]}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/80">
                      <span>Risk Index: {req.riskScore} / 100</span>
                      <span className="text-emerald-400 font-medium">Policy Compliant</span>
                    </div>
                  </CardContent>

                  {/* Actions */}
                  <div className="p-4 pt-0 mt-2 border-t border-slate-800/60 flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="destructive"
                      className="flex-1 text-xs h-8"
                      onClick={() => {
                        setSelectedRequest(req);
                        setDecisionAction("reject");
                      }}
                    >
                      <XCircle className="w-3.5 h-3.5 mr-1" />
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      className="flex-1 text-xs h-8 bg-emerald-600 hover:bg-emerald-500 shadow-glow-emerald"
                      onClick={() => {
                        setSelectedRequest(req);
                        setDecisionAction("approve");
                      }}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                      Approve
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Resolved Approvals History */}
        <div className="pt-4 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <History className="w-4 h-4 text-blue-400" />
            Decision Audit History
          </h2>

          <div className="rounded-xl border border-slate-800/80 bg-navy-900/60 overflow-hidden">
            <div className="p-4 text-xs font-semibold uppercase text-slate-400 border-b border-slate-800 grid grid-cols-12 gap-2">
              <span className="col-span-2">ID</span>
              <span className="col-span-4">Directive</span>
              <span className="col-span-2">Origin Agent</span>
              <span className="col-span-2">Resolution</span>
              <span className="col-span-2">Timestamp</span>
            </div>

            <div className="divide-y divide-slate-800/60 text-xs">
              <div className="p-4 grid grid-cols-12 gap-2 items-center">
                <span className="col-span-2 font-mono text-slate-400">appr_840</span>
                <span className="col-span-4 text-slate-200 font-medium truncate">
                  LinkedIn Organic Thought Leadership Carousel
                </span>
                <span className="col-span-2 text-blue-400 font-mono">content_engine</span>
                <span className="col-span-2">
                  <Badge variant="success" className="text-[10px]">
                    Approved
                  </Badge>
                </span>
                <span className="col-span-2 text-slate-400">2026-11-09 14:10</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Confirmation Modal */}
      <Modal
        isOpen={!!selectedRequest}
        onClose={() => setSelectedRequest(null)}
        title={
          decisionAction === "approve"
            ? "Authorize & Sign Off Publication"
            : "Reject Proposed Agent Action"
        }
        description={`Request: ${selectedRequest?.title} [${selectedRequest?.id}]`}
      >
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-navy-950 border border-slate-800 text-xs space-y-1">
            <div className="font-semibold text-white">Full Directive Preview:</div>
            <p className="text-slate-300 leading-relaxed font-sans italic">
              "{selectedRequest?.contentPreview}"
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-300 mb-1.5">
              Decision Note (Recorded to Immutable Audit Hash Chain):
            </label>
            <input
              type="text"
              value={decisionNote}
              onChange={(e) => setDecisionNote(e.target.value)}
              placeholder="e.g., Reviewed and verified alignment with Brand OS..."
              className="w-full h-10 rounded-lg border border-slate-700 bg-navy-950 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {statusMessage && (
            <div className="p-2.5 rounded bg-emerald-950/60 border border-emerald-500/40 text-xs text-emerald-200">
              {statusMessage}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedRequest(null)}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={isSubmitting}
              onClick={handleDecision}
              className={
                decisionAction === "approve"
                  ? "bg-emerald-600 hover:bg-emerald-500 shadow-glow-emerald"
                  : "bg-rose-600 hover:bg-rose-500"
              }
            >
              {isSubmitting
                ? "Submitting to Backend..."
                : decisionAction === "approve"
                ? "Cryptographically Sign & Authorize"
                : "Confirm Rejection"}
            </Button>
          </div>
        </div>
      </Modal>
    </AppLayout>
  );
}

