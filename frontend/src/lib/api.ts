import type {
  ChatRequest,
  ChatResponse,
  MetricsResponse,
  HealthResponse,
  AgentConfig,
  RequestLogEntry,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  sendMessage(req: ChatRequest): Promise<ChatResponse> {
    return request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  getMetrics(): Promise<MetricsResponse> {
    return request<MetricsResponse>("/metrics");
  },

  getRecentRequests(): Promise<{ recent_requests: RequestLogEntry[] }> {
    return request("/metrics/requests");
  },

  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  },

  getConfig(): Promise<AgentConfig> {
    return request<AgentConfig>("/api/config");
  },
};
