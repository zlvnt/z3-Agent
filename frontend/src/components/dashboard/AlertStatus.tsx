import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import type { MetricsResponse } from "@/lib/types";

export function AlertStatus({ data }: { data: MetricsResponse }) {
  const { alerts } = data;
  const hasAlerts = alerts.high_error_rate || alerts.slow_response;

  return (
    <Card>
      <h3 className="text-sm font-medium text-zinc-400 mb-3">Alerts</h3>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-400">Error Rate</span>
          <span
            className={cn(
              "text-xs font-medium",
              alerts.high_error_rate ? "text-red-400" : "text-emerald-400",
            )}
          >
            {alerts.high_error_rate ? "TRIGGERED" : "OK"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-400">Response Time</span>
          <span
            className={cn(
              "text-xs font-medium",
              alerts.slow_response ? "text-red-400" : "text-emerald-400",
            )}
          >
            {alerts.slow_response ? "TRIGGERED" : "OK"}
          </span>
        </div>
        {!hasAlerts && (
          <p className="text-xs text-emerald-400/60 mt-2">All systems normal</p>
        )}
      </div>
    </Card>
  );
}
