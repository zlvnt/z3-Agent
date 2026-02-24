"use client";

import { useMetrics } from "@/hooks/useMetrics";
import { MetricsOverview } from "@/components/dashboard/MetricsOverview";
import { RAGStats } from "@/components/dashboard/RAGStats";
import { RecentRequests } from "@/components/dashboard/RecentRequests";
import { AlertStatus } from "@/components/dashboard/AlertStatus";

export default function DashboardPage() {
  const { metrics, isLoading, error, lastUpdated, refresh } = useMetrics();

  if (isLoading && !metrics) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-zinc-500">Loading metrics...</p>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-red-400 mb-2">{error}</p>
          <button
            onClick={refresh}
            className="text-sm text-zinc-400 hover:text-white"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Dashboard</h2>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-zinc-500">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={refresh}
            className="text-xs text-zinc-400 hover:text-white px-2 py-1 bg-zinc-800 rounded-lg transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      <MetricsOverview data={metrics} />

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <RAGStats data={metrics} />
        </div>
        <AlertStatus data={metrics} />
      </div>

      <RecentRequests />
    </div>
  );
}
