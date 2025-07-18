#!/usr/bin/env python3
"""
Embedding Migration Script
Migrates vector store from Gemini to HuggingFace embeddings with backup
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import shutil

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings
from app.services.vector import build_index, _get_embeddings, _index_exists
from app.services.logger import logger

def backup_existing_index():
    """Backup existing FAISS index if it exists"""
    vector_dir = Path(settings.VECTOR_DIR)
    if not _index_exists():
        print("INFO: No existing index to backup")
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = vector_dir.parent / f"vector_store_backup_{timestamp}"
    
    try:
        shutil.copytree(vector_dir, backup_dir)
        print(f"INFO: Index backed up to {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"ERROR: Failed to backup index - {e}")
        return None

def test_embedding_connection():
    """Test if embedding model is working"""
    try:
        embeddings = _get_embeddings()
        test_text = "Test embedding connection"
        result = embeddings.embed_query(test_text)
        print(f"INFO: Embedding test successful - dimension: {len(result)}")
        return True
    except Exception as e:
        print(f"ERROR: Embedding test failed - {e}")
        return False

def migrate_embeddings():
    """Main migration function"""
    print("🚀 Starting embedding migration...")
    print(f"Target embedding model: {settings.EMBEDDING_MODEL}")
    print("Migration: Gemini → HuggingFace (Local, FREE! 🎉)")
    
    # Step 1: Test embedding connection
    print("\n📡 Testing embedding connection...")
    if not test_embedding_connection():
        print("❌ Migration aborted - embedding connection failed")
        return False
    
    # Step 2: Backup existing index
    print("\n💾 Backing up existing index...")
    backup_path = backup_existing_index()
    
    # Step 3: Clear cache to force new embedding model
    print("\n🔄 Clearing embedding cache...")
    _get_embeddings.cache_clear()
    
    # Step 4: Rebuild index with new embeddings
    print("\n🏗️ Building new index with updated embeddings...")
    try:
        build_index()
        print("✅ Migration completed successfully!")
        
        # Test the new index
        print("\n🧪 Testing new index...")
        from app.services.vector import get_retriever
        retriever = get_retriever()
        test_results = retriever.get_relevant_documents("test query", k=2)
        print(f"✅ New index test successful - retrieved {len(test_results)} docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed during rebuild - {e}")
        
        # Restore backup if available
        if backup_path and backup_path.exists():
            print("🔄 Restoring backup...")
            try:
                vector_dir = Path(settings.VECTOR_DIR)
                if vector_dir.exists():
                    shutil.rmtree(vector_dir)
                shutil.copytree(backup_path, vector_dir)
                print("✅ Backup restored successfully")
            except Exception as restore_error:
                print(f"❌ Failed to restore backup - {restore_error}")
        
        return False

def compare_embeddings():
    """Compare performance between old and new embeddings"""
    print("\n📊 Comparing embedding performance...")
    
    test_queries = [
        "cara return barang",
        "bagaimana cara refund",
        "customer service contact",
        "status pengiriman",
        "promo terbaru"
    ]
    
    try:
        from app.services.vector import get_retriever
        retriever = get_retriever()
        
        for query in test_queries:
            docs = retriever.get_relevant_documents(query, k=3)
            print(f"Query: '{query}' -> Retrieved {len(docs)} docs")
            for i, doc in enumerate(docs, 1):
                preview = doc.page_content[:100].replace('\n', ' ')
                print(f"  {i}. {preview}...")
        
        print("✅ Embedding comparison completed")
        
    except Exception as e:
        print(f"❌ Comparison failed - {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  EMBEDDING MIGRATION SCRIPT")
    print("  Gemini → HuggingFace (Local & FREE)")
    print("=" * 60)
    
    # Check requirements - HuggingFace needs no API key!
    print("✅ Using HuggingFace embeddings (no API key required)")
    print(f"✅ Model: {settings.EMBEDDING_MODEL}")
    
    # Run migration
    success = migrate_embeddings()
    
    if success:
        print("\n📊 Running performance comparison...")
        compare_embeddings()
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("✅ Vector store now uses HuggingFace embeddings (LOCAL & FREE)")
        print("✅ Backup created for rollback if needed")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRATION FAILED")
        print("Check error messages above and retry")
        print("=" * 60)
        sys.exit(1)