"use client";

import { useState } from "react";

export function JsonViewer({ data, label = "Raw JSON" }: { data: unknown; label?: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
      >
        {open ? "▾" : "▸"} {label}
      </button>
      {open && (
        <pre className="mt-1 p-2 bg-zinc-950 rounded text-xs text-zinc-400 overflow-x-auto max-h-64 overflow-y-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
