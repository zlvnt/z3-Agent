# Instagram AI Agent - Project Memory

## Project Structure
- **Main App**: `app/main.py` - FastAPI application
- **Agents**: `app/agents/` - Router, reply, RAG systems
- **Services**: `app/services/` - Instagram API, logging, conversation
- **API**: `app/api/` - Webhook endpoints
- **Config**: `app/config.py` - Pydantic settings

## Environment Configuration
- **Required vars**: INSTAGRAM_ACCESS_TOKEN, GEMINI_API_KEY, MODEL_NAME, VERIFY_TOKEN
- **Model**: Currently using `gemini-2.0-flash`
- **Important**: Avoid duplicate env vars in `.env` file

## Common Commands
```bash
# Start development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Debug mode
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload
```

## Known Issues & Solutions

### FastAPI Startup Hang ("Waiting for application startup")
**Solved**: Issue was in `app/services/logger.py` - structlog configuration without exception handling

**Root causes**:
1. Structlog configuration hang in `setup_logging()`
2. Duplicate environment variables in `.env`
3. Missing exception handling in logger initialization

**Solution applied**:
- Added try-catch in `setup_logging()` with fallback to basic logging
- Removed duplicate env vars
- Added `disable_existing_loggers: False` in dictConfig
- Simplified startup lifecycle

**Fixed files**:
- `app/services/logger.py`: Added exception handling
- `app/main.py`: Simplified lifespan function
- `.env`: Removed duplicates

## Troubleshooting Tips
1. Always check for duplicate environment variables
2. Use debug logging: `LOG_LEVEL=DEBUG`
3. Check required files exist: `content/*.txt`, `content/*.json`
4. If startup hangs, check logger configuration first

## Development Notes
- Bot username: `z3_agent` (prevents self-reply loops)
- Uses lazy loading for LLM initialization via `@lru_cache`
- Conversation history stored in `data/conversations.json`
- Vector store in `data/vector_store/`