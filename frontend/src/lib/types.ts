// Chat
export interface ChatRequest {
  message: string;
  session_id: string;
}

export interface ChatResponse {
  reply: string;
  routing_decision: string;
  escalated: boolean;
  reformulated_query?: string;
  quality_score?: number;
  flagged_for_review?: boolean;
  escalation_reason?: string;
  escalation_stage?: string;
  error?: string;
  session_id: string;
  agent_mode: string;
  processing_time_ms: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: ChatResponse;
}

// Metrics
export interface MetricsResponse {
  summary: {
    total_requests: number;
    total_errors: number;
    error_rate: number;
    avg_response_time: number;
    uptime_seconds: number;
  };
  recent_activity: {
    requests_last_minute: number;
    requests_last_hour: number;
    errors_last_minute: number;
    errors_last_hour: number;
  };
  channels: Record<
    string,
    {
      requests: number;
      errors: number;
      error_rate: number;
      avg_response_time: number;
      requests_last_hour: number;
      errors_last_hour: number;
    }
  >;
  users: {
    unique_users_today: number;
    repeat_users_today: number;
    total_user_sessions: number;
    avg_requests_per_user: number;
  };
  rag: {
    total_queries: number;
    success_rate: number;
    routing_distribution: Record<string, number>;
    most_used_mode: string;
  };
  errors: {
    total_errors: number;
    categories: Record<string, number>;
    most_common_error?: string;
  };
  alerts: {
    high_error_rate: boolean;
    slow_response: boolean;
    error_rate_value: number;
    avg_response_time_value: number;
    requests_last_hour: number;
  };
}

// Health
export interface HealthResponse {
  status: string;
  timestamp: number;
  uptime_seconds: number;
  version: string;
}

// Config
export interface AgentConfig {
  agent_mode: string;
  model_name: string;
  embedding_model: string;
  use_reranker: boolean;
  reranker_model: string;
  reranker_top_k: number;
  retrieval_k: number;
  chunk_size: number;
  chunk_overlap: number;
  quality_gate_threshold_good: number;
  quality_gate_threshold_medium: number;
  use_unified_processor: boolean;
  reply_temperature: number;
  unified_processor_temperature: number;
  relevance_threshold: number;
  enable_adaptive_fallback: boolean;
}

// RAG Test
export interface RAGTestRequest {
  query: string;
  mode?: string;
  k_docs?: number;
  use_reranker?: boolean;
  reranker_top_k?: number;
  skip_unified_processor?: boolean;
}

export interface DocumentResult {
  content: string;
  source?: string;
  reranker_score?: number;
}

export interface RAGTestResponse {
  unified_processor?: Record<string, unknown>;
  raw_documents: DocumentResult[];
  reranked_documents: DocumentResult[];
  quality_gate?: Record<string, unknown>;
  final_context: string;
  config_used: Record<string, unknown>;
  processing_time_ms: number;
  error?: string;
}

// Request Log
export interface RequestLogEntry {
  timestamp: string;
  channel: string;
  username: string;
  query: string;
  routing_mode: string;
  duration: number;
  success: boolean;
  error?: string;
}
