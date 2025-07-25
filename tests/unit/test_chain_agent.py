import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import asyncio
import time

# Legacy imports (minimal - only for legacy mode)
from app.agents.router import handle, supervisor_route
from app.agents.reply import generate_reply
from app.agents.rag import retrieve_context

# NEW: Chain imports
from app.chains.conditional_chain import process_with_chain, get_chain

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
            
            
            print()
            print("🔗 Chain Processing...")
            print("-" * 40)
            
            try:
                start_time = time.time()
                
                reply = await process_with_chain(
                    comment=user_input,
                    post_id=session_id,
                    comment_id="interactive_session",  # Same comment_id untuk thread
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
                # Get history for better routing decision
                from app.agents.reply import _build_history_context
                try:
                    history_context = _build_history_context(session_id, f"legacy_msg_{conversation_count}", limit=3)
                except:
                    history_context = ""
                
                route = supervisor_route(user_input, history_context=history_context)
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


def main():
    """Direct to Chain interactive session"""
    if len(sys.argv) > 1 and sys.argv[1] == '--legacy':
        print("🏛️  Starting Legacy Interactive Mode\n")
        interactive_chat()
    else:
        # Always go to Chain interactive (default)
        print("🔗 Starting Chain Interactive Mode\n")
        asyncio.run(interactive_chain_chat())

if __name__ == "__main__":
    main()