#!/usr/bin/env python3
"""
Simple Retriever Comparison Tool
Compare hasil lengkap dari retriever antara RecursiveCharacterTextSplitter vs SemanticChunker
"""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import settings

# Paths
COMPARISON_DIR = Path(__file__).parent
RECURSIVE_DIR = COMPARISON_DIR / "vector_stores" / "recursive"
SEMANTIC_DIR = COMPARISON_DIR / "vector_stores" / "semantic"

# Global state
vector_stores = {}

def get_embeddings():
    """Get HuggingFace embeddings (same as main app)"""
    model_name = getattr(settings, 'EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def load_vector_stores():
    """Load both vector stores"""
    global vector_stores
    
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
            print(f"✅ Recursive store loaded")
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
            print(f"✅ Semantic store loaded")
        else:
            print(f"❌ Semantic store not found at {SEMANTIC_DIR}")
            return False
        
        print("🎉 Both vector stores loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to load vector stores: {e}")
        return False

def compare_retriever_results(query: str, k: int = 3):
    """Compare complete retriever results that go to LLM"""
    
    if not vector_stores:
        print("❌ Vector stores not loaded. Run load_vector_stores() first.")
        return
    
    print(f"\n" + "="*80)
    print(f"RETRIEVER COMPARISON FOR LLM")
    print(f"Query: '{query}' (k={k})")
    print("="*80)
    
    try:
        results = {}
        
        # Get results from both methods
        for method in ["recursive", "semantic"]:
            retriever = vector_stores[method].as_retriever(search_kwargs={"k": k})
            docs = retriever.get_relevant_documents(query)
            
            # Create complete context (exactly what LLM receives)
            complete_context = "\n\n".join([doc.page_content for doc in docs])
            results[method] = {
                "docs": docs,
                "context": complete_context,
                "chunks": len(docs)
            }
        
        # Show both results
        for method, result in results.items():
            print(f"\n🔍 {method.upper()} RETRIEVER RESULT:")
            print(f"Chunks retrieved: {result['chunks']}")
            print(f"Total context length: {len(result['context'])} chars")
            print("-" * 60)
            print(result['context'])
            print("-" * 60)
        
        # Quick comparison analysis
        print(f"\n📊 COMPARISON ANALYSIS:")
        recursive_len = len(results["recursive"]["context"])
        semantic_len = len(results["semantic"]["context"])
        
        print(f"Recursive: {recursive_len} chars, {results['recursive']['chunks']} chunks")
        print(f"Semantic:  {semantic_len} chars, {results['semantic']['chunks']} chunks")
        print(f"Difference: {semantic_len - recursive_len:+d} chars")
        
        # Information completeness
        print(f"\n🎯 INFORMATION QUALITY:")
        for method, result in results.items():
            context = result['context'].lower()
            qa_pairs = context.count('q:') + context.count('**q:')
            procedures = context.count('step') + context.count('langkah')
            contact_info = '1500-600' in context or '@' in context
            
            print(f"{method.upper()}:")
            print(f"  Q&A pairs: {qa_pairs}")
            print(f"  Procedures: {procedures}")
            print(f"  Contact info: {'✅' if contact_info else '❌'}")
        
        # Recommendation
        print(f"\n🏆 RECOMMENDATION FOR LLM:")
        if semantic_len > recursive_len * 1.3:
            print("SEMANTIC - Significantly more complete information")
        elif semantic_len > recursive_len:
            print("SEMANTIC - More comprehensive context")
        elif recursive_len > semantic_len * 1.1:
            print("RECURSIVE - More focused, concise content")
        else:
            print("SIMILAR - Both provide comparable context quality")
            
    except Exception as e:
        print(f"❌ Comparison failed: {e}")

def main():
    """Simple interactive comparison"""
    print("🔍 Simple Retriever Comparison Tool")
    print("Compare RecursiveCharacterTextSplitter vs SemanticChunker results")
    
    # Load vector stores
    if not load_vector_stores():
        print("❌ Cannot proceed without vector stores")
        return
    
    print("\n✅ Ready for comparison!")
    
    # Sample queries for testing
    sample_queries = [
        "Bagaimana cara return barang?",
        "Customer service jam berapa buka?", 
        "Saya tidak bisa login ke akun",
        "Refund kapan cair ke rekening?",
        "Voucher tidak bisa dipakai kenapa?"
    ]
    
    while True:
        print(f"\n" + "-"*50)
        print("OPTIONS:")
        print("1. Compare with custom query")
        print("2. Compare with sample queries")
        print("3. Exit")
        
        choice = input("\nYour choice (1-3): ").strip()
        
        if choice == "1":
            query = input("\nEnter your query: ").strip()
            if query:
                compare_retriever_results(query)
            else:
                print("❌ Please enter a valid query")
        
        elif choice == "2":
            print(f"\n🧪 Testing {len(sample_queries)} sample queries...")
            for i, query in enumerate(sample_queries, 1):
                print(f"\n[SAMPLE {i}/{len(sample_queries)}]")
                compare_retriever_results(query)
                input("\nPress Enter for next query...")
        
        elif choice == "3":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-3.")

if __name__ == "__main__":
    main()