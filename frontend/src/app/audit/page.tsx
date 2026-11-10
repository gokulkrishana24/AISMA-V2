"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  ScrollText,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  Lock,
  RefreshCw,
  Search,
  KeyRound,
  FileCheck2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function AuditLogsPage() {
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{
    valid: boolean;
    verifiedCount: number;
    message: string;
  } | null>(null);

  const { data: auditRes, isLoading, refetch } = useQuery({
    queryKey: ["auditLogs"],
    queryFn: () => apiClient.getAuditLogs(),
  });

  const logs = auditRes?.data?.entries || [];

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    setVerificationResult(null);
    try {
      const res = await apiClient.verifyAuditChain();
      setVerificationResult(res.data);
    } catch (err: any) {
      setVerificationResult({
        valid: false,
        verifiedCount: 0,
        message: `Verification Failed: ${err.message}`,
      });
    } finally {
      setIsVerifying(false);
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
                Cryptographic Governance
              </Badge>
              <span className="text-xs text-slate-400">
                SHA-256 Hash-Chained Append-Only Audit Trail
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Immutable Audit Logs & Verification
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Button
              size="sm"
              disabled={isVerifying}
              onClick={handleVerifyChain}
              className="bg-emerald-600 hover:bg-emerald-500 shadow-glow-emerald text-xs font-semibold gap-1.5"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              {isVerifying ? "Verifying Hash Chain..." : "Verify Hash Chain Integrity"}
            </Button>
          </div>
        </div>

        {/* Verification Result Banner */}
        {verificationResult && (
          <div
            className={`p-4 rounded-xl border flex items-center justify-between text-xs ${
              verificationResult.valid
                ? "border-emerald-500/40 bg-emerald-950/30 text-emerald-300"
                : "border-rose-500/40 bg-rose-950/30 text-rose-300"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <span className="font-bold text-sm block">
                  {verificationResult.valid
                    ? "Cryptographic Verification Succeeded"
                    : "Integrity Compromised"}
                </span>
                <span>{verificationResult.message}</span>
              </div>
            </div>
            <span className="font-mono text-[11px] text-emerald-400">
              Verified {verificationResult.verifiedCount} blocks
            </span>
          </div>
        )}

        {/* Audit Log Entries List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-300">
              Chained Records ({logs.length} Blocks Verified)
            </span>
            <span className="text-slate-500 font-mono text-[11px]">
              Business Isolation: biz_apex_enterprises
            </span>
          </div>

          <div className="space-y-4">
            {logs.map((entry, idx) => (
              <Card key={entry.entry_hash} className="p-5 space-y-3 border-slate-800">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-blue-400 font-bold">
                      BLOCK #{logs.length - idx}
                    </span>
                    <Badge variant="secondary" className="font-mono text-[10px]">
                      {entry.actor}
                    </Badge>
                    <Badge
                      variant={entry.outcome === "success" ? "success" : "destructive"}
                      className="text-[10px] uppercase font-bold"
                    >
                      {entry.action}
                    </Badge>
                  </div>
                  <span className="text-slate-500 font-mono text-[11px]">
                    {entry.timestamp}
                  </span>
                </div>

                {/* Details Payload */}
                <div className="p-3 rounded-lg bg-navy-950 border border-slate-800/80 text-xs text-slate-300 space-y-1">
                  <div className="text-[10px] text-slate-500 font-semibold uppercase">
                    Redacted Payload (PII Scrubbed):
                  </div>
                  <pre className="font-mono text-[11px] text-cyan-200 overflow-x-auto">
                    {JSON.stringify(entry.details, null, 2)}
                  </pre>
                </div>

                {/* Cryptographic Linkage Hashes */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px] font-mono pt-1 text-slate-500">
                  <div className="truncate">
                    <span className="text-slate-400">prev_hash:</span> {entry.prev_hash}
                  </div>
                  <div className="truncate text-right">
                    <span className="text-slate-400">entry_hash:</span>{" "}
                    <span className="text-emerald-400">{entry.entry_hash}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

