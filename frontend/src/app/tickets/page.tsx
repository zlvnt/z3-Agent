"use client";

import { useState } from "react";
import { useTickets } from "@/hooks/useTickets";
import type { Ticket } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TicketDetail } from "@/components/tickets/TicketDetail";

const STATUS_FILTERS = [
  { value: undefined, label: "All" },
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In Progress" },
  { value: "resolved", label: "Resolved" },
  { value: "closed", label: "Closed" },
] as const;

function formatTime(iso?: string) {
  if (!iso) return "-";
  try {
    const d = new Date(iso);
    return d.toLocaleString("id-ID", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function truncate(text: string, len = 40) {
  return text.length > len ? text.slice(0, len) + "..." : text;
}

export default function TicketsPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const { tickets, stats, total, page, setPage, isLoading, error, refresh } =
    useTickets(statusFilter);

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Tickets</h1>
        <button
          onClick={refresh}
          className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm rounded-lg transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card className="text-center">
            <p className="text-2xl font-bold text-amber-400">{stats.open}</p>
            <p className="text-xs text-zinc-500">Open</p>
          </Card>
          <Card className="text-center">
            <p className="text-2xl font-bold text-blue-400">{stats.in_progress}</p>
            <p className="text-xs text-zinc-500">In Progress</p>
          </Card>
          <Card className="text-center">
            <p className="text-2xl font-bold text-emerald-400">{stats.resolved}</p>
            <p className="text-xs text-zinc-500">Resolved</p>
          </Card>
          <Card className="text-center">
            <p className="text-2xl font-bold text-zinc-400">
              {stats.avg_resolution_time_hours != null
                ? `${stats.avg_resolution_time_hours}h`
                : "-"}
            </p>
            <p className="text-xs text-zinc-500">Avg Resolution</p>
          </Card>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-1">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => {
              setStatusFilter(f.value);
              setPage(1);
              setSelectedTicket(null);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              statusFilter === f.value
                ? "bg-zinc-700 text-white"
                : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <Card className="border-red-500/30">
          <p className="text-sm text-red-400">{error}</p>
        </Card>
      )}

      {/* Table */}
      <Card className="p-0 overflow-hidden">
        {isLoading ? (
          <p className="text-sm text-zinc-500 p-4">Loading...</p>
        ) : tickets.length === 0 ? (
          <p className="text-sm text-zinc-500 p-4">No tickets found.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs text-zinc-500">
                <th className="text-left px-4 py-2">ID</th>
                <th className="text-left px-4 py-2">Time</th>
                <th className="text-left px-4 py-2">User</th>
                <th className="text-left px-4 py-2">Query</th>
                <th className="text-left px-4 py-2">Stage</th>
                <th className="text-left px-4 py-2">Status</th>
                <th className="text-left px-4 py-2">Assigned</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => setSelectedTicket(t)}
                  className={`border-b border-zinc-800/50 cursor-pointer transition-colors ${
                    selectedTicket?.id === t.id
                      ? "bg-zinc-800"
                      : "hover:bg-zinc-800/50"
                  }`}
                >
                  <td className="px-4 py-2 text-xs text-zinc-400 font-mono">
                    {t.id.slice(0, 15)}
                  </td>
                  <td className="px-4 py-2 text-xs text-zinc-400">
                    {formatTime(t.created_at)}
                  </td>
                  <td className="px-4 py-2 text-xs text-zinc-300">
                    @{t.username || t.user_id || "-"}
                  </td>
                  <td className="px-4 py-2 text-xs text-zinc-300">
                    {truncate(t.original_query)}
                  </td>
                  <td className="px-4 py-2">
                    <Badge variant={t.escalation_stage === "pre_rag" ? "direct" : "docs"}>
                      {t.escalation_stage}
                    </Badge>
                  </td>
                  <td className="px-4 py-2">
                    <Badge variant={t.status}>{t.status}</Badge>
                  </td>
                  <td className="px-4 py-2 text-xs text-zinc-400">
                    {t.assigned_to || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-1 text-xs text-zinc-400 hover:text-white disabled:text-zinc-600"
          >
            Prev
          </button>
          <span className="text-xs text-zinc-500">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 text-xs text-zinc-400 hover:text-white disabled:text-zinc-600"
          >
            Next
          </button>
        </div>
      )}

      {/* Ticket Detail */}
      {selectedTicket && (
        <TicketDetail
          ticket={selectedTicket}
          onUpdate={() => {
            refresh();
            setSelectedTicket(null);
          }}
          onClose={() => setSelectedTicket(null)}
        />
      )}
    </div>
  );
}
