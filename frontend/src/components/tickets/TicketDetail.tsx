"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { Ticket } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

function formatTime(iso?: string) {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleString("id-ID", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function TicketDetail({
  ticket,
  onUpdate,
  onClose,
}: {
  ticket: Ticket;
  onUpdate: () => void;
  onClose: () => void;
}) {
  const [status, setStatus] = useState(ticket.status);
  const [assignedTo, setAssignedTo] = useState(ticket.assigned_to || "");
  const [resolutionNote, setResolutionNote] = useState(ticket.resolution_note || "");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await api.updateTicket(ticket.id, {
        status: status !== ticket.status ? status : undefined,
        assigned_to: assignedTo !== (ticket.assigned_to || "") ? assignedTo : undefined,
        resolution_note: resolutionNote !== (ticket.resolution_note || "") ? resolutionNote : undefined,
      });
      onUpdate();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to update");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">{ticket.id}</h3>
        <button
          onClick={onClose}
          className="text-xs text-zinc-500 hover:text-zinc-300"
        >
          Close
        </button>
      </div>

      {/* Info */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <span className="text-zinc-500">User:</span>{" "}
          <span className="text-zinc-300">@{ticket.username || ticket.user_id || "-"}</span>
        </div>
        <div>
          <span className="text-zinc-500">Channel:</span>{" "}
          <span className="text-zinc-300">{ticket.channel}</span>
        </div>
        <div>
          <span className="text-zinc-500">Stage:</span>{" "}
          <Badge variant={ticket.escalation_stage === "pre_rag" ? "direct" : "docs"}>
            {ticket.escalation_stage}
          </Badge>
        </div>
        <div>
          <span className="text-zinc-500">Score:</span>{" "}
          <span className="text-zinc-300">
            {ticket.quality_score != null ? ticket.quality_score.toFixed(4) : "-"}
          </span>
        </div>
        <div>
          <span className="text-zinc-500">Created:</span>{" "}
          <span className="text-zinc-300">{formatTime(ticket.created_at)}</span>
        </div>
        <div>
          <span className="text-zinc-500">Resolved:</span>{" "}
          <span className="text-zinc-300">{formatTime(ticket.resolved_at)}</span>
        </div>
      </div>

      {/* Query */}
      <div>
        <span className="text-xs text-zinc-500">Query:</span>
        <p className="text-sm text-zinc-300 mt-1">{ticket.original_query}</p>
      </div>

      {/* Reason */}
      <div>
        <span className="text-xs text-zinc-500">Escalation Reason:</span>
        <p className="text-sm text-zinc-300 mt-1">{ticket.escalation_reason}</p>
      </div>

      {/* History */}
      {ticket.history_snippet && (
        <div>
          <span className="text-xs text-zinc-500">History:</span>
          <pre className="text-xs text-zinc-400 mt-1 bg-zinc-950 rounded p-2 max-h-32 overflow-y-auto whitespace-pre-wrap">
            {ticket.history_snippet}
          </pre>
        </div>
      )}

      {/* Edit Form */}
      <div className="border-t border-zinc-800 pt-3 space-y-3">
        <div className="flex gap-3">
          <label className="flex-1">
            <span className="text-xs text-zinc-500">Status</span>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as Ticket["status"])}
              className="w-full mt-1 bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-white"
            >
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </label>
          <label className="flex-1">
            <span className="text-xs text-zinc-500">Assigned To</span>
            <input
              type="text"
              value={assignedTo}
              onChange={(e) => setAssignedTo(e.target.value)}
              placeholder="CS agent name"
              className="w-full mt-1 bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-white placeholder-zinc-600"
            />
          </label>
        </div>

        <label>
          <span className="text-xs text-zinc-500">Resolution Note</span>
          <textarea
            value={resolutionNote}
            onChange={(e) => setResolutionNote(e.target.value)}
            rows={2}
            placeholder="How was this resolved?"
            className="w-full mt-1 bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-white placeholder-zinc-600 resize-none"
          />
        </label>

        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {saving ? "Saving..." : "Save"}
        </button>
      </div>
    </Card>
  );
}
