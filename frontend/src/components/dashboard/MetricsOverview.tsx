"use client";

import { MetricCard } from "./MetricCard";
import { formatPercent, formatDuration, formatUptime } from "@/lib/utils";
import type { MetricsResponse } from "@/lib/types";

export function MetricsOverview({ data }: { data: MetricsResponse }) {
  const { summary, recent_activity } = data;

  const errorColor =
    summary.error_rate > 0.1
      ? "text-red-400"
      : summary.error_rate > 0.05
        ? "text-yellow-400"
        : "text-emerald-400";

  const rtColor =
    summary.avg_response_time > 5
      ? "text-red-400"
      : summary.avg_response_time > 2
        ? "text-yellow-400"
        : "text-emerald-400";

  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard
        label="Total Requests"
        value={summary.total_requests.toLocaleString()}
        sub={`${recent_activity.requests_last_hour}/hr`}
      />
      <MetricCard
        label="Error Rate"
        value={formatPercent(summary.error_rate)}
        sub={`${summary.total_errors} errors`}
        color={errorColor}
      />
      <MetricCard
        label="Avg Response Time"
        value={formatDuration(summary.avg_response_time * 1000)}
        color={rtColor}
      />
      <MetricCard
        label="Uptime"
        value={formatUptime(summary.uptime_seconds)}
      />
    </div>
  );
}
