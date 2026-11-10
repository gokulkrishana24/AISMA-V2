"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AgentDetails, AgentId } from "@/types";
import {
  Bot,
  Play,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Cpu,
  Layers,
  Shield,
  Activity,
  ArrowRight,
  Sliders,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import Link from "next/link";

export default function AgentCommandCenterPage() {
  const queryClient = useQueryClient();
  const [selectedAgent, setSelectedAgent] = useState<AgentDetails | null>(null);
  const [actionInput, setActionInput] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<string | null>(null);

  const { data: agentsRes, isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiClient.getAgents(),
  });

  const agents = agentsRes?.data || [];

  const handleExecuteTask = async () => {
    if (!selectedAgent) return;
    setIsExecuting(true);
    setExecutionResult(null);
    try {
      const res = await apiClient.triggerAgentTask(selectedAgent.id, {
        action: actionInput || "manual_routine_run",
      });
      setExecutionResult(
        `Task #${res.data.task_id} successfully dispatched to agent engine. Status: ${res.data.status}`
      );
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    } catch (err: any) {
      setExecutionResult(`Error dispatching task: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Specialized AI Fleet
              </Badge>
              <span className="text-xs text-slate-400">
                8 Dedicated Local Inference Agents
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Agent Command Center
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              All Agents Synchronized
            </span>
          </div>
        </div>

        {/* 8 Agent Command Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {agents.map((agent) => {
            const isRunning = agent.status === "running";
            const isError = agent.errorCount > 0 && agent.status === "error";

            return (
              <Card
                key={agent.id}
                className="flex flex-col justify-between hover:border-blue-500/50 transition-all duration-300 group"
              >
                <div>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <span className="font-mono text-[10px] text-blue-400 uppercase tracking-widest font-bold">
                          {agent.codename}
                        </span>
                        <CardTitle className="text-lg font-bold text-white group-hover:text-blue-300 transition-colors">
                          {agent.name}
                        </CardTitle>
                      </div>

                      <Badge
                        variant={
                          agent.status === "active"
                            ? "success"
                            : agent.status === "running"
                            ? "cyan"
                            : "secondary"
                        }
                        className="text-[10px] uppercase font-bold"
                      >
                        <span
                          className={`h-1.5 w-1.5 rounded-full mr-1.5 ${
                            agent.status === "active"
                              ? "bg-emerald-400 animate-pulse"
                              : agent.status === "running"
                              ? "bg-cyan-400 animate-ping"
                              : "bg-slate-400"
                          }`}
                        />
                        {agent.status}
                      </Badge>
                    </div>

                    <CardDescription className="text-xs line-clamp-2 mt-2">
                      {agent.description}
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-3 pt-0">
                    {/* Live Task Status Box */}
                    <div className="p-2.5 rounded-lg border border-slate-800 bg-navy-950/70 text-xs space-y-1">
                      <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold flex items-center justify-between">
                        <span>Current Activity</span>
                        <span className="text-slate-400 flex items-center gap-1 font-mono">
                          <Clock className="w-3 h-3" />
                          {new Date(agent.lastExecution).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      <p className="text-slate-300 font-medium text-[11px] line-clamp-2">
                        {agent.currentTask || "Idle / Monitoring schedule"}
                      </p>
                    </div>

                    {/* Output Summary */}
                    {agent.lastOutputSummary && (
                      <div className="text-[11px] text-slate-400 border-l-2 border-blue-500/60 pl-2 italic">
                        "{agent.lastOutputSummary}"
                      </div>
                    )}

                    {/* Agent Metrics Grid */}
                    <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/80">
                      <div className="p-1.5 rounded bg-navy-950/40">
                        <span className="text-[10px] text-slate-500 block">
                          Success Rate
                        </span>
                        <span className="text-xs font-bold text-white">
                          {agent.successRate}%
                        </span>
                      </div>
                      <div className="p-1.5 rounded bg-navy-950/40">
                        <span className="text-[10px] text-slate-500 block">
                          Executions
                        </span>
                        <span className="text-xs font-bold text-white">
                          {agent.totalExecutions}
                        </span>
                      </div>
                    </div>

                    {/* Errors if any */}
                    {agent.errorCount > 0 && (
                      <div className="flex items-center gap-1.5 text-[11px] text-amber-400/90 pt-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>{agent.errorCount} non-fatal retries logged</span>
                      </div>
                    )}
                  </CardContent>
                </div>

                {/* Footer Actions */}
                <div className="p-4 pt-0 mt-3 border-t border-slate-800/60 flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 text-xs h-8 border-slate-700"
                    onClick={() => {
                      setSelectedAgent(agent);
                      setActionInput("");
                      setExecutionResult(null);
                    }}
                  >
                    <Play className="w-3 h-3 mr-1 text-blue-400" />
                    Trigger
                  </Button>

                  <Link
                    href={`/agents/${agent.id.replace("_", "-")}`}
                    className="flex-1"
                  >
                    <Button
                      size="sm"
                      className="w-full text-xs h-8 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30"
                    >
                      Telemetry
                      <ArrowRight className="w-3 h-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Manual Task Dispatch Modal */}
      <Modal
        isOpen={!!selectedAgent}
        onClose={() => setSelectedAgent(null)}
        title={`Trigger Execution: ${selectedAgent?.name}`}
        description={`Codename: ${selectedAgent?.codename} | Model: ${selectedAgent?.config.model}`}
      >
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-navy-950/80 border border-slate-800 text-xs text-slate-300 space-y-1">
            <div className="font-semibold text-white">Governance Verification:</div>
            <p>
              Execution will be checked against backend permissions and logged to the SHA-256 hash chain with business isolation enforcement.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-300 mb-1.5">
              Task Directive / Action Name
            </label>
            <input
              type="text"
              value={actionInput}
              onChange={(e) => setActionInput(e.target.value)}
              placeholder="e.g. recalibrate_matrix, generate_batch, score_sentiment"
              className="w-full h-10 rounded-lg border border-slate-700 bg-navy-950 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {executionResult && (
            <div className="p-3 rounded-lg bg-blue-950/40 border border-blue-500/40 text-xs text-blue-200">
              {executionResult}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedAgent(null)}
            >
              Close
            </Button>
            <Button
              size="sm"
              disabled={isExecuting}
              onClick={handleExecuteTask}
              className="bg-blue-600 hover:bg-blue-500 shadow-glow-blue"
            >
              {isExecuting ? "Executing in Backend..." : "Dispatch to Agent Fleet"}
            </Button>
          </div>
        </div>
      </Modal>
    </AppLayout>
  );
}

