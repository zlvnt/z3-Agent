"""
Data models untuk LangChain conditional chain architecture.
Foundation untuk structured communication dan type safety.
"""

from __future__ import annotations
from typing import Optional, Literal, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class RouteDecision(str, Enum):
    """Route decision types dengan clear semantics"""
    DIRECT = "direct"        # Skip RAG, direct ke reply
    DOCS = "docs"           # Use internal documentation
    WEB = "web"             # Use web search
    ALL = "all"             # Use both docs + web


class ContextSource(str, Enum):
    """Context source untuk tracking dan optimization"""
    DOCS = "docs"
    WEB = "web"
    MEMORY = "memory"


class RouterOutput(BaseModel):
    """Structured output dari routing decision"""
    route: RouteDecision = Field(description="Routing decision")
    reasoning: str = Field(description="Why this route was chosen")
    confidence: float = Field(ge=0.0, le=1.0, description="Decision confidence score")
    needs_context: bool = Field(description="Whether context retrieval is needed")
    query_type: Optional[str] = Field(default=None, description="Classified query type")
    
    class Config:
        use_enum_values = True


class ContextChunk(BaseModel):
    """Individual context chunk dengan metadata"""
    source: ContextSource
    content: str
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class ContextOutput(BaseModel):
    """Structured context retrieval output"""
    chunks: List[ContextChunk]
    total_length: int = Field(description="Total context length in chars")
    sources_used: List[ContextSource] = Field(description="Which sources were queried")
    retrieval_time: Optional[float] = None
    query: str = Field(description="Original query used for retrieval")
    
    @property
    def combined_content(self) -> str:
        """Get all context combined for LLM"""
        return "\n\n".join([
            f"[{chunk.source.upper()}] {chunk.content}"
            for chunk in self.chunks
        ])
    
    class Config:
        use_enum_values = True


class ChainInput(BaseModel):
    """Input untuk conditional chain execution"""
    comment: str
    post_id: str
    comment_id: str
    username: str
    additional_context: Optional[Dict[str, Any]] = None
    
    @property
    def user_id(self) -> str:
        """Generate user ID untuk memory management"""
        return f"{self.username}_{self.post_id}"


class ChainOutput(BaseModel):
    """Final output dari chain execution"""
    reply: str
    route_used: RouteDecision
    context_sources: List[ContextSource] = Field(default_factory=list)
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Chain execution details
    router_output: Optional[RouterOutput] = None
    context_output: Optional[ContextOutput] = None
    
    class Config:
        use_enum_values = True


class ChainError(BaseModel):
    """Structured error information"""
    error_type: str
    message: str
    component: Optional[str] = None  # router, rag, reply
    recoverable: bool = True
    timestamp: datetime = Field(default_factory=datetime.now)


class MemoryState(BaseModel):
    """Memory state untuk per-user conversation"""
    user_id: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    context_window: int = Field(default=5, description="Number of exchanges to keep")
    
    def add_exchange(self, user_msg: str, ai_msg: str):
        """Add conversation exchange"""
        self.conversation_history.append({
            "user": user_msg,
            "ai": ai_msg,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last N exchanges
        if len(self.conversation_history) > self.context_window:
            self.conversation_history = self.conversation_history[-self.context_window:]
        
        self.last_updated = datetime.now()
    
    @property
    def formatted_history(self) -> str:
        """Format history for LLM context"""
        if not self.conversation_history:
            return ""
        
        lines = ["Riwayat Percakapan Sebelumnya:"]
        for exchange in self.conversation_history:
            lines.append(f"User: {exchange['user']}")
            lines.append(f"z3: {exchange['ai']}")
        
        return "\n".join(lines)


# Type aliases untuk convenience
ChainInputType = ChainInput
ChainOutputType = ChainOutput
RouterOutputType = RouterOutput
ContextOutputType = ContextOutput