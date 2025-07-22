"""
Individual chain components dengan structured output.
Transform existing agents ke LangChain-compatible components.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import time
from pathlib import Path

from langchain.base import BaseChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from functools import lru_cache

from app.config import settings
from app.chains.models import (
    RouterOutput, 
    ContextOutput, 
    ContextChunk,
    RouteDecision,
    ContextSource,
    ChainError
)
from app.agents.rag import retrieve_context as _legacy_retrieve_context
from app.prompt.personality import persona_intro, rules_txt


class RouterChain(BaseChain):
    """Enhanced router with structured output"""
    
    def __init__(self):
        super().__init__()
        self._prompt = ChatPromptTemplate.from_template(
            Path(settings.SUPERVISOR_PROMPT_PATH).read_text(encoding="utf-8")
        )
    
    @property
    def input_keys(self) -> list[str]:
        return ["user_input"]
    
    @property 
    def output_keys(self) -> list[str]:
        return ["router_output"]
    
    @lru_cache(maxsize=1)
    def _get_llm(self) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=0,
            google_api_key=settings.GEMINI_API_KEY,
        )
    
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute routing decision dengan structured output"""
        start_time = time.time()
        user_input = inputs["user_input"]
        
        try:
            # Get LLM decision
            msg = self._prompt.format_messages(user_input=user_input)
            decision = self._get_llm().invoke(msg).content.strip().lower()
            
            # Parse decision to structured format
            route, reasoning, confidence = self._parse_decision(decision, user_input)
            needs_context = route != RouteDecision.DIRECT
            
            # Classify query type untuk monitoring
            query_type = self._classify_query_type(user_input)
            
            router_output = RouterOutput(
                route=route,
                reasoning=reasoning,
                confidence=confidence,
                needs_context=needs_context,
                query_type=query_type
            )
            
            print(f"INFO: Router decision - route: {route}, confidence: {confidence:.2f}")
            
            return {"router_output": router_output}
            
        except Exception as e:
            print(f"ERROR: Router failed - error: {e}")
            # Fallback ke DIRECT route
            fallback_output = RouterOutput(
                route=RouteDecision.DIRECT,
                reasoning=f"Router failed, fallback to direct: {str(e)}",
                confidence=0.1,
                needs_context=False,
                query_type="error_fallback"
            )
            return {"router_output": fallback_output}
    
    def _parse_decision(self, decision: str, user_input: str) -> tuple[RouteDecision, str, float]:
        """Parse LLM decision to structured format"""
        
        # Route mapping dengan confidence scoring
        if decision.startswith(("internal_doc", "rag")):
            return (
                RouteDecision.DOCS,
                "Query membutuhkan internal documentation",
                0.8
            )
        elif decision.startswith(("web_search", "websearch")):
            return (
                RouteDecision.WEB, 
                "Query membutuhkan web search",
                0.7
            )
        elif decision.startswith("all"):
            return (
                RouteDecision.ALL,
                "Query membutuhkan docs + web search",
                0.9
            )
        else:
            return (
                RouteDecision.DIRECT,
                "Query dapat dijawab langsung tanpa context",
                0.6
            )
    
    def _classify_query_type(self, user_input: str) -> str:
        """Simple query type classification for monitoring"""
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ["return", "refund", "kembalikan"]):
            return "return_policy"
        elif any(word in input_lower for word in ["login", "akun", "masuk"]):
            return "account_issue"
        elif any(word in input_lower for word in ["customer", "service", "kontak"]):
            return "contact_info"
        elif any(word in input_lower for word in ["voucher", "diskon", "promo"]):
            return "promotion"
        elif any(word in input_lower for word in ["pembayaran", "bayar", "transfer"]):
            return "payment"
        else:
            return "general"


