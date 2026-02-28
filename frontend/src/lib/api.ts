import type {
  ChatRequest,
  ChatResponse,
  MetricsResponse,
  HealthResponse,
  AgentConfig,
  RequestLogEntry,
  RAGTestRequest,
  RAGTestResponse,
  TicketListResponse,
  TicketUpdateRequest,
  TicketStats,
  Ticket,
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

  testRAG(req: RAGTestRequest): Promise<RAGTestResponse> {
    return request<RAGTestResponse>("/api/rag/test", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  listTickets(params?: { status?: string; page?: number; page_size?: number }): Promise<TicketListResponse> {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.page) qs.set("page", String(params.page));
    if (params?.page_size) qs.set("page_size", String(params.page_size));
    return request<TicketListResponse>(`/api/tickets?${qs.toString()}`);
  },

  getTicketStats(): Promise<TicketStats> {
    return request<TicketStats>("/api/tickets/stats");
  },

  getTicket(id: string): Promise<Ticket> {
    return request<Ticket>(`/api/tickets/${id}`);
  },

  updateTicket(id: string, data: TicketUpdateRequest): Promise<Ticket> {
    return request<Ticket>(`/api/tickets/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};
