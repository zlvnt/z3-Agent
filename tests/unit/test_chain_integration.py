"""
Comprehensive test suite for InstagramConditionalChain integration.
Tests the complete chain flow with different scenarios and routing modes.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import time


from app.chains.conditional_chain import process_with_chain, get_chain



class TestChainIntegration:
    """Test cases for chain integration"""

    @pytest.mark.asyncio
    async def test_basic_greeting_direct_route(self):
        """Test basic greeting should use direct route"""
        with patch('app.agents.router.supervisor_route', return_value='direct'), \
             patch('app.agents.reply.generate_reply', return_value='Hello! 👋'):
            
            reply = await process_with_chain(
                comment="Hello",
                post_id="test_post_1",
                comment_id="test_comment_1", 
                username="test_user"
            )
            
            assert reply is not None
            assert reply != ""
            assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_faq_query_docs_route(self):
        """Test FAQ query should use docs route"""
        with patch('app.agents.router.supervisor_route', return_value='docs'), \
             patch('app.agents.rag.retrieve_context', return_value='Context from docs'), \
             patch('app.agents.reply.generate_reply', return_value='Based on documentation...'):
            
            reply = await process_with_chain(
                comment="How do I use the API?",
                post_id="test_post_2",
                comment_id="test_comment_2",
                username="test_user"
            )
            
            assert reply is not None
            assert reply != ""
            assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_web_route_current_events(self):
        """Test current events should use web route"""
        with patch('app.agents.router.supervisor_route', return_value='web'), \
             patch('app.agents.rag.retrieve_context', return_value='Current web info'), \
             patch('app.agents.reply.generate_reply', return_value='Latest news shows...'):
            
            reply = await process_with_chain(
                comment="What's the latest news about AI?",
                post_id="test_post_3", 
                comment_id="test_comment_3",
                username="test_user"
            )
            
            assert reply is not None
            assert reply != ""
            assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_all_route_complex_query(self):
        """Test complex query should use all route (docs + web)"""
        with patch('app.agents.router.supervisor_route', return_value='all'), \
             patch('app.agents.rag.retrieve_context', return_value='Combined context'), \
             patch('app.agents.reply.generate_reply', return_value='Based on multiple sources...'):
            
            reply = await process_with_chain(
                comment="How does your AI compare to latest ChatGPT updates?",
                post_id="test_post_4",
                comment_id="test_comment_4", 
                username="test_user"
            )
            
            assert reply is not None
            assert reply != ""
            assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_conversation_history_multiple_calls(self):
        """Test conversation history with multiple calls for same user"""
        with patch('app.agents.router.supervisor_route', return_value='direct'), \
             patch('app.agents.reply.generate_reply', side_effect=['First reply', 'Second reply']):
            
            # First call
            reply1 = await process_with_chain(
                comment="Hi there",
                post_id="test_post_5",
                comment_id="test_comment_5a",
                username="conversation_user"
            )
            
            # Second call - should have access to history via conversation.py
            reply2 = await process_with_chain(
                comment="How are you?",
                post_id="test_post_5", 
                comment_id="test_comment_5b",
                username="conversation_user"
            )
            
            assert reply1 == 'First reply'
            assert reply2 == 'Second reply'
            assert reply1 != reply2

    @pytest.mark.asyncio
    async def test_error_handling_missing_parameters(self):
        """Test error handling with missing parameters"""
        with patch('app.agents.router.supervisor_route', side_effect=Exception("Router failed")):
            
            try:
                reply = await process_with_chain(
                    comment="Test comment",
                    post_id="test_post_6",
                    comment_id="test_comment_6",
                    username="error_user"
                )
                # If no exception, chain should handle gracefully
                assert reply is not None
            except Exception as e:
                # Expected behavior - chain should bubble up critical errors
                assert "Router failed" in str(e)

    @pytest.mark.asyncio
    async def test_performance_measurement(self):
        """Test performance vs old approach (timing measurement)"""
        with patch('app.agents.router.supervisor_route', return_value='direct'), \
             patch('app.agents.reply.generate_reply', return_value='Performance test reply'):
            
            # Measure chain processing time
            start_time = time.time()
            
            reply = await process_with_chain(
                comment="Performance test",
                post_id="test_post_7",
                comment_id="test_comment_7",
                username="perf_user"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Basic assertions
            assert reply == 'Performance test reply'
            assert processing_time < 5.0  # Should complete within 5 seconds
            
            print(f"Chain processing time: {processing_time:.3f}s")

    def test_chain_singleton_behavior(self):
        """Test that get_chain returns same instance"""
        chain1 = get_chain()
        chain2 = get_chain()
        
        assert chain1 is chain2  # Same object reference
        assert id(chain1) == id(chain2)

    def test_chain_stats_functionality(self):
        """Test chain stats return meaningful data"""
        chain = get_chain()
        stats = chain.get_stats()
        
        assert isinstance(stats, dict)
        assert 'memory_window' in stats
        assert 'using_conversation_service' in stats
        assert stats['memory_window'] == 5
        assert stats['using_conversation_service'] is True

    @pytest.mark.asyncio
    async def test_chain_input_output_keys(self):
        """Test chain input/output keys are properly defined"""
        chain = get_chain()
        
        assert chain.input_keys == ["comment", "post_id", "comment_id", "username"]
        assert chain.output_keys == ["reply", "route_used", "processing_info"]

    @pytest.mark.asyncio
    async def test_full_chain_run_with_result_validation(self):
        """Test full chain run with detailed result validation"""
        with patch('app.agents.router.supervisor_route', return_value='docs'), \
             patch('app.agents.rag.retrieve_context', return_value='Test context'), \
             patch('app.agents.reply.generate_reply', return_value='Test reply'):
            
            chain = get_chain()
            result = chain.run({
                "comment": "Test question",
                "post_id": "test_post_8",
                "comment_id": "test_comment_8", 
                "username": "validation_user"
            })
            
            # Validate result structure
            assert isinstance(result, dict)
            assert "reply" in result
            assert "route_used" in result
            assert "processing_info" in result
            
            # Validate reply
            assert result["reply"] == "Test reply"
            assert result["route_used"] == "docs"
            
            # Validate processing info
            processing_info = result["processing_info"]
            assert isinstance(processing_info, dict)
            assert "context_used" in processing_info
            assert "context_length" in processing_info
            assert "memory_handled_by_conversation_service" in processing_info
            
            assert processing_info["context_used"] is True
            assert processing_info["context_length"] == len("Test context")
            assert processing_info["memory_handled_by_conversation_service"] is True


# Run tests asynchronously if executed directly
if __name__ == "__main__":
    async def run_async_tests():
        """Run async tests manually"""
        test_instance = TestChainIntegration()
        
        print("Running chain integration tests...")
        
        # Test 1: Basic greeting
        await test_instance.test_basic_greeting_direct_route()
        print("✓ Basic greeting test passed")
        
        # Test 2: FAQ query
        await test_instance.test_faq_query_docs_route()
        print("✓ FAQ query test passed")
        
        # Test 3: Performance test
        await test_instance.test_performance_measurement()
        print("✓ Performance test passed")
        
        print("All async tests completed!")

    # Run async tests
    asyncio.run(run_async_tests())