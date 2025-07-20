#!/usr/bin/env python3
"""
Chunking Methods A/B Testing - Scientific Comparison
Compare RecursiveCharacterTextSplitter vs SemanticChunker performance
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores.faiss import FAISS

from app.config import settings

# Test Configuration
TEST_QUERIES = [
    "Cara return barang rusak?",
    "Customer service contact info?",
    "App error troubleshooting?", 
    "Refund policy details?",
    "Prosedur eskalasi komplain?"
]

COMPARISON_DIR = Path(__file__).parent
RECURSIVE_DIR = COMPARISON_DIR / "vector_stores" / "recursive"
SEMANTIC_DIR = COMPARISON_DIR / "vector_stores" / "semantic"
DOCS_DIR = Path(settings.DOCS_DIR)

def get_embeddings():
    """Get HuggingFace embeddings (same as main app)"""
    from langchain_huggingface import HuggingFaceEmbeddings
    model_name = getattr(settings, 'EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def load_documents() -> List[Document]:
    """Load documents from docs directory (same as main app)"""
    loaders = [
        DirectoryLoader(str(DOCS_DIR), glob="**/*.md", loader_cls=TextLoader),
        DirectoryLoader(str(DOCS_DIR), glob="**/*.txt", loader_cls=TextLoader),
    ]
    
    docs: List[Document] = []
    for loader in loaders:
        try:
            docs.extend(loader.load())
        except Exception as e:
            print(f"WARNING: Doc load failed - {e}")
    
    print(f"INFO: Loaded {len(docs)} documents for testing")
    return docs

def build_recursive_index() -> Dict[str, Any]:
    """Build index using RecursiveCharacterTextSplitter"""
    print("\n=' Building Recursive Index...")
    start_time = time.time()
    
    # Load docs
    docs = load_documents()
    
    # Split with RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    split_docs = splitter.split_documents(docs)
    
    # Build FAISS index
    embeddings = get_embeddings()
    vectordb = FAISS.from_documents(split_docs, embeddings)
    
    # Save to isolated directory
    RECURSIVE_DIR.mkdir(parents=True, exist_ok=True)
    vectordb.save_local(str(RECURSIVE_DIR))
    
    build_time = time.time() - start_time
    avg_chunk_size = sum(len(doc.page_content) for doc in split_docs) / len(split_docs)
    
    results = {
        "method": "RecursiveCharacterTextSplitter",
        "chunk_count": len(split_docs),
        "avg_chunk_size": int(avg_chunk_size),
        "build_time": round(build_time, 2),
        "vectordb": vectordb,
        "chunks": split_docs
    }
    
    print(f" Recursive Index: {results['chunk_count']} chunks, {results['avg_chunk_size']} avg chars, {results['build_time']}s")
    return results

def build_semantic_index() -> Dict[str, Any]:
    """Build index using SemanticChunker"""
    print("\n>� Building Semantic Index...")
    start_time = time.time()
    
    # Load docs
    docs = load_documents()
    
    # Split with SemanticChunker
    embeddings = get_embeddings()
    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile"
    )
    split_docs = splitter.split_documents(docs)
    
    # Build FAISS index
    vectordb = FAISS.from_documents(split_docs, embeddings)
    
    # Save to isolated directory
    SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)
    vectordb.save_local(str(SEMANTIC_DIR))
    
    build_time = time.time() - start_time
    avg_chunk_size = sum(len(doc.page_content) for doc in split_docs) / len(split_docs)
    
    results = {
        "method": "SemanticChunker",
        "chunk_count": len(split_docs),
        "avg_chunk_size": int(avg_chunk_size),
        "build_time": round(build_time, 2),
        "vectordb": vectordb,
        "chunks": split_docs
    }
    
    print(f" Semantic Index: {results['chunk_count']} chunks, {results['avg_chunk_size']} avg chars, {results['build_time']}s")
    return results

def analyze_chunking_process(recursive_chunks, semantic_chunks):
    """Show actual chunk boundaries and content"""
    
    print("\n" + "="*80)
    print("CHUNKING PROCESS ANALYSIS")
    print("="*80)
    
    # Show first few chunks from each method
    print("\n🔪 RECURSIVE CHUNKING (Character-based):")
    for i, chunk in enumerate(recursive_chunks[:3]):
        print(f"\nChunk {i+1} ({len(chunk.page_content)} chars):")
        print("-" * 40)
        preview = chunk.page_content[:300] + "..." if len(chunk.page_content) > 300 else chunk.page_content
        print(preview)
        print(f"[...continues for {len(chunk.page_content)} total chars]")
    
    print(f"\n... and {len(recursive_chunks)-3} more chunks")
    
    print("\n🧠 SEMANTIC CHUNKING (Meaning-based):")
    for i, chunk in enumerate(semantic_chunks[:3]):
        print(f"\nChunk {i+1} ({len(chunk.page_content)} chars):")
        print("-" * 40)
        preview = chunk.page_content[:300] + "..." if len(chunk.page_content) > 300 else chunk.page_content
        print(preview)
        print(f"[...continues for {len(chunk.page_content)} total chars]")
    
    print(f"\n... and {len(semantic_chunks)-3} more chunks")

def detailed_retrieval_analysis(recursive_retriever, semantic_retriever, query):
    """Show actual retrieved content for comparison"""
    
    print(f"\n" + "="*60)
    print(f"DETAILED RETRIEVAL ANALYSIS: '{query}'")
    print("="*60)
    
    recursive_docs = recursive_retriever.get_relevant_documents(query)
    semantic_docs = semantic_retriever.get_relevant_documents(query)
    
    print("\n📄 RECURSIVE RETRIEVAL RESULTS:")
    for i, doc in enumerate(recursive_docs, 1):
        print(f"\nResult {i} ({len(doc.page_content)} chars):")
        print("-" * 30)
        # Show more content for better analysis
        preview = doc.page_content[:400] + "..." if len(doc.page_content) > 400 else doc.page_content
        print(preview)
    
    print("\n🧠 SEMANTIC RETRIEVAL RESULTS:")
    for i, doc in enumerate(semantic_docs, 1):
        print(f"\nResult {i} ({len(doc.page_content)} chars):")
        print("-" * 30)
        preview = doc.page_content[:400] + "..." if len(doc.page_content) > 400 else doc.page_content
        print(preview)
    
    # Analysis comparison
    print(f"\n📊 CONTENT ANALYSIS:")
    print(f"Recursive - Avg length: {sum(len(d.page_content) for d in recursive_docs) // len(recursive_docs)} chars")
    print(f"Semantic  - Avg length: {sum(len(d.page_content) for d in semantic_docs) // len(semantic_docs)} chars")
    
    # Check for completeness indicators
    recursive_text = " ".join(d.page_content for d in recursive_docs)
    semantic_text = " ".join(d.page_content for d in semantic_docs)
    
    print(f"\n🔍 COMPLETENESS CHECK:")
    print(f"Recursive contains 'Langkah': {recursive_text.count('Langkah')} times")
    print(f"Semantic contains 'Langkah': {semantic_text.count('Langkah')} times")
    print(f"Recursive contains 'Q:': {recursive_text.count('Q:')} times") 
    print(f"Semantic contains 'Q:': {semantic_text.count('Q:')} times")

def analyze_context_coherence(chunks, method_name):
    """Analyze how well chunks preserve document structure"""
    
    print(f"\n📖 CONTEXT COHERENCE ANALYSIS - {method_name}:")
    print("-" * 50)
    
    # Check for broken Q&A pairs
    qa_pairs_broken = 0
    step_sequences_broken = 0
    
    for chunk in chunks:
        content = chunk.page_content
        
        # Check for incomplete Q&A (Q without A or A without Q)
        if ('Q:' in content and 'A:' not in content) or ('A:' in content and 'Q:' not in content):
            qa_pairs_broken += 1
        
        # Check for broken step sequences (step N without N-1 or N+1)
        import re
        steps = re.findall(r'Langkah \d+', content)
        if len(steps) > 0:
            # Simple check for sequential steps
            step_numbers = [int(re.search(r'\d+', step).group()) for step in steps]
            if len(step_numbers) > 1:
                for i in range(1, len(step_numbers)):
                    if step_numbers[i] != step_numbers[i-1] + 1:
                        step_sequences_broken += 1
                        break
    
    print(f"Q&A pairs broken: {qa_pairs_broken}/{len(chunks)} chunks")
    print(f"Step sequences broken: {step_sequences_broken}/{len(chunks)} chunks")
    print(f"Average chunk coherence: {((len(chunks) - qa_pairs_broken - step_sequences_broken) / len(chunks) * 100):.1f}%")

def compare_retrieval_quality(recursive_results: Dict, semantic_results: Dict) -> Dict[str, Any]:
    """Compare retrieval quality between both methods"""
    print("\n=Comparing Retrieval Quality...")
    
    comparison_results = {
        "query_comparisons": [],
        "winner_count": {"recursive": 0, "semantic": 0, "tie": 0}
    }
    
    recursive_retriever = recursive_results["vectordb"].as_retriever(search_kwargs={"k": 3})
    semantic_retriever = semantic_results["vectordb"].as_retriever(search_kwargs={"k": 3})
    
    for query in TEST_QUERIES:
        print(f"\n=� Testing Query: '{query}'")
        
        # Get results from both methods
        recursive_docs = recursive_retriever.get_relevant_documents(query)
        semantic_docs = semantic_retriever.get_relevant_documents(query)
        
        # Analyze results
        recursive_preview = [doc.page_content[:100] + "..." for doc in recursive_docs]
        semantic_preview = [doc.page_content[:100] + "..." for doc in semantic_docs]
        
        # Simple winner determination (could be more sophisticated)
        # For now, prefer semantic if chunk count is reasonable and context looks coherent
        avg_recursive_length = sum(len(doc.page_content) for doc in recursive_docs) / len(recursive_docs)
        avg_semantic_length = sum(len(doc.page_content) for doc in semantic_docs) / len(semantic_docs)
        
        winner = "semantic" if avg_semantic_length > avg_recursive_length * 1.2 else "recursive"
        if abs(avg_semantic_length - avg_recursive_length) < 100:
            winner = "tie"
        
        comparison_results["winner_count"][winner] += 1
        
        query_result = {
            "query": query,
            "recursive": {
                "docs_count": len(recursive_docs),
                "avg_length": int(avg_recursive_length),
                "previews": recursive_preview
            },
            "semantic": {
                "docs_count": len(semantic_docs),
                "avg_length": int(avg_semantic_length),
                "previews": semantic_preview
            },
            "winner": winner
        }
        
        comparison_results["query_comparisons"].append(query_result)
        print(f"   Winner: {winner.upper()}")
    
    return comparison_results

def generate_report(recursive_results: Dict, semantic_results: Dict, comparison_results: Dict):
    """Generate comprehensive comparison report"""
    
    report = []
    report.append("=" * 60)
    report.append("CHUNKING COMPARISON RESULTS")
    report.append("=" * 60)
    report.append("")
    
    # Method Comparison
    report.append("=� METHOD COMPARISON:")
    report.append(f"RecursiveCharacterTextSplitter:")
    report.append(f"  - Chunks: {recursive_results['chunk_count']}")
    report.append(f"  - Avg size: {recursive_results['avg_chunk_size']} chars")
    report.append(f"  - Build time: {recursive_results['build_time']}s")
    report.append("")
    
    report.append(f"SemanticChunker:")
    report.append(f"  - Chunks: {semantic_results['chunk_count']}")
    report.append(f"  - Avg size: {semantic_results['avg_chunk_size']} chars")
    report.append(f"  - Build time: {semantic_results['build_time']}s")
    report.append("")
    
    # Performance Analysis
    chunk_reduction = (recursive_results['chunk_count'] - semantic_results['chunk_count']) / recursive_results['chunk_count'] * 100
    report.append("=� PERFORMANCE ANALYSIS:")
    report.append(f"  - Chunk reduction: {chunk_reduction:.1f}% (semantic vs recursive)")
    report.append(f"  - Context preservation: {'BETTER' if chunk_reduction > 20 else 'SIMILAR'}")
    report.append(f"  - Build time overhead: {semantic_results['build_time'] - recursive_results['build_time']:.1f}s")
    report.append("")
    
    # Query Test Results
    report.append("=QUERY TEST RESULTS:")
    for result in comparison_results["query_comparisons"]:
        report.append(f"Query: '{result['query']}'")
        report.append(f"  Recursive: {result['recursive']['docs_count']} docs, {result['recursive']['avg_length']} avg chars")
        report.append(f"  Semantic:  {result['semantic']['docs_count']} docs, {result['semantic']['avg_length']} avg chars")
        report.append(f"  Winner: {result['winner'].upper()}")
        report.append("")
    
    # Overall Winner
    winners = comparison_results["winner_count"]
    overall_winner = max(winners, key=winners.get)
    report.append("<� OVERALL ANALYSIS:")
    report.append(f"  - Recursive wins: {winners['recursive']}")
    report.append(f"  - Semantic wins: {winners['semantic']}")
    report.append(f"  - Ties: {winners['tie']}")
    report.append(f"  - Overall winner: {overall_winner.upper()}")
    report.append("")
    
    # Recommendation
    report.append("=� RECOMMENDATION:")
    if semantic_results['chunk_count'] < recursive_results['chunk_count'] * 0.7:
        recommendation = "SemanticChunker - Better context preservation with fewer chunks"
    elif winners['semantic'] > winners['recursive']:
        recommendation = "SemanticChunker - Better retrieval quality in testing"
    else:
        recommendation = "RecursiveCharacterTextSplitter - More predictable and faster"
    
    report.append(f"  {recommendation}")
    report.append("")
    report.append("=" * 60)
    
    # Print to console
    print("\n" + "\n".join(report))
    
    # Save to file
    report_file = COMPARISON_DIR / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    
    print(f"\n=� Report saved to: {report_file}")

def main():
    """Main A/B testing execution"""
    print("=� Starting Chunking Methods A/B Testing...")
    print(f"=� Docs directory: {DOCS_DIR}")
    print(f">� Test queries: {len(TEST_QUERIES)}")
    print("=" * 60)
    
    try:
        # Build both indexes
        recursive_results = build_recursive_index()
        semantic_results = build_semantic_index()
        
        # NEW: Add detailed process analysis
        print("\n" + "="*80)
        print("ENHANCED ANALYSIS WITH PROCESS TRANSPARENCY")
        print("="*80)
        
        # Analyze chunking process
        analyze_chunking_process(recursive_results["chunks"], semantic_results["chunks"])
        
        # Analyze context coherence
        analyze_context_coherence(recursive_results["chunks"], "RecursiveCharacterTextSplitter")
        analyze_context_coherence(semantic_results["chunks"], "SemanticChunker")
        
        # Detailed retrieval analysis for first 2 queries
        recursive_retriever = recursive_results["vectordb"].as_retriever(search_kwargs={"k": 3})
        semantic_retriever = semantic_results["vectordb"].as_retriever(search_kwargs={"k": 3})
        
        for query in TEST_QUERIES[:2]:  # Show detailed analysis for first 2 queries
            detailed_retrieval_analysis(recursive_retriever, semantic_retriever, query)
        
        # Compare retrieval quality
        comparison_results = compare_retrieval_quality(recursive_results, semantic_results)
        
        # Generate comprehensive report
        generate_report(recursive_results, semantic_results, comparison_results)
        
        print("\n A/B Testing completed successfully!")
        
    except Exception as e:
        print(f"\nL A/B Testing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()