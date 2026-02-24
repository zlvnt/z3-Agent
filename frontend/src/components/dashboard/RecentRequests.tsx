"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/utils";
import type { RequestLogEntry } from "@/lib/types";

export function RecentRequests() {
  const [requests, setRequests] = useState<RequestLogEntry[]>([]);

  useEffect(() => {
    const load = () => {
      api
        .getRecentRequests()
        .then((d) => setRequests(d.recent_requests || []))
        .catch(() => {});
    };
    load();
    const id = setInterval(load, 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <Card>
      <h3 className="text-sm font-medium text-zinc-400 mb-3">
        Recent Requests
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-zinc-500 border-b border-zinc-800">
              <th className="text-left py-2 pr-3">Time</th>
              <th className="text-left py-2 pr-3">Channel</th>
              <th className="text-left py-2 pr-3">User</th>
              <th className="text-left py-2 pr-3">Query</th>
              <th className="text-left py-2 pr-3">Route</th>
              <th className="text-right py-2">Duration</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r, i) => (
              <tr
                key={i}
                className="border-b border-zinc-800/50 text-zinc-300"
              >
                <td className="py-1.5 pr-3 text-zinc-500 whitespace-nowrap">
                  {new Date(r.timestamp).toLocaleTimeString()}
                </td>
                <td className="py-1.5 pr-3">{r.channel}</td>
                <td className="py-1.5 pr-3 truncate max-w-[100px]">
                  {r.username}
                </td>
                <td className="py-1.5 pr-3 truncate max-w-[200px]">
                  {r.query}
                </td>
                <td className="py-1.5 pr-3">
                  <Badge variant={r.routing_mode}>{r.routing_mode}</Badge>
                </td>
                <td className="py-1.5 text-right text-zinc-500">
                  {formatDuration(r.duration * 1000)}
                </td>
              </tr>
            ))}
            {requests.length === 0 && (
              <tr>
                <td colSpan={6} className="py-4 text-center text-zinc-600">
                  No recent requests
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
