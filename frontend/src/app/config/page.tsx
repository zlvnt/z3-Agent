"use client";

import { useConfig } from "@/hooks/useConfig";
import { Card } from "@/components/ui/Card";

const SECTIONS: Record<string, { label: string; keys: string[] }> = {
  agent: {
    label: "Agent",
    keys: ["agent_mode", "model_name", "reply_temperature"],
  },
  rag: {
    label: "RAG",
    keys: [
      "embedding_model",
      "retrieval_k",
      "chunk_size",
      "chunk_overlap",
      "relevance_threshold",
      "enable_adaptive_fallback",
    ],
  },
  reranker: {
    label: "Reranker",
    keys: ["use_reranker", "reranker_model", "reranker_top_k"],
  },
  quality_gate: {
    label: "Quality Gate",
    keys: ["quality_gate_threshold_good", "quality_gate_threshold_medium"],
  },
  processor: {
    label: "Unified Processor",
    keys: ["use_unified_processor", "unified_processor_temperature"],
  },
};

function formatValue(v: unknown): string {
  if (typeof v === "boolean") return v ? "Enabled" : "Disabled";
  return String(v);
}

export default function ConfigPage() {
  const { config, isLoading, error } = useConfig();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-zinc-500">Loading config...</p>
      </div>
    );
  }

  if (error || !config) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-400">{error || "Failed to load config"}</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <h2 className="text-lg font-semibold text-white">Configuration</h2>
      <div className="grid grid-cols-2 gap-4">
        {Object.entries(SECTIONS).map(([key, section]) => (
          <Card key={key}>
            <h3 className="text-sm font-medium text-zinc-400 mb-3">
              {section.label}
            </h3>
            <div className="space-y-2">
              {section.keys.map((k) => {
                const val = (config as unknown as Record<string, unknown>)[k];
                return (
                  <div
                    key={k}
                    className="flex items-center justify-between text-xs"
                  >
                    <span className="text-zinc-500 font-mono">{k}</span>
                    <span className="text-zinc-200 font-medium">
                      {formatValue(val)}
                    </span>
                  </div>
                );
              })}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
