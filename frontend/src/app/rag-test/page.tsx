"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { RAGTestRequest, RAGTestResponse, DocumentResult } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { JsonViewer } from "@/components/ui/JsonViewer";

function ScoreBar({ score, max = 1 }: { score: number; max?: number }) {
  const pct = Math.max(0, Math.min(100, (score / max) * 100));
  const color =
    score >= 0.5 ? "bg-emerald-500" : score >= 0.0 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-zinc-400 w-14 text-right">{score.toFixed(4)}</span>
    </div>
  );
}

function DocCard({ doc, index }: { doc: DocumentResult; index: number }) {
  return (
    <div className="border border-zinc-800 rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-zinc-500">#{index + 1}</span>
        {doc.source && (
          <span className="text-xs text-zinc-600 truncate max-w-[200px]">{doc.source}</span>
        )}
      </div>
      {doc.reranker_score !== undefined && doc.reranker_score !== null && (
        <ScoreBar score={doc.reranker_score} />
      )}
      <p className="text-sm text-zinc-300 whitespace-pre-wrap break-words">{doc.content}</p>
    </div>
  );
}

function QualityGateBadge({ action }: { action: string }) {
  const variant =
    action === "proceed" ? "docs" : action === "proceed_with_flag" ? "direct" : "escalate";
  return <Badge variant={variant}>{action}</Badge>;
}