class ContextRetrievalChain(BaseChain):
    """Enhanced context retrieval dengan structured output"""
    
    @property
    def input_keys(self) -> list[str]:
        return ["query", "mode"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["context_output"]
    
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute context retrieval dengan structured output"""
        start_time = time.time()
        query = inputs["query"]
        mode = inputs["mode"]
        
        try:
            # Use legacy retrieve_context but structure the output
            raw_context = _legacy_retrieve_context(
                query=query,
                mode=mode,
                k_docs=3,
                k_web=3,
                max_len=2000,
                relevance_threshold=0.8
            )
            
            # Parse raw context to structured format
            chunks = self._parse_context_to_chunks(raw_context, mode)
            sources_used = self._determine_sources_used(mode, chunks)
            
            context_output = ContextOutput(
                chunks=chunks,
                total_length=len(raw_context),
                sources_used=sources_used,
                retrieval_time=time.time() - start_time,
                query=query
            )
            
            print(f"INFO: Context retrieved - chunks: {len(chunks)}, length: {context_output.total_length}")
            
            return {"context_output": context_output}
            
        except Exception as e:
            print(f"ERROR: Context retrieval failed - error: {e}")
            # Return empty context
            empty_context = ContextOutput(
                chunks=[],
                total_length=0,
                sources_used=[],
                retrieval_time=time.time() - start_time,
                query=query
            )
            return {"context_output": empty_context}
    
    def _parse_context_to_chunks(self, raw_context: str, mode: str) -> list[ContextChunk]:
        """Parse raw context string to structured chunks"""
        if not raw_context:
            return []
        
        chunks = []
        
        # Split by source markers
        sections = raw_context.split('\n\n')
        
        for section in sections:
            if not section.strip():
                continue
                
            # Determine source from marker
            if section.startswith('[Docs]'):
                source = ContextSource.DOCS
                content = section.replace('[Docs]', '').strip()
            elif section.startswith('[Web]'):
                source = ContextSource.WEB  
                content = section.replace('[Web]', '').strip()
            else:
                # Default based on mode
                source = ContextSource.DOCS if mode == "docs" else ContextSource.WEB
                content = section.strip()
            
            if content:
                chunks.append(ContextChunk(
                    source=source,
                    content=content,
                    relevance_score=None,  # Could add scoring here
                    metadata={"mode": mode}
                ))
        
        return chunks
    
    def _determine_sources_used(self, mode: str, chunks: list[ContextChunk]) -> list[ContextSource]:
        """Determine which sources were actually used"""
        sources = set()
        for chunk in chunks:
            sources.add(chunk.source)
        return list(sources)


class ReplyGenerationChain(BaseChain):
    """Enhanced reply generation dengan conversation memory"""
    
    def __init__(self):
        super().__init__()
        self._prompt = ChatPromptTemplate.from_template(
            Path(settings.REPLY_PROMPT_PATH).read_text(encoding="utf-8")
        )
    
    @property
    def input_keys(self) -> list[str]:
        return ["comment", "context", "history_context", "username"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["reply"]
    
    @lru_cache(maxsize=1) 
    def _get_llm(self) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=0.7,
            google_api_key=settings.GEMINI_API_KEY,
        )
    
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reply dengan structured context"""
        comment = inputs["comment"]
        context = inputs.get("context", "")
        history_context = inputs.get("history_context", "")
        username = inputs.get("username", "User")
        
        try:
            # Combine context
            context_final = "\n".join([history_context, context]).strip()
            
            # Generate reply
            messages = self._prompt.format_messages(
                persona_intro=persona_intro(),
                rules=rules_txt(),
                comment=comment,
                context=context_final,
            )
            
            ai_msg = self._get_llm().invoke(messages)
            reply = ai_msg.content.strip()
            
            print(f"INFO: Generated reply from LLM - user: {username}")
            
            return {"reply": reply}
            
        except Exception as e:
            print(f"ERROR: Reply generation failed - error: {e}")
            fallback_reply = "Maaf, sistem sedang mengalami gangguan. Silakan coba lagi nanti."
            return {"reply": fallback_reply}