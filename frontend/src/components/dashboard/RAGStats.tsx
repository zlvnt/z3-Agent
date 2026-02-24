"use client";

import { Card } from "@/components/ui/Card";
import { formatPercent } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { MetricsResponse } from "@/lib/types";

const COLORS: Record<string, string> = {
  direct: "#3b82f6",
  docs: "#10b981",
  social: "#a855f7",
  web: "#f59e0b",
  escalate: "#ef4444",
};

export function RAGStats({ data }: { data: MetricsResponse }) {
  const { rag } = data;

  const chartData = Object.entries(rag.routing_distribution).map(
    ([name, value]) => ({ name, value }),
  );

  return (
    <Card>
      <h3 className="text-sm font-medium text-zinc-400 mb-3">
        RAG & Routing
      </h3>
      <div className="grid grid-cols-3 gap-3 mb-4 text-center">
        <div>
          <p className="text-lg font-bold text-white">{rag.total_queries}</p>
          <p className="text-xs text-zinc-500">Total Queries</p>
        </div>
        <div>
          <p className="text-lg font-bold text-emerald-400">
            {formatPercent(rag.success_rate)}
          </p>
          <p className="text-xs text-zinc-500">Success Rate</p>
        </div>
        <div>
          <p className="text-lg font-bold text-blue-400">
            {rag.most_used_mode || "-"}
          </p>
          <p className="text-xs text-zinc-500">Top Mode</p>
        </div>
      </div>
      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" tick={{ fill: "#71717a", fontSize: 11 }} />
            <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#18181b",
                border: "1px solid #27272a",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={COLORS[entry.name] || "#71717a"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
