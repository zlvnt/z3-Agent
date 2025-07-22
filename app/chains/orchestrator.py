"""
Chain Orchestrator untuk FastAPI Integration.

Provides:
- Single entry point untuk chain execution
- Error handling dan recovery
- Performance monitoring
- Graceful fallback to legacy system
"""

from __future__ import annotations
from typing import Optional, Dict, Any
import time
import asyncio
from contextlib import asynccontextmanager

from app.chains.models import ChainInput, ChainOutput, ChainError
from app.chains.conditional import InstagramConditionalChain
from app.chains.memory import MemoryManager
from app.services.logger import logger


class ChainOrchestrator:
    """
    Orchestrator untuk managing chain execution dengan FastAPI integration.
    
    Features:
    - Singleton pattern untuk resource management
    - Graceful degradation ke legacy system
    - Performance monitoring
    - Memory management
    """
    
    _instance: Optional['ChainOrchestrator'] = None
    
    def __new__(cls) -> 'ChainOrchestrator':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.memory_manager = MemoryManager()
        self.chain = InstagramConditionalChain(memory_manager=self.memory_manager)
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "fallback_requests": 0
        }
        
        print("INFO: ChainOrchestrator initialized")
    
    async def process_comment(
        self,
        comment: str,
        post_id: str,
        comment_id: str,
        username: str,
        **kwargs: Any
    ) -> str:
        """
        Main entry point untuk processing Instagram comments.
        
        Returns: Reply string (for compatibility dengan existing webhook)
        """
        start_time = time.time()
        self._stats["total_requests"] += 1
        
        try:
            # Create chain input
            chain_input = ChainInput(
                comment=comment,
                post_id=post_id,
                comment_id=comment_id,
                username=username,
                additional_context=kwargs
            )
            
            # Execute chain
            chain_output = await self._execute_chain_with_fallback(chain_input)
            
            # Update stats
            processing_time = time.time() - start_time
            self._stats["successful_requests"] += 1
            self._stats["total_processing_time"] += processing_time
            
            print(f"INFO: Comment processed successfully - time: {processing_time:.2f}s, route: {chain_output.route_used}")
            
            return chain_output.reply
            
        except Exception as e:
            # Update stats
            processing_time = time.time() - start_time
            self._stats["failed_requests"] += 1
            self._stats["total_processing_time"] += processing_time
            
            print(f"ERROR: Comment processing failed - error: {e}, time: {processing_time:.2f}s")
            
            # Final fallback
            return await self._emergency_fallback(comment, username)
    
    async def _execute_chain_with_fallback(self, chain_input: ChainInput) -> ChainOutput:
        """
        Execute chain dengan fallback ke legacy system jika diperlukan.
        """
        try:
            # Try new chain system
            chain_output = await self.chain.arun_async(chain_input)
            return chain_output
            
        except Exception as e:
            print(f"WARNING: Chain execution failed, falling back to legacy system: {e}")
            self._stats["fallback_requests"] += 1
            
            # Fallback to legacy system
            return await self._legacy_fallback(chain_input)
    
    async def _legacy_fallback(self, chain_input: ChainInput) -> ChainOutput:
        """
        Fallback ke legacy system (existing router.handle).
        Wraps legacy response dalam ChainOutput format.
        """
        try:
            # Import legacy system
            from app.agents.router import handle as legacy_handle
            
            # Execute legacy handler
            reply = await asyncio.get_event_loop().run_in_executor(
                None,
                legacy_handle,
                chain_input.comment,
                chain_input.post_id,
                chain_input.comment_id,
                chain_input.username
            )
            
            # Wrap dalam ChainOutput format
            from app.chains.models import RouteDecision
            
            chain_output = ChainOutput(
                reply=reply,
                route_used=RouteDecision.DIRECT,  # Unknown route dari legacy
                context_sources=[],
                processing_time=None,
                metadata={
                    "source": "legacy_fallback",
                    "fallback_reason": "chain_execution_failed"
                }
            )
            
            print("INFO: Legacy fallback executed successfully")
            return chain_output
            
        except Exception as e:
            print(f"ERROR: Legacy fallback also failed: {e}")
            raise
    
    async def _emergency_fallback(self, comment: str, username: str) -> str:
        """Final emergency fallback jika semua sistem gagal"""
        error_messages = [
            f"Halo {username}, maaf sistem sedang mengalami gangguan teknis.",
            "Silakan coba lagi dalam beberapa saat atau hubungi customer service kami.",
            "Terima kasih atas pengertiannya! 🙏"
        ]
        
        return " ".join(error_messages)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        avg_processing_time = (
            self._stats["total_processing_time"] / max(self._stats["total_requests"], 1)
        )
        
        return {
            "requests": self._stats["total_requests"],
            "success_rate": self._stats["successful_requests"] / max(self._stats["total_requests"], 1),
            "fallback_rate": self._stats["fallback_requests"] / max(self._stats["total_requests"], 1),
            "avg_processing_time": avg_processing_time,
            "chain_stats": self.chain.get_chain_stats(),
            "memory_stats": self.memory_manager.get_memory_stats()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check untuk monitoring"""
        try:
            # Test basic chain components
            router_healthy = self.chain.router is not None
            context_healthy = self.chain.context_retrieval is not None
            reply_healthy = self.chain.reply_generation is not None
            memory_healthy = self.memory_manager is not None
            
            overall_healthy = all([
                router_healthy, 
                context_healthy, 
                reply_healthy, 
                memory_healthy
            ])
            
            return {
                "status": "healthy" if overall_healthy else "degraded",
                "components": {
                    "router": "healthy" if router_healthy else "error",
                    "context_retrieval": "healthy" if context_healthy else "error",
                    "reply_generation": "healthy" if reply_healthy else "error",
                    "memory": "healthy" if memory_healthy else "error"
                },
                "stats": self.get_stats()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "components": {"all": "error"}
            }
    
    def cleanup_memory(self) -> None:
        """Manual memory cleanup"""
        try:
            self.memory_manager.cleanup_old_memories()
            print("INFO: Memory cleanup completed")
        except Exception as e:
            print(f"ERROR: Memory cleanup failed: {e}")
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        try:
            print("INFO: ChainOrchestrator shutting down...")
            
            # Cleanup memory
            self.cleanup_memory()
            
            # Log final stats
            final_stats = self.get_stats()
            print(f"INFO: Final stats - requests: {final_stats['requests']}, success_rate: {final_stats['success_rate']:.2%}")
            
            print("INFO: ChainOrchestrator shutdown completed")
            
        except Exception as e:
            print(f"ERROR: Shutdown failed: {e}")


# Global orchestrator instance
_global_orchestrator: Optional[ChainOrchestrator] = None


def get_orchestrator() -> ChainOrchestrator:
    """Get global orchestrator instance"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = ChainOrchestrator()
    return _global_orchestrator


async def process_instagram_comment(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    **kwargs: Any
) -> str:
    """
    Convenient function untuk processing Instagram comments.
    
    Drop-in replacement untuk legacy router.handle function.
    """
    orchestrator = get_orchestrator()
    return await orchestrator.process_comment(
        comment=comment,
        post_id=post_id,
        comment_id=comment_id,
        username=username,
        **kwargs
    )


@asynccontextmanager
async def orchestrator_lifespan():
    """Context manager untuk orchestrator lifecycle"""
    orchestrator = get_orchestrator()
    try:
        print("INFO: Orchestrator lifecycle started")
        yield orchestrator
    finally:
        await orchestrator.shutdown()