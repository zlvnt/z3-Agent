"use client";

import { cn } from "@/lib/utils";

export function SessionSelector({
  sessions,
  current,
  onSelect,
  onCreate,
  onClear,
}: {
  sessions: string[];
  current: string;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onClear: () => void;
}) {
  return (
    <div className="w-48 bg-zinc-900 border-r border-zinc-800 flex flex-col">
      <div className="p-3 border-b border-zinc-800">
        <button
          onClick={onCreate}
          className="w-full px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs rounded-lg transition-colors"
        >
          + New Session
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {sessions.map((id) => (
          <button
            key={id}
            onClick={() => onSelect(id)}
            className={cn(
              "w-full text-left px-3 py-2 rounded-lg text-xs truncate transition-colors",
              id === current
                ? "bg-zinc-800 text-white"
                : "text-zinc-400 hover:text-white hover:bg-zinc-800/50",
            )}
          >
            {id}
          </button>
        ))}
      </div>
      <div className="p-2 border-t border-zinc-800">
        <button
          onClick={onClear}
          className="w-full px-3 py-1.5 text-xs text-zinc-500 hover:text-red-400 transition-colors"
        >
          Clear Chat
        </button>
      </div>
    </div>
  );
}
