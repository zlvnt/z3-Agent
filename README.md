# z3-Agent

**Multi-Channel AI Agent for Intelligent Customer Service**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-purple.svg)
![AI/ML](https://img.shields.io/badge/AI%2FML-Gemini-orange.svg)

---

## Overview

**z3-Agent** is an AI-powered customer service and social media agent built on FastAPI and Gemini. Currently deployed on Telegram, with architecture ready for additional channels.

The system supports two operational modes:
- **Social Mode**: Casual social media replies without RAG
- **CS Mode**: Full customer service with intelligent routing, RAG retrieval, quality gates, and human escalation

In CS mode, a Unified Processor analyzes each message in a single LLM call to determine:
- **Routing decision**: Direct reply or documentation search
- **Query reformulation**: Optimized query for better retrieval
- **Escalation check**: Flag for human handoff when needed

Built with clean channel-based architecture, making it straightforward to add support for additional messaging platforms.

**Current status**: Telegram active in production. Instagram channels ready but disabled (requires Meta Advanced Access).

---

## Key Features

### 🤖 Multi-Channel Support
Instagram and Telegram integration through unified channel abstraction. Each platform has dedicated processing while sharing core intelligence systems.

### 🧠 Intelligent Routing System
Supervisor agent analyzes every query to determine optimal response strategy: direct reply for casual chat, documentation search for technical questions, web search for current events, or combined approach for complex queries.

### 📚 Documentation-Grounded Responses
Vector-based semantic search on internal documentation retrieves relevant context to ground LLM responses in factual information—reducing hallucinations and improving accuracy.

### 💬 Conversation Memory
Channel-specific memory systems maintain conversation context with appropriate storage for each platform's needs.

### 📊 Comprehensive Monitoring
Real-time metrics tracking, automatic Telegram alerts for critical issues, Streamlit dashboard, and health check endpoints for external integration.

### ⚡ Performance Optimizations
Singleton pattern for chain instances, lazy loading, async processing, and efficient vector search operations.

---

## Architecture

### High-Level Flow

```
User Message → Webhook → Channel Handler → Core Chain → Response
                                              ↓
                                    ┌─────────┴─────────┐
                                    ↓                   ↓
                          Unified Processor    Conversation Memory
                          (Route + Reformulate)
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              Direct Reply    Doc Retrieval    Web Search
                                    ↓
                              Reranker + Quality Gate
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
              Reply Generation              Escalation (if needed)
                    ↓
              Send via Channel API
```

### Core Components

#### **Channels Layer**
Provides platform abstraction with unified interface. Each channel implements message processing, data extraction, API integration, and thread management. Enables adding new platforms with minimal code.

#### **Core Processing**
Shared intelligence layer across all channels:
- **Unified Processor**: Single LLM call for routing decision, query reformulation, and escalation check
- **RAG System**: Semantic search with BGE reranker for high-precision context retrieval
- **Quality Gate**: Evaluates retrieval quality and triggers escalation when confidence is low
- **Reply Generator**: Combines context and history for natural, grounded responses

Shared core ensures consistent behavior and makes improvements benefit all channels.

#### **Monitoring System**
Observability built from the start with metrics collection, automatic alerts, real-time dashboard, and structured logging. Detect issues immediately and understand user patterns.

#### **Storage & Memory**
Vector store for documentation search, and channel-specific conversation storage optimized for each platform's requirements.

---

## Tech Stack

### **LLM: Google Gemini**
Fast inference, native Indonesian and English support, cost-effective for sustained usage, large context window for extensive documentation.

### **Embeddings: Local Models (HuggingFace)**
Zero per-request costs, works offline without external dependencies, privacy-preserving with local processing, multilingual support.

### **Reranker: BGE Cross-Encoder**
Two-stage retrieval with initial vector search followed by cross-encoder reranking for high-precision results.

### **Framework: LangChain**
Standard patterns for chains and memory, seamless integration with vector stores and LLMs, built-in monitoring callbacks, clear path for future enhancements.

### **Backend: FastAPI**
Async native for efficient webhook processing, type safety with Pydantic, high performance for I/O workloads, auto-generated documentation.

### **Vector Database: FAISS**
Optimized for fast similarity search, local file-based storage, flexible index types, native Python integration.

### **Monitoring: Custom + Streamlit**
Lightweight solution for early-stage systems, integrated metrics collection, immediate alert notifications, intuitive real-time dashboard.

---

### Design Philosophy

**Layer separation**: Clear boundaries between channels, core processing, and services ensure changes in one area don't affect others.

**Shared intelligence**: Router, RAG, and reply logic are shared so all channels benefit from improvements.

**Configuration as code**: Prompts and personality in version-controlled files enable rapid iteration without code changes.

**Data isolation**: Each channel uses appropriate storage for its needs.

**Observability first-class**: Monitoring is integrated from the start, not bolted on later.

---

## Monitoring & Observability

The system includes comprehensive monitoring with real-time metrics tracking (requests, errors, performance, user activity), automatic Telegram alerts for critical issues, Streamlit dashboard for live system overview, and health check endpoints for external integrations.

Alerts trigger when error rates exceed 10% or response times exceed 5 seconds, with cooldown to prevent spam.

---

## Current Status

### ✅ Working Features
- Multi-channel support (Instagram, Telegram) with unified interface
- Unified Processor for routing, reformulation, and escalation in single LLM call
- RAG with reranker and quality gates for high-precision retrieval
- Human-in-the-loop escalation when retrieval confidence is low
- Conversation memory with channel-specific storage
- Async webhook processing with background tasks
- Monitoring with Telegram alerts and Streamlit dashboard
- Configuration via environment variables (Pydantic Settings)
- Railway deployment ready with optimized Docker image

### 🚧 In Development
Webhook signature verification, HITL ticketing integration, load testing.

### 🎯 Future Plans
Additional channels (WhatsApp, Discord), advanced analytics, response caching, A/B testing, fine-tuned embeddings.

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Built with clean architecture and production patterns for scalable customer service automation.**