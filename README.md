# z3-Agent

**Multi-Channel AI Agent for Intelligent Customer Service**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-purple.svg)
![AI/ML](https://img.shields.io/badge/AI%2FML-Gemini-orange.svg)

---

## Overview

**z3-Agent** is a multi-channel AI customer service agent that handles conversations across Instagram and Telegram. It uses intelligent routing to deliver context-aware responses by combining large language models, internal documentation search, and real-time web information.

The system analyzes each incoming message through a supervisor agent that determines the optimal response strategy:
- **Direct reply** for greetings and casual conversation
- **Documentation search** for technical questions using semantic retrieval
- **Web search** for current events and recent information
- **Combined approach** for complex, multi-faceted queries

Built with a clean channel-based architecture, z3-Agent makes it straightforward to add support for additional messaging platforms. The system includes comprehensive monitoring, alerting, and observability features.

**Current capabilities**: Handles Instagram Direct Messages and Telegram conversations with conversation memory, intelligent routing, and real-time monitoring.

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
User Message → Webhook → Channel Handler → Core Chain → Intelligence Layer → Response
                                              ↓
                                    ┌─────────┴─────────┐
                                    ↓                   ↓
                            Router Decision      Conversation Memory
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              Direct Reply    Doc Retrieval    Web Search
                    │               │               │
                    └───────────────┴───────────────┘
                                    ↓
                            Reply Generation → Send via Channel API
```

### Core Components

#### **Channels Layer**
Provides platform abstraction with unified interface. Each channel implements message processing, data extraction, API integration, and thread management. Enables adding new platforms with minimal code.

#### **Core Processing**
Shared intelligence layer across all channels:
- **Router**: Analyzes queries to determine optimal processing strategy
- **RAG System**: Searches documentation and retrieves relevant context  
- **Reply Generator**: Combines context and history for natural responses

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

### **Framework: LangChain**
Standard patterns for chains and memory, seamless integration with vector stores and LLMs, built-in monitoring callbacks, clear path for future enhancements.

### **Backend: FastAPI**
Async native for efficient webhook processing, type safety with Pydantic, high performance for I/O workloads, auto-generated documentation.

### **Vector Database: FAISS**
Optimized for fast similarity search, local file-based storage, flexible index types, native Python integration.

### **Monitoring: Custom + Streamlit**
Lightweight solution for early-stage systems, integrated metrics collection, immediate alert notifications, intuitive real-time dashboard.

---

## Project Structure

```
z3-agent/
├── app/
│   ├── channels/          # Platform integrations (Instagram, Telegram)
│   ├── core/              # Shared AI processing (router, RAG, reply)
│   ├── monitoring/        # Metrics, alerts, dashboard
│   └── services/          # Utilities and external APIs
├── content/               # Prompts and bot configuration
├── docs/                  # Knowledge base for RAG
└── data/                  # Runtime storage (conversations, vectors)
```

### Design Philosophy

**Layer separation**: Clear boundaries between channels, core processing, and services ensure changes in one area don't affect others.

**Shared intelligence**: Router, RAG, and reply logic are shared so all channels benefit from improvements.

**Configuration as code**: Prompts and personality in version-controlled files enable rapid iteration without code changes.

**Data isolation**: Each channel uses appropriate storage for its needs.

**Observability first-class**: Monitoring is integrated from the start, not bolted on later.

---

## Design Decisions

### Why Channel Abstraction?
Adding new messaging platforms shouldn't require rewriting core AI logic. Base interface defines the contract for message processing while each platform shares core components. Result: new platform support requires minimal code with no risk of breaking existing channels.

### Why Local Embeddings?
Cloud-based embedding APIs add per-request costs that scale with usage. Local embedding models run on your infrastructure with one-time setup. Result: zero ongoing API costs, no rate limits, complete privacy. Trade-off is slightly lower quality vs. commercial APIs, but still effective for most use cases.

### Why Built-in Monitoring?
Systems often fail silently without proper observability, making debugging difficult. Metrics collection integrated from day one with automatic alerting and visual dashboard. Result: issues detected immediately with context for rapid debugging.

---

## Monitoring & Observability

The system includes comprehensive monitoring with real-time metrics tracking (requests, errors, performance, user activity), automatic Telegram alerts for critical issues, Streamlit dashboard for live system overview, and health check endpoints for external integrations.

Alerts trigger when error rates exceed 10% or response times exceed 5 seconds, with cooldown to prevent spam.

---

## Current Status

### ✅ Working Features
Core functionality complete: multi-channel support (Instagram, Telegram), intelligent routing, RAG-powered responses, conversation memory, async webhook processing, monitoring with alerts and dashboard, error handling with graceful degradation.

### 🚧 In Development
Webhook security hardening, deployment optimization, load testing under realistic conditions.

### 🎯 Future Plans
Additional channel support (WhatsApp, Discord), advanced analytics (retention, quality scoring), response caching, A/B testing framework, domain-specific embedding fine-tuning.

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Built with clean architecture and production patterns for scalable customer service automation.**