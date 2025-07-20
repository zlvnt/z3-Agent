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
    """Display interactive menu"""
    print("\n" + "="*50)
    print("CHUNKING EXPLORER")
    print("="*50)
    print("1. Load vector stores")
    print("2. Test query retrieval")
    print("3. Browse chunks")
    print("4. Compare chunk for query")
    print("5. Show statistics")
    print("6. Exit")
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
                method = input("\nMethod (recursive/semantic): ").strip().lower()
                start_idx = input("Start index (default 0): ").strip()
                start_idx = int(start_idx) if start_idx.isdigit() else 0
                browse_chunks(method, start_idx)
            
            elif choice == "4":
                query = input("\nEnter query for detailed comparison: ").strip()
                if query:
                    compare_chunk_at_index(query)
                else:
                    print("❌ Please enter a valid query")
            
            elif choice == "5":
                show_stats()
            
            elif choice == "6":
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