"""
Interactive Agent Chat Terminal - ENHANCED with Chain Testing
Usage: python test_agents.py

Features:
- Real-time agent orchestration testing (LEGACY)
- NEW: Chain system testing and comparison
- Step-by-step routing, context, and reply visualization  
- Interactive chat interface like ChatGPT/Claude
- Performance comparison between Legacy vs Chain
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import asyncio
import time

# Legacy imports
from app.agents.router import handle, supervisor_route
from app.agents.reply import generate_reply
from app.agents.rag import retrieve_context

# NEW: Chain imports
from app.chains.conditional_chain import process_with_chain, get_chain

def test_supervisor_routing():
    """Test supervisor decision making"""
    print("🤖 Testing Supervisor Routing...")
    
    test_cases = [
        "Halo apa kabar?",
        "Bagaimana cara menggunakan fitur X?",
        "Apa berita terbaru tentang AI?", 
        "Jelaskan dokumentasi tentang API",
        "Cara install Python yang benar?",
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n{i}. Input: '{query}'")
        route = supervisor_route(query)
        print(f"   Route: {route}")

def test_rag_retrieval():
    """Test RAG context retrieval"""
    print("\n🔍 Testing RAG Retrieval...")
    
    test_queries = [
        "dokumentasi API",
        "cara install",
        "berita AI terbaru"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        
        # Test docs mode
        docs_context = retrieve_context(query, mode="docs", k_docs=2)
        print(f"   Docs context length: {len(docs_context)}")
        
        # Test web mode  
        web_context = retrieve_context(query, mode="web", k_web=2)
        print(f"   Web context length: {len(web_context)}")

def test_reply_generation():
    """Test reply generation"""
    print("\n💬 Testing Reply Generation...")
    
    test_case = {
        "comment": "Halo, apa kabar?",
        "post_id": "test_post_123", 
        "comment_id": "test_comment_456",
        "username": "test_user",
        "context": ""
    }
    
    print(f"Comment: '{test_case['comment']}'")
    reply = generate_reply(**test_case)
    print(f"Reply: '{reply}'")

# NEW: Chain testing functions
async def test_chain_basic():
    """Test basic chain functionality"""
    print("\n🔗 Testing Chain Basic Functionality...")
    
    test_cases = [
        {
            "comment": "Halo apa kabar?",
            "description": "Simple greeting"
        },
        {
            "comment": "Bagaimana cara return barang?",
            "description": "Documentation query"
        },
        {
            "comment": "Berita AI terbaru apa?",
            "description": "Web search query"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['description']}")
        print(f"   Input: '{test['comment']}'")
        
        try:
            start_time = time.time()
            reply = await process_with_chain(
                comment=test['comment'],
                post_id=f"test_post_{i}",
                comment_id=f"test_comment_{i}",
                username="test_user"
            )
            processing_time = time.time() - start_time
            
            print(f"   Reply: '{reply}'")
            print(f"   Time: {processing_time:.3f}s")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_chain_vs_legacy_comparison():
    """Compare Chain vs Legacy performance and results"""
    print("\n⚔️  Testing Chain vs Legacy Comparison...")
    
    test_cases = [
        "Halo, apa kabar hari ini?",
        "Bagaimana cara menggunakan API?",
        "Apa berita terbaru tentang AI?"
    ]
    
    for i, comment in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 COMPARISON TEST {i}")
        print(f"Query: '{comment}'")
        print(f"{'='*60}")
        
        # Test Legacy System
        print("\n🏛️  LEGACY SYSTEM:")
        try:
            start_time = time.time()
            legacy_reply = handle(
                comment=comment,
                post_id=f"legacy_post_{i}",
                comment_id=f"legacy_comment_{i}",
                username="test_user"
            )
            legacy_time = time.time() - start_time
            
            print(f"   Reply: '{legacy_reply}'")
            print(f"   Time: {legacy_time:.3f}s")
            print(f"   Length: {len(legacy_reply)} chars")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            legacy_reply = None
            legacy_time = None
        
        # Test Chain System
        print("\n🔗 CHAIN SYSTEM:")
        try:
            start_time = time.time()
            chain_reply = await process_with_chain(
                comment=comment,
                post_id=f"chain_post_{i}",
                comment_id=f"chain_comment_{i}",
                username="test_user"
            )
            chain_time = time.time() - start_time
            
            print(f"   Reply: '{chain_reply}'")
            print(f"   Time: {chain_time:.3f}s")
            print(f"   Length: {len(chain_reply)} chars")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            chain_reply = None
            chain_time = None
        
        # Comparison Summary
        print(f"\n📊 COMPARISON SUMMARY:")
        if legacy_time and chain_time:
            if chain_time < legacy_time:
                print(f"   ⚡ Chain is {legacy_time/chain_time:.1f}x faster")
            else:
                print(f"   ⚡ Legacy is {chain_time/legacy_time:.1f}x faster")
        
        if legacy_reply and chain_reply:
            similarity = "Similar" if abs(len(legacy_reply) - len(chain_reply)) < 50 else "Different"
            print(f"   📝 Response similarity: {similarity}")

async def test_chain_detailed_orchestration():
    """Test chain with detailed step visualization"""
    print("\n🔍 Testing Chain Detailed Orchestration...")
    
    test_scenarios = [
        {
            "comment": "Halo, apa kabar hari ini?",
            "post_id": "chain_post_001",
            "comment_id": "chain_comment_001", 
            "username": "user1",
            "description": "Simple greeting - should route to direct"
        },
        {
            "comment": "Bagaimana cara menggunakan API Instagram?",
            "post_id": "chain_post_002", 
            "comment_id": "chain_comment_002",
            "username": "user2",
            "description": "Technical question - should route to docs"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"🧪 CHAIN SCENARIO {i}: {scenario['description']}")
        print(f"{'='*60}")
        print(f"👤 User: {scenario['username']}")
        print(f"💬 Comment: '{scenario['comment']}'")
        print()
        
        try:
            # Get chain instance
            chain = get_chain()
            print("🔗 Chain instance retrieved")
            print(f"   Stats: {chain.get_stats()}")
            print()
            
            # Test chain execution with detailed result
            start_time = time.time()
            result = chain.run({
                "comment": scenario['comment'],
                "post_id": scenario['post_id'],
                "comment_id": scenario['comment_id'],
                "username": scenario['username']
            })
            processing_time = time.time() - start_time
            
            print("📊 CHAIN EXECUTION RESULT:")
            print(f"   Reply: '{result['reply']}'")
            print(f"   Route Used: {result['route_used']}")
            print(f"   Processing Info: {result['processing_info']}")
            print(f"   Processing Time: {processing_time:.3f}s")
            
        except Exception as e:
            print(f"❌ Error in chain scenario {i}: {e}")
            import traceback
            traceback.print_exc()

def test_detailed_orchestration():
    """Test LEGACY orchestration with detailed step-by-step tracing"""
    print("\n🎯 Testing Detailed LEGACY Agent Orchestration...")
    
    test_scenarios = [
        {
            "comment": "Halo, apa kabar hari ini?",
            "post_id": "post_001",
            "comment_id": "comment_001", 
            "username": "user1",
            "description": "Simple greeting - should route to direct"
        },
        {
            "comment": "Bagaimana cara menggunakan API Instagram?",
            "post_id": "post_002", 
            "comment_id": "comment_002",
            "username": "user2",
            "description": "Technical question - should route to docs"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"🧪 LEGACY SCENARIO {i}: {scenario['description']}")
        print(f"{'='*60}")
        print(f"👤 User: {scenario['username']}")
        print(f"💬 Comment: '{scenario['comment']}'")
        print()
        
        try:
            # Step 1: Supervisor Decision
            print("🤖 STEP 1: Supervisor Routing Decision")
            route = supervisor_route(scenario['comment'])
            print(f"   Decision: {route}")
            print()
            
            # Step 2: Context Retrieval (if needed)
            context = ""
            if route in {"docs", "web", "all"}:
                print(f"🔍 STEP 2: Context Retrieval (mode: {route})")
                context = retrieve_context(scenario['comment'], mode=route)
                print(f"   Context length: {len(context)} characters")
                if context:
                    print("   Context preview:")
                    preview = context[:300] + "..." if len(context) > 300 else context
                    print(f"   {preview}")
                else:
                    print("   No context found")
                print()
            else:
                print("🔍 STEP 2: No context retrieval needed (direct mode)")
                print()
            
            # Step 3: Final Reply Generation
            print("💭 STEP 3: Reply Generation")
            reply = generate_reply(
                comment=scenario['comment'],
                post_id=scenario['post_id'],
                comment_id=scenario['comment_id'],
                username=scenario['username'],
                context=context
            )
            print(f"   Final Reply: '{reply}'")
            print()
            
            # Summary
            print("📊 LEGACY ORCHESTRATION SUMMARY:")
            print(f"   Route: {route}")
            print(f"   Context Used: {'Yes' if context else 'No'}")
            print(f"   Reply Length: {len(reply)} characters")
            
        except Exception as e:
            print(f"❌ Error in legacy scenario {i}: {e}")
            import traceback
            traceback.print_exc()

def test_full_orchestration():
    """Test end-to-end LEGACY agent flow using handle() function"""
    print("\n🎯 Testing Full LEGACY Agent Orchestration (via handle())...")
    
    test_scenarios = [
        {
            "comment": "Halo, apa kabar hari ini?",
            "post_id": "post_001",
            "comment_id": "comment_001", 
            "username": "user1"
        },
        {
            "comment": "Bagaimana cara menggunakan API Instagram?",
            "post_id": "post_002", 
            "comment_id": "comment_002",
            "username": "user2"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Legacy Scenario {i} ---")
        print(f"User: {scenario['username']}")
        print(f"Comment: '{scenario['comment']}'")
        
        try:
            reply = handle(**scenario)
            print(f"Legacy Bot Reply: '{reply}'")
        except Exception as e:
            print(f"❌ Error: {e}")

async def interactive_chain_chat():
    """NEW: Interactive chat using Chain system"""
    print("🔗 Instagram AI Agent - CHAIN Interactive Chat Terminal")
    print("=" * 60)
    print("Features:")
    print("  • Real-time CHAIN orchestration")
    print("  • Automatic routing with Chain system")
    print("  • Memory management via Chain")
    print("  • Type 'exit', 'quit', or 'bye' to exit")
    print("  • Type 'legacy' to switch to legacy mode")
    print("  • Type 'compare' to compare both systems")
    print("=" * 60)
    print()
    
    session_id = f"chain_session_{int(time.time())}"
    conversation_count = 0
    
    try:
        while True:
            conversation_count += 1
            
            # User input
            user_input = input(f"👤 You: ").strip()
            
            if not user_input:
                continue
                
            # Exit commands
            if user_input.lower() in ['exit', 'quit', 'bye', 'keluar']:
                print("\n👋 Sampai jumpa! Thanks for testing the CHAIN!")
                break
            
            # Switch to legacy mode
            if user_input.lower() == 'legacy':
                print("\n🔄 Switching to legacy mode...")
                interactive_chat()  # Call legacy function
                break
            
            # Compare mode
            if user_input.lower() == 'compare':
                print("\n⚔️  Running comparison...")
                await test_single_comparison(user_input)
                continue
            
            print()
            print("🔗 Chain Processing...")
            print("-" * 40)
            
            try:
                start_time = time.time()
                
                reply = await process_with_chain(
                    comment=user_input,
                    post_id=session_id,
                    comment_id=f"msg_{conversation_count}",
                    username="chain_user"
                )
                
                processing_time = time.time() - start_time
                
                print(f"🎉 [CHAIN RESULT]")
                print(f"💬 Chain Agent: {reply}")
                print(f"⏱️  Processing time: {processing_time:.3f}s")
                
            except Exception as e:
                print(f"❌ Chain error: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "="*60 + "\n")
            
    except KeyboardInterrupt:
        print("\n\n⚡ Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

async def test_single_comparison(user_input):
    """Compare single query between Chain and Legacy"""
    print(f"\n⚔️  COMPARING: '{user_input}'")
    print("-" * 50)
    
    # Legacy test
    print("🏛️  LEGACY:")
    try:
        start_time = time.time()
        legacy_reply = handle(
            comment=user_input,
            post_id="compare_legacy",
            comment_id="compare_msg",
            username="compare_user"
        )
        legacy_time = time.time() - start_time
        print(f"   Reply: {legacy_reply}")
        print(f"   Time: {legacy_time:.3f}s")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Chain test
    print("\n🔗 CHAIN:")
    try:
        start_time = time.time()
        chain_reply = await process_with_chain(
            comment=user_input,
            post_id="compare_chain",
            comment_id="compare_msg",
            username="compare_user"
        )
        chain_time = time.time() - start_time
        print(f"   Reply: {chain_reply}")
        print(f"   Time: {chain_time:.3f}s")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def interactive_chat():
    """Original LEGACY interactive chat terminal"""
    print("🏛️  Instagram AI Agent - LEGACY Interactive Chat Terminal")
    print("=" * 60)
    print("Features:")
    print("  • Real-time LEGACY agent routing decisions")
    print("  • Step-by-step context retrieval")
    print("  • Final reply generation")
    print("  • Conversation history tracking")
    print("  • Type 'exit', 'quit', or 'bye' to exit")
    print("  • Type 'chain' to switch to chain mode")
    print("=" * 60)
    print()
    
    session_id = f"legacy_session_{int(time.time())}"
    conversation_count = 0
    
    try:
        while True:
            conversation_count += 1
            
            user_input = input(f"👤 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'bye', 'keluar']:
                print("\n👋 Sampai jumpa! Thanks for testing LEGACY agent!")
                break
            
            # Switch to chain mode
            if user_input.lower() == 'chain':
                print("\n🔄 Switching to chain mode...")
                asyncio.run(interactive_chain_chat())
                break
                
            print()
            print("🤖 Legacy Agent Processing...")
            print("-" * 40)
            
            try:
                # Show detailed legacy orchestration steps
                print("🎯 [STEP 1] Routing Decision")
                route = supervisor_route(user_input)
                print(f"   Decision: {route}")
                print()
                
                context = ""
                if route in {"docs", "web", "all"}:
                    print(f"🔍 [STEP 2] Context Retrieval (mode: {route})")
                    try:
                        context = retrieve_context(user_input, mode=route)
                        if context:
                            print(f"   ✅ Context retrieved: {len(context)} characters")
                            preview = context[:200] + "..." if len(context) > 200 else context
                            print(f"   Preview: \"{preview}\"")
                        else:
                            print("   ⚠️  No relevant context found")
                    except Exception as e:
                        print(f"   ❌ Context retrieval failed: {e}")
                        context = ""
                else:
                    print("🔍 [STEP 2] No context retrieval needed")
                    print(f"   Mode: {route} (direct response)")
                print()
                
                print("💬 [STEP 3] Generating Reply")
                
                reply = generate_reply(
                    comment=user_input,
                    post_id=session_id,
                    comment_id=f"legacy_msg_{conversation_count}",
                    username="legacy_user", 
                    context=context
                )
                print(f"   ✅ Reply generated: {len(reply)} characters")
                print()
                
                print("🎉 [LEGACY RESULT]")
                print(f"💬 Legacy Agent: {reply}")
                
            except Exception as e:
                print(f"❌ Error during processing: {e}")
                import traceback
                print("📋 Full traceback:")
                traceback.print_exc()
            
            print("\n" + "="*60 + "\n")
            
    except KeyboardInterrupt:
        print("\n\n⚡ Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

async def run_all_tests():
    """Run both legacy and chain tests"""
    print("🚀 Running ALL Tests (Legacy + Chain)\n")
    
    # Legacy tests
    print("🏛️  === LEGACY SYSTEM TESTS ===")
    test_supervisor_routing()
    test_rag_retrieval() 
    test_reply_generation()
    test_detailed_orchestration()
    test_full_orchestration()
    
    # Chain tests
    print("\n🔗 === CHAIN SYSTEM TESTS ===")
    await test_chain_basic()
    await test_chain_detailed_orchestration()
    await test_chain_vs_legacy_comparison()
    
    print("\n✅ All tests completed!")

def main():
    """Enhanced main entry point with Chain support"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            print("🚀 Running Automated Tests (Legacy + Chain)\n")
            asyncio.run(run_all_tests())
        elif sys.argv[1] == '--chain':
            print("🔗 Starting Chain Interactive Mode\n")
            asyncio.run(interactive_chain_chat())
        elif sys.argv[1] == '--legacy':
            print("🏛️  Starting Legacy Interactive Mode\n")
            interactive_chat()
        elif sys.argv[1] == '--compare':
            print("⚔️  Running Comparison Tests\n")
            asyncio.run(test_chain_vs_legacy_comparison())
    else:
        print("🎯 Instagram AI Agent Tester")
        print("=" * 40)
        print("Choose mode:")
        print("1. Chain Interactive Chat (recommended)")
        print("2. Legacy Interactive Chat")
        print("3. Run All Tests")
        print("4. Comparison Tests Only")
        print("=" * 40)
        
        choice = input("Your choice (1-4): ").strip()
        
        if choice == "1":
            asyncio.run(interactive_chain_chat())
        elif choice == "2":
            interactive_chat()
        elif choice == "3":
            asyncio.run(run_all_tests())
        elif choice == "4":
            asyncio.run(test_chain_vs_legacy_comparison())
        else:
            print("Invalid choice. Starting Chain mode...")
            asyncio.run(interactive_chain_chat())

if __name__ == "__main__":
    main()