"""
Main Conditional Chain - Graph-ready architecture untuk Instagram AI Agent.

Implements true LangChain conditional execution dengan:
- Router → RAG (conditional) → Reply 
- Structured data flow
- Memory integration
- Performance optimization
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import time

from langchain.base import BaseChain
from langchain.memory import ConversationBufferWindowMemory

from app.chains.models import (
    ChainInput,
    ChainOutput,
    RouteDecision,
    ContextSource,
    ChainError
)
from app.chains.components import (
    RouterChain,
    ContextRetrievalChain,
    ReplyGenerationChain
)
from app.chains.memory import MemoryManager


class InstagramConditionalChain(BaseChain):
    """
    Main conditional chain untuk Instagram AI Agent.
    
    Graph-ready architecture:
    - Router → Conditional RAG → Reply
    - Structured data flow dengan type safety
    - Memory integration (LangChain + JSON persistence)
    - Performance optimization
    """
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        super().__init__()
        
        # Chain components
        self.router = RouterChain()
        self.context_retrieval = ContextRetrievalChain()
        self.reply_generation = ReplyGenerationChain()
        
        # Memory management
        self.memory_manager = memory_manager or MemoryManager()
        
        print("INFO: InstagramConditionalChain initialized")
    
    @property
    def input_keys(self) -> list[str]:
        return ["chain_input"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["chain_output"]
    
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute conditional chain dengan structured data flow.
        
        Flow:
        1. Router decision
        2. Conditional context retrieval  
        3. Reply generation dengan memory
        4. Memory update
        """
        start_time = time.time()
        chain_input: ChainInput = inputs["chain_input"]
        
        try:
            # Step 1: Router Decision
            router_result = self.router.run({
                "user_input": chain_input.comment
            })
            router_output = router_result["router_output"]
            
            print(f"INFO: Chain step 1 - route: {router_output.route}")
            
            # Step 2: Conditional Context Retrieval
            context_output = None
            if router_output.needs_context:
                # Convert route to mode string untuk compatibility
                mode = self._route_to_mode(router_output.route)
                
                context_result = self.context_retrieval.run({
                    "query": chain_input.comment,
                    "mode": mode
                })
                context_output = context_result["context_output"]
                
                print(f"INFO: Chain step 2 - context retrieved: {len(context_output.chunks)} chunks")
            else:
                print("INFO: Chain step 2 - skipping context retrieval (direct route)")
            
            # Step 3: Get Memory Context
            memory_context = self.memory_manager.get_formatted_history(
                user_id=chain_input.user_id,
                post_id=chain_input.post_id,
                comment_id=chain_input.comment_id
            )
            
            # Step 4: Reply Generation
            reply_context = context_output.combined_content if context_output else ""
            
            reply_result = self.reply_generation.run({
                "comment": chain_input.comment,
                "context": reply_context,
                "history_context": memory_context,
                "username": chain_input.username
            })
            reply = reply_result["reply"]
            
            print(f"INFO: Chain step 3 - reply generated")
            
            # Step 5: Update Memory
            self.memory_manager.add_exchange(
                user_id=chain_input.user_id,
                post_id=chain_input.post_id,
                comment_id=chain_input.comment_id,
                user_message=chain_input.comment,
                ai_message=reply,
                username=chain_input.username
            )
            
            # Step 6: Create Structured Output
            processing_time = time.time() - start_time
            
            chain_output = ChainOutput(
                reply=reply,
                route_used=router_output.route,
                context_sources=context_output.sources_used if context_output else [],
                processing_time=processing_time,
                metadata={
                    "query_type": router_output.query_type,
                    "confidence": router_output.confidence,
                    "context_chunks": len(context_output.chunks) if context_output else 0
                },
                router_output=router_output,
                context_output=context_output
            )
            
            print(f"INFO: Chain completed - time: {processing_time:.2f}s, route: {router_output.route}")
            
            return {"chain_output": chain_output}
            
        except Exception as e:
            print(f"ERROR: Chain execution failed - error: {e}")
            
            # Create error output
            error_output = ChainOutput(
                reply="Maaf, sistem sedang mengalami gangguan. Silakan coba lagi nanti.",
                route_used=RouteDecision.DIRECT,
                context_sources=[],
                processing_time=time.time() - start_time,
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            return {"chain_output": error_output}
    
    def _route_to_mode(self, route: RouteDecision) -> str:
        """Convert RouteDecision to legacy mode string"""
        if route == RouteDecision.DOCS:
            return "docs"
        elif route == RouteDecision.WEB:
            return "web"  
        elif route == RouteDecision.ALL:
            return "all"
        else:
            return "docs"  # fallback
    
    def run_sync(self, chain_input: ChainInput) -> ChainOutput:
        """
        Convenient synchronous interface untuk FastAPI integration.
        """
        result = self.run({"chain_input": chain_input})
        return result["chain_output"]
    
    async def arun_async(self, chain_input: ChainInput) -> ChainOutput:
        """
        Asynchronous interface untuk future optimization.
        Currently uses sync implementation.
        """
        # Future: implement true async execution
        return self.run_sync(chain_input)
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get chain performance statistics"""
        return {
            "memory_users": self.memory_manager.get_active_users_count(),
            "components": {
                "router": self.router.__class__.__name__,
                "context_retrieval": self.context_retrieval.__class__.__name__,
                "reply_generation": self.reply_generation.__class__.__name__
            }
        }
    
    def clear_user_memory(self, user_id: str) -> bool:
        """Clear memory untuk specific user"""
        return self.memory_manager.clear_user_memory(user_id)