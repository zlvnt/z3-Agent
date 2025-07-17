#!/usr/bin/env python3
"""
Interactive Agent Chat Terminal
Usage: python test_agents.py

Features:
- Real-time agent orchestration testing
- Step-by-step routing, context, and reply visualization  
- Interactive chat interface like ChatGPT/Claude
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.agents.router import handle, supervisor_route
from app.agents.reply import generate_reply
from app.agents.rag import retrieve_context

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

def test_detailed_orchestration():
    """Test orchestration with detailed step-by-step tracing"""
    print("\n🎯 Testing Detailed Agent Orchestration...")
    
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
        },
        {
            "comment": "Apa berita terbaru tentang teknologi AI?",
            "post_id": "post_003",
            "comment_id": "comment_003", 
            "username": "user3",
            "description": "Current events - should route to web"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"🧪 SCENARIO {i}: {scenario['description']}")
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
            print("📊 ORCHESTRATION SUMMARY:")
            print(f"   Route: {route}")
            print(f"   Context Used: {'Yes' if context else 'No'}")
            print(f"   Reply Length: {len(reply)} characters")
            
        except Exception as e:
            print(f"❌ Error in scenario {i}: {e}")
            import traceback
            traceback.print_exc()

def test_full_orchestration():
    """Test end-to-end agent flow using handle() function"""
    print("\n🎯 Testing Full Agent Orchestration (via handle())...")
    
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
        },
        {
            "comment": "Apa berita terbaru tentang teknologi AI?",
            "post_id": "post_003",
            "comment_id": "comment_003", 
            "username": "user3"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Scenario {i} ---")
        print(f"User: {scenario['username']}")
        print(f"Comment: '{scenario['comment']}'")
        
        try:
            reply = handle(**scenario)
            print(f"Bot Reply: '{reply}'")
        except Exception as e:
            print(f"❌ Error: {e}")

def interactive_chat():
    """Interactive chat terminal with agent orchestration visualization"""
    print("🤖 Instagram AI Agent - Interactive Chat Terminal")
    print("=" * 60)
    print("Features:")
    print("  • Real-time agent routing decisions")
    print("  • Step-by-step context retrieval")
    print("  • Final reply generation")
    print("  • Conversation history tracking")
    print("  • Type 'exit', 'quit', or 'bye' to exit")
    print("  • Type 'test' to run automated tests")
    print("=" * 60)
    print()
    
    # Use consistent post_id for entire interactive session
    import time
    session_id = f"interactive_session_{int(time.time())}"
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
                print("\n👋 Sampai jumpa! Thanks for testing the agent!")
                break
                
            # Test command
            if user_input.lower() == 'test':
                print("\n🧪 Running automated tests...\n")
                run_automated_tests()
                print("\n" + "="*60 + "\n")
                continue
            
            print()
            print("🤖 Agent Processing...")
            print("-" * 40)
            
            try:
                # Step 1: Routing Decision
                print("🎯 [STEP 1] Routing Decision")
                route = supervisor_route(user_input)
                print(f"   Decision: {route}")
                print()
                
                # Step 2: Context Retrieval
                context = ""
                if route in {"docs", "web", "all"}:
                    print(f"🔍 [STEP 2] Context Retrieval (mode: {route})")
                    try:
                        context = retrieve_context(user_input, mode=route)
                        if context:
                            print(f"   ✅ Context retrieved: {len(context)} characters")
                            # Show preview
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
                
                # Step 3: Reply Generation
                print("💬 [STEP 3] Generating Reply")
                
                # Show conversation history info
                from app.services.conversation import get_comment_history
                history = get_comment_history(session_id, "interactive_conversation")
                if history:
                    print(f"   📚 Using conversation history: {len(history)} previous messages")
                else:
                    print("   📚 No previous conversation history")
                
                reply = generate_reply(
                    comment=user_input,
                    post_id=session_id,  # Same post_id for all conversation in this session
                    comment_id="interactive_conversation",  # Fixed comment_id for entire session
                    username="interactive_user", 
                    context=context
                )
                print(f"   ✅ Reply generated: {len(reply)} characters")
                print()
                
                # Final Result
                print("🎉 [FINAL RESULT]")
                print(f"💬 Agent: {reply}")
                
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

def run_automated_tests():
    """Run the original automated tests"""
    try:
        test_supervisor_routing()
        test_rag_retrieval() 
        test_reply_generation()
        test_detailed_orchestration()
        test_full_orchestration()
        print("✅ All automated tests completed!")
    except Exception as e:
        print(f"❌ Automated test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point - choose between interactive or automated testing"""
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("🚀 Running Automated Agent Tests\n")
        run_automated_tests()
    else:
        interactive_chat()

if __name__ == "__main__":
    main()