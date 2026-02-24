"use client";

import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";

export function Header() {
  const { isOnline } = useHealth();

  return (
    <header className="h-12 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between px-4">
      <div />
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "inline-block w-2 h-2 rounded-full",
            isOnline ? "bg-emerald-400" : "bg-red-400",
          )}
        />
        <span className="text-xs text-zinc-400">
          Backend {isOnline ? "Online" : "Offline"}
        </span>
      </div>
    </header>
  );
}
