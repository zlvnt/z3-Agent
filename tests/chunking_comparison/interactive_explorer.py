#!/usr/bin/env python3
"""
Interactive Chunking Explorer
Real-time CLI tool untuk explore chunking results dan compare retrieval quality
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from langchain.schema import Document
from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings

# Paths
COMPARISON_DIR = Path(__file__).parent
RECURSIVE_DIR = COMPARISON_DIR / "vector_stores" / "recursive"
SEMANTIC_DIR = COMPARISON_DIR / "vector_stores" / "semantic"

# Global state
vector_stores = {}
chunks = {}

def get_embeddings():
    """Get HuggingFace embeddings (same as main app)"""
    model_name = getattr(settings, 'EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def load_vector_stores():
    """Load both vector stores from existing directories"""
    global vector_stores, chunks
    
    print("🔄 Loading vector stores...")
    
    try:
        embeddings = get_embeddings()
        
        # Load recursive vector store
        if RECURSIVE_DIR.exists():
            recursive_store = FAISS.load_local(
                str(RECURSIVE_DIR), 
                embeddings,
                allow_dangerous_deserialization=True
            )
            vector_stores["recursive"] = recursive_store
            print(f"✅ Recursive store loaded from {RECURSIVE_DIR}")
        else:
            print(f"❌ Recursive store not found at {RECURSIVE_DIR}")
            return False
        
        # Load semantic vector store  
        if SEMANTIC_DIR.exists():
            semantic_store = FAISS.load_local(
                str(SEMANTIC_DIR),
                embeddings, 
                allow_dangerous_deserialization=True
            )
            vector_stores["semantic"] = semantic_store
            print(f"✅ Semantic store loaded from {SEMANTIC_DIR}")
        else:
            print(f"❌ Semantic store not found at {SEMANTIC_DIR}")
            return False
        
        print("🎉 Both vector stores loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to load vector stores: {e}")
        return False

def test_query_retrieval(query: str):
    """Show side-by-side retrieval for both methods"""
    
    if not vector_stores:
        print("❌ Vector stores not loaded. Please run option 1 first.")
        return
    
    print(f"\n" + "="*60)
    print(f"QUERY RETRIEVAL TEST: '{query}'")
    print("="*60)
    
    try:
        # Get retrievers
        recursive_retriever = vector_stores["recursive"].as_retriever(search_kwargs={"k": 3})
        semantic_retriever = vector_stores["semantic"].as_retriever(search_kwargs={"k": 3})
        
        # Retrieve documents
        recursive_docs = recursive_retriever.get_relevant_documents(query)
        semantic_docs = semantic_retriever.get_relevant_documents(query)
        
        # Show recursive results
        print(f"\n📄 RECURSIVE RESULTS ({len(recursive_docs)} docs):")
        for i, doc in enumerate(recursive_docs, 1):
            preview = doc.page_content[:60] + "..." if len(doc.page_content) > 60 else doc.page_content
            print(f"[{i}] {len(doc.page_content)} chars: \"{preview}\"")
        
        # Show semantic results
        print(f"\n🧠 SEMANTIC RESULTS ({len(semantic_docs)} docs):")
        for i, doc in enumerate(semantic_docs, 1):
            preview = doc.page_content[:60] + "..." if len(doc.page_content) > 60 else doc.page_content
            print(f"[{i}] {len(doc.page_content)} chars: \"{preview}\"")
        
        # Quick comparison
        recursive_avg = sum(len(d.page_content) for d in recursive_docs) // len(recursive_docs)
        semantic_avg = sum(len(d.page_content) for d in semantic_docs) // len(semantic_docs)
        
        print(f"\n📊 QUICK COMPARISON:")
        print(f"Recursive avg: {recursive_avg} chars")
        print(f"Semantic avg:  {semantic_avg} chars")
        print(f"Semantic advantage: {semantic_avg - recursive_avg:+d} chars")
        
    except Exception as e:
        print(f"❌ Query retrieval failed: {e}")

def browse_chunks(method: str, start_index: int = 0):
    """Show chunks with pagination (5 at a time)"""
    
    if not vector_stores:
        print("❌ Vector stores not loaded. Please run option 1 first.")
        return
    
    if method not in vector_stores:
        print(f"❌ Method '{method}' not available. Use 'recursive' or 'semantic'.")
        return
    
    print(f"\n" + "="*60)
    print(f"BROWSING CHUNKS - {method.upper()} METHOD")
    print("="*60)
    
    try:
        # Get all documents from vector store (approximate)
        store = vector_stores[method]
        # Note: FAISS doesn't expose documents directly, so we'll use a workaround
        
        print(f"📚 {method.upper()} chunks (showing 5 from index {start_index}):")
        print("Note: Use query retrieval to see actual content")
        
        # For demo, show some sample queries to explore chunks
        sample_queries = [
            "return barang", "customer service", "troubleshooting", 
            "refund policy", "contact info"
        ]
        
        for i, query in enumerate(sample_queries[start_index:start_index+5], start_index+1):
            retriever = store.as_retriever(search_kwargs={"k": 1})
            docs = retriever.get_relevant_documents(query)
            if docs:
                doc = docs[0]
                preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                print(f"\n[{i}] Query: '{query}' ({len(doc.page_content)} chars)")
                print(f"    Content: \"{preview}\"")
        
    except Exception as e:
        print(f"❌ Chunk browsing failed: {e}")

def compare_chunk_at_index(query: str):
    """Show detailed content comparison for specific query"""
    
    if not vector_stores:
        print("❌ Vector stores not loaded. Please run option 1 first.")
        return
    
    print(f"\n" + "="*80)
    print(f"DETAILED CHUNK COMPARISON: '{query}'")
    print("="*80)
    
    try:
        # Get first result from each method
        recursive_retriever = vector_stores["recursive"].as_retriever(search_kwargs={"k": 1})
        semantic_retriever = vector_stores["semantic"].as_retriever(search_kwargs={"k": 1})
        
        recursive_doc = recursive_retriever.get_relevant_documents(query)[0]
        semantic_doc = semantic_retriever.get_relevant_documents(query)[0]
        
        print(f"\n📄 RECURSIVE CHUNK ({len(recursive_doc.page_content)} chars):")
        print("-" * 40)
        print(recursive_doc.page_content[:500] + "..." if len(recursive_doc.page_content) > 500 else recursive_doc.page_content)
        
        print(f"\n🧠 SEMANTIC CHUNK ({len(semantic_doc.page_content)} chars):")
        print("-" * 40)
        print(semantic_doc.page_content[:500] + "..." if len(semantic_doc.page_content) > 500 else semantic_doc.page_content)
        
        # Analysis
        print(f"\n📊 ANALYSIS:")
        print(f"Size difference: {len(semantic_doc.page_content) - len(recursive_doc.page_content):+d} chars")
        print(f"Recursive: {'Fragmented' if len(recursive_doc.page_content) < 800 else 'Complete'}")
        print(f"Semantic:  {'Fragmented' if len(semantic_doc.page_content) < 800 else 'Complete'}")
        
    except Exception as e:
        print(f"❌ Chunk comparison failed: {e}")

def show_complete_llm_context(query: str, method: str):
    """Show exactly what LLM receives as context"""
    
    if not vector_stores or method not in vector_stores:
        print("❌ Vector stores not loaded or method not available")
        return
    
    print(f"\n" + "="*80)
    print(f"COMPLETE LLM CONTEXT - {method.upper()}")
    print(f"Query: '{query}'")
    print("="*80)
    
    try:
        # Get retriever and documents
        retriever = vector_stores[method].as_retriever(search_kwargs={"k": 4})
        docs = retriever.get_relevant_documents(query)
        
        # Concatenate all retrieved content (exactly what goes to LLM)
        complete_context = "\n\n".join([doc.page_content for doc in docs])
        
        print(f"\n📄 COMPLETE CONTEXT ({len(complete_context)} chars):")
        print("="*60)
        print(complete_context)
        print("="*60)
        
        # Content analysis
        print(f"\n📊 CONTENT ANALYSIS:")
        print(f"Total context length: {len(complete_context)} characters")
        print(f"Number of chunks combined: {len(docs)}")
        print(f"Contains Q&A pairs: {'Q:' in complete_context and 'A:' in complete_context}")
        print(f"Contains step procedures: {'Langkah' in complete_context or 'Step' in complete_context}")
        print(f"Contains contact info: {'1500-600' in complete_context or 'email' in complete_context}")
        
        # Information completeness check
        print(f"\n🔍 INFORMATION COMPLETENESS:")
        query_lower = query.lower()
        if 'return' in query_lower or 'refund' in query_lower:
            has_procedure = 'ajukan' in complete_context.lower() and 'step' in complete_context.lower()
            has_policy = 'produk yang bisa' in complete_context.lower()
            has_timeframe = 'hari' in complete_context and 'jam' in complete_context
            print(f"  Return procedure: {'✅' if has_procedure else '❌'}")
            print(f"  Policy information: {'✅' if has_policy else '❌'}")
            print(f"  Timeframe details: {'✅' if has_timeframe else '❌'}")
        elif 'contact' in query_lower or 'customer service' in query_lower:
            has_phone = '1500-600' in complete_context
            has_hours = 'jam' in complete_context and 'operasional' in complete_context
            has_email = 'email' in complete_context or '@' in complete_context
            print(f"  Phone number: {'✅' if has_phone else '❌'}")
            print(f"  Operating hours: {'✅' if has_hours else '❌'}")
            print(f"  Email contact: {'✅' if has_email else '❌'}")
        elif 'login' in query_lower or 'akun' in query_lower:
            has_troubleshooting = 'solusi' in complete_context.lower()
            has_steps = any(str(i) in complete_context for i in range(1, 6))
            has_otp = 'otp' in complete_context.lower()
            print(f"  Troubleshooting steps: {'✅' if has_troubleshooting else '❌'}")
            print(f"  Numbered steps: {'✅' if has_steps else '❌'}")
            print(f"  OTP solutions: {'✅' if has_otp else '❌'}")
        
        print(f"\n💡 LLM ANSWER POTENTIAL: {'HIGH' if len(complete_context) > 1000 else 'MEDIUM' if len(complete_context) > 500 else 'LOW'}")
        
    except Exception as e:
        print(f"❌ Failed to show LLM context: {e}")

def compare_llm_contexts(query: str):
    """Compare complete contexts that both methods provide to LLM"""
    
    if not vector_stores:
        print("❌ Vector stores not loaded")
        return
    
    print(f"\n" + "="*80)
    print(f"LLM CONTEXT COMPARISON")
    print(f"Query: '{query}'")
    print("="*80)
    
    try:
        contexts = {}
        
        # Get contexts from both methods
        for method in ["recursive", "semantic"]:
            retriever = vector_stores[method].as_retriever(search_kwargs={"k": 4})
            docs = retriever.get_relevant_documents(query)
            contexts[method] = "\n\n".join([doc.page_content for doc in docs])
        
        # Show both contexts
        for method, context in contexts.items():
            print(f"\n🔍 {method.upper()} CONTEXT ({len(context)} chars):")
            print("-" * 50)
            # Show first 800 chars for comparison
            preview = context[:800] + "\n... [TRUNCATED FOR DISPLAY]" if len(context) > 800 else context
            print(preview)
        
        # Compare information richness
        print(f"\n📊 CONTEXT COMPARISON:")
        for method, context in contexts.items():
            qa_count = context.count('Q:') + context.count('**Q:')
            step_count = context.count('Langkah') + context.count('Step')
            info_density = len(context.split()) / max(len(context.split('\n')), 1)
            print(f"{method.upper()}:")
            print(f"  Length: {len(context)} chars")
            print(f"  Q&A pairs: {qa_count}")
            print(f"  Step procedures: {step_count}")
            print(f"  Info density: {info_density:.1f} words/line")
        
        # Determine which provides better context
        recursive_len = len(contexts["recursive"])
        semantic_len = len(contexts["semantic"])
        
        print(f"\n🏆 BETTER CONTEXT FOR LLM:")
        if semantic_len > recursive_len * 1.5:
            print("SEMANTIC - Significantly more complete information")
        elif semantic_len > recursive_len:
            print("SEMANTIC - More comprehensive context")
        elif recursive_len > semantic_len:
            print("RECURSIVE - More concise, focused content")
        else:
            print("TIE - Similar context quality")
            
    except Exception as e:
        print(f"❌ Context comparison failed: {e}")

def show_stats():
    """Quick stats: chunk counts, avg sizes"""
    
    if not vector_stores:
        print("❌ Vector stores not loaded. Please run option 1 first.")
        return
    
    print(f"\n" + "="*50)
    print("VECTOR STORE STATISTICS")
    print("="*50)
    
    try:
        for method, store in vector_stores.items():
            # Get sample documents to estimate stats
            retriever = store.as_retriever(search_kwargs={"k": 10})
            sample_docs = retriever.get_relevant_documents("customer service return policy")
            
            if sample_docs:
                avg_size = sum(len(doc.page_content) for doc in sample_docs) // len(sample_docs)
                max_size = max(len(doc.page_content) for doc in sample_docs)
                min_size = min(len(doc.page_content) for doc in sample_docs)
                
                print(f"\n📊 {method.upper()} STATS:")
                print(f"  Sample size: {len(sample_docs)} chunks")
                print(f"  Avg size: {avg_size} chars")
                print(f"  Max size: {max_size} chars")
                print(f"  Min size: {min_size} chars")
            else:
                print(f"\n📊 {method.upper()}: No sample data available")
        
    except Exception as e:
        print(f"❌ Stats generation failed: {e}")

def show_menu():
    """Display enhanced interactive menu"""
    print("\n" + "="*50)
    print("CHUNKING EXPLORER - LLM CONTENT FOCUS")
    print("="*50)
    print("1. Load vector stores")
    print("2. Test query retrieval (overview)")
    print("3. Show complete LLM context (recursive)")
    print("4. Show complete LLM context (semantic)")
    print("5. Compare LLM contexts side-by-side")
    print("6. Show statistics")
    print("7. Exit")
    print("-" * 50)

def main():
    """Main interactive loop"""
    print("🚀 Interactive Chunking Explorer")
    print("Explore and compare chunking methods in real-time!")
    
    while True:
        show_menu()
        
        try:
            choice = input("Your choice (1-6): ").strip()
            
            if choice == "1":
                success = load_vector_stores()
                if success:
                    print("\n✅ Ready for exploration!")
            
            elif choice == "2":
                query = input("\nEnter query to test: ").strip()
                if query:
                    test_query_retrieval(query)
                else:
                    print("❌ Please enter a valid query")
            
            elif choice == "3":
                query = input("\nEnter query to see recursive LLM context: ").strip()
                if query:
                    show_complete_llm_context(query, "recursive")
                else:
                    print("❌ Please enter a valid query")

            elif choice == "4":
                query = input("\nEnter query to see semantic LLM context: ").strip()
                if query:
                    show_complete_llm_context(query, "semantic")
                else:
                    print("❌ Please enter a valid query")

            elif choice == "5":
                query = input("\nEnter query to compare both LLM contexts: ").strip()
                if query:
                    compare_llm_contexts(query)
                else:
                    print("❌ Please enter a valid query")

            elif choice == "6":
                show_stats()
            
            elif choice == "7":
                print("\n👋 Thanks for exploring! Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-6.")
            
            if choice != "6":
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\n⚡ Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()