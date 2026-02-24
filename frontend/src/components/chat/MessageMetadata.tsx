"use client";

import { Badge } from "@/components/ui/Badge";
import { JsonViewer } from "@/components/ui/JsonViewer";
import { formatDuration } from "@/lib/utils";
import type { ChatResponse } from "@/lib/types";

export function MessageMetadata({ data }: { data: ChatResponse }) {
  const scoreColor =
    data.quality_score == null
      ? "bg-zinc-600"
      : data.quality_score >= 0.5
        ? "bg-emerald-500"
        : data.quality_score >= 0
          ? "bg-yellow-500"
          : "bg-red-500";

  return (
    <div className="mt-2 space-y-2 text-xs">
      {/* Badges row */}
      <div className="flex flex-wrap gap-1.5">
        <Badge variant={data.routing_decision}>{data.routing_decision}</Badge>
        <Badge variant="default">{data.agent_mode}</Badge>
        <Badge variant="default">{formatDuration(data.processing_time_ms)}</Badge>
        {data.escalated && <Badge variant="escalate">ESCALATED</Badge>}
        {data.flagged_for_review && <Badge variant="escalate">FLAGGED</Badge>}
      </div>

      {/* Quality score bar */}
      {data.quality_score != null && (
        <div>
          <span className="text-zinc-500">Quality Score: </span>
          <span className="text-zinc-300">{data.quality_score.toFixed(3)}</span>
          <div className="mt-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${scoreColor}`}
              style={{ width: `${Math.max(0, Math.min(100, (data.quality_score + 1) * 50))}%` }}
            />
          </div>
        </div>
      )}

      {/* Reformulated query */}
      {data.reformulated_query && (
        <div>
          <span className="text-zinc-500">Reformulated: </span>
          <span className="text-zinc-300 font-mono">{data.reformulated_query}</span>
        </div>
      )}

      {/* Escalation */}
      {data.escalation_reason && (
        <div>
          <span className="text-zinc-500">Escalation: </span>
          <span className="text-red-300">{data.escalation_reason}</span>
          {data.escalation_stage && (
            <span className="text-zinc-500"> ({data.escalation_stage})</span>
          )}
        </div>
      )}

      {/* Error */}
      {data.error && (
        <div className="text-red-400">Error: {data.error}</div>
      )}

      <JsonViewer data={data} />
    </div>
  );
}
