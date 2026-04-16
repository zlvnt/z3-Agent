# z3-Agent

### AI Agent for Customer Support Across Any Messaging Channel

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![Gemini](https://img.shields.io/badge/Gemini-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Unified Processor** — First LLM call for routing, query reformulation, and escalation detection
- **Reply Generation** — Second LLM call to generate final response with RAG context
- **RAG Pipeline** — FAISS vector search + BGE cross-encoder reranker
- **Quality Gate** — Confidence scoring: `proceed` / `proceed_with_flag` / `escalate`
- **HITL Ticketing** — Auto-create tickets on escalation, CS group notifications, admin panel
- **Admin Panel** — Web dashboard for chat testing, RAG debugging, ticket management, and monitoring
- **Auto-detect Database** — PostgreSQL (production) or SQLite (local dev)

## Architecture

### CS Mode Flow

```
User Message
  │
  ▼
Unified Processor — 1st LLM call (Gemini 2.5 Flash)
  ├─ routing_decision: direct | docs
  ├─ reformulated_query
  └─ escalate: true/false
      │
      ├─ [direct] ──────────────────────▶ Reply Generation — 2nd LLM call
      │
      ├─ [docs] ──▶ FAISS Retrieval ──▶ BGE Reranker ──▶ Quality Gate
      │                                                      │
      │                                    [proceed] ◀───────┤──▶ Reply Generation — 2nd LLM call
      │                                                      │
      │                              [proceed_with_flag] ◀───┤──▶ Reply Generation — 2nd LLM call
      │                                                      │
      │                                   [escalate] ◀───────┘
      │                                       │
      └─ [escalate] ─────────────────────────▶├─ User: "connecting you with CS"
                                              ├─ CS Group: Telegram notification
                                              └─ Ticket: auto-created in DB
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Uvicorn, Python 3.11 |
| **LLM** | Google Gemini 2.5 Flash (via LangChain) |
| **Embeddings** | sentence-transformers (multilingual MiniLM) |
| **Vector Store** | FAISS |
| **Reranker** | BGE cross-encoder (BAAI/bge-reranker-base) |
| **Database** | PostgreSQL 17 / SQLite (auto-detect) |
| **Frontend** | Next.js 16, React 19, Tailwind CSS |
| **Deployment** | Docker Compose, Railway-ready |

## Admin Panel

| Page | Description |
|------|-------------|
| `/chat` | Web chat interface for testing bot responses |
| `/rag-test` | RAG pipeline debugger — see each step (retrieval, reranking, quality gate) |
| `/tickets` | HITL ticket management — stats, filtering, status updates |
| `/dashboard` | Monitoring dashboard with metrics and alerts |
| `/config` | Configuration panel |

## Project Structure

```
z3-Agent/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Pydantic settings
│   ├── api/
│   │   ├── chat.py              # Web chat endpoint
│   │   ├── tickets.py           # Ticket CRUD
│   │   └── rag_test.py          # RAG test endpoint
│   ├── channels/
│   │   └── telegram/
│   │       ├── handler.py       # Message processing
│   │       ├── memory.py        # Conversation memory
│   │       ├── client.py        # Telegram API client
│   │       ├── escalation.py    # CS group notifications
│   │       └── webhook.py       # Webhook endpoints
│   ├── core/
│   │   ├── chain.py             # CoreChain
│   │   ├── unified_processor.py # Routing + reformulation
│   │   ├── rag.py               # RAG + quality gate
│   │   ├── reranker.py          # BGE cross-encoder
│   │   └── reply.py             # Reply generation
│   ├── monitoring/              # Metrics, alerts, health
│   └── services/
│       ├── vector.py            # FAISS vector store
│       └── ticket_service.py    # Ticket persistence
├── frontend/                    # Next.js admin panel
├── docs/                        # Knowledge base (markdown)
├── prompts/                     # LLM prompt templates
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