export default function RAGTestPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("docs");
  const [kDocs, setKDocs] = useState(7);
  const [useReranker, setUseReranker] = useState(true);
  const [rerankerTopK, setRerankerTopK] = useState(3);
  const [skipUP, setSkipUP] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RAGTestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleTest() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const req: RAGTestRequest = {
        query: query.trim(),
        mode,
        k_docs: kDocs,
        use_reranker: useReranker,
        reranker_top_k: rerankerTopK,
        skip_unified_processor: skipUP,
      };
      const res = await api.testRAG(req);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4 max-w-4xl h-full overflow-y-auto p-4">
      <h1 className="text-xl font-bold text-white">RAG Test</h1>
      <p className="text-sm text-zinc-500">
        Debug RAG pipeline step-by-step. See retrieved docs, reranker scores, and quality gate.
      </p>

      {/* Input Controls */}
      <Card>
        <div className="space-y-3">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter query to test..."
            rows={2}
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500 resize-none"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleTest();
              }
            }}
          />

          <div className="flex flex-wrap items-center gap-3">
            {/* Mode */}
            <label className="flex items-center gap-1.5 text-xs text-zinc-400">
              Mode
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-white"
              >
                <option value="docs">docs</option>
                <option value="web">web</option>
                <option value="all">all</option>
              </select>
            </label>

            {/* k_docs */}
            <label className="flex items-center gap-1.5 text-xs text-zinc-400">
              k_docs
              <input
                type="number"
                value={kDocs}
                onChange={(e) => setKDocs(Number(e.target.value))}
                min={1}
                max={50}
                className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-white w-16"
              />
            </label>

            {/* Reranker toggle */}
            <label className="flex items-center gap-1.5 text-xs text-zinc-400 cursor-pointer">
              <input
                type="checkbox"
                checked={useReranker}
                onChange={(e) => setUseReranker(e.target.checked)}
                className="rounded border-zinc-600"
              />
              Reranker
            </label>

            {/* Reranker top_k */}
            {useReranker && (
              <label className="flex items-center gap-1.5 text-xs text-zinc-400">
                top_k
                <input
                  type="number"
                  value={rerankerTopK}
                  onChange={(e) => setRerankerTopK(Number(e.target.value))}
                  min={1}
                  max={20}
                  className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-white w-16"
                />
              </label>
            )}

            {/* Skip Unified Processor */}
            <label className="flex items-center gap-1.5 text-xs text-zinc-400 cursor-pointer">
              <input
                type="checkbox"
                checked={skipUP}
                onChange={(e) => setSkipUP(e.target.checked)}
                className="rounded border-zinc-600"
              />
              Skip Unified Processor
            </label>
          </div>

          <button
            onClick={handleTest}
            disabled={loading || !query.trim()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {loading ? "Testing..." : "Run Test"}
          </button>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <Card className="border-red-500/30">
          <p className="text-sm text-red-400">{error}</p>
        </Card>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-3">
          {/* Processing time */}
          <div className="text-xs text-zinc-500 text-right">
            {result.processing_time_ms.toFixed(0)}ms
          </div>

          {/* Step 1: Unified Processor */}
          {result.unified_processor && (
            <Card>
              <h2 className="text-sm font-semibold text-zinc-300 mb-2">
                Step 1: Unified Processor
              </h2>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-500">Routing:</span>
                  <Badge variant={result.unified_processor.routing_decision as string}>
                    {result.unified_processor.routing_decision as string}
                  </Badge>
                  {result.unified_processor.escalate && (
                    <Badge variant="escalate">ESCALATE</Badge>
                  )}
                </div>
                {result.unified_processor.reformulated_query && (
                  <div className="flex gap-2">
                    <span className="text-xs text-zinc-500 shrink-0">Reformulated:</span>
                    <span className="text-sm text-zinc-300">
                      {result.unified_processor.reformulated_query as string}
                    </span>
                  </div>
                )}
                {result.unified_processor.reasoning && (
                  <div className="flex gap-2">
                    <span className="text-xs text-zinc-500 shrink-0">Reasoning:</span>
                    <span className="text-xs text-zinc-400">
                      {result.unified_processor.reasoning as string}
                    </span>
                  </div>
                )}
              </div>
              <div className="mt-2">
                <JsonViewer data={result.unified_processor} label="Raw JSON" />
              </div>
            </Card>
          )}

          {/* Step 2: Raw Documents */}
          <Card>
            <h2 className="text-sm font-semibold text-zinc-300 mb-2">
              Step 2: Retrieved Documents ({result.raw_documents.length})
            </h2>
            {result.raw_documents.length === 0 ? (
              <p className="text-xs text-zinc-500">No documents retrieved.</p>
            ) : (
              <div className="space-y-2">
                {result.raw_documents.map((doc, i) => (
                  <DocCard key={i} doc={doc} index={i} />
                ))}
              </div>
            )}
          </Card>

          {/* Step 3: Reranked Documents */}
          {result.reranked_documents.length > 0 && (
            <Card>
              <h2 className="text-sm font-semibold text-zinc-300 mb-2">
                Step 3: Reranked Documents ({result.reranked_documents.length})
              </h2>
              <div className="space-y-2">
                {result.reranked_documents.map((doc, i) => (
                  <DocCard key={i} doc={doc} index={i} />
                ))}
              </div>
            </Card>
          )}

          {/* Step 4: Quality Gate */}
          {result.quality_gate && (
            <Card>
              <h2 className="text-sm font-semibold text-zinc-300 mb-2">
                Step 4: Quality Gate
              </h2>
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <QualityGateBadge action={result.quality_gate.action as string} />
                  {result.quality_gate.top_score !== undefined && (
                    <div className="flex-1 max-w-xs">
                      <ScoreBar score={result.quality_gate.top_score as number} />
                    </div>
                  )}
                </div>
                {result.quality_gate.reasoning && (
                  <p className="text-xs text-zinc-400">
                    {result.quality_gate.reasoning as string}
                  </p>
                )}
              </div>
            </Card>
          )}

          {/* Final Context */}
          {result.final_context && (
            <Card>
              <JsonViewer data={result.final_context} label="Final Context" />
            </Card>
          )}

          {/* Config Used */}
          {Object.keys(result.config_used).length > 0 && (
            <Card>
              <JsonViewer data={result.config_used} label="Config Used" />
            </Card>
          )}

          {/* Error from backend */}
          {result.error && (
            <Card className="border-red-500/30">
              <p className="text-sm text-red-400">{result.error}</p>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
