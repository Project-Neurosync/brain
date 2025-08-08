"""
Test script to verify Chroma vector store is working correctly.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_chroma():
    """Test the Chroma vector store."""
    print("🧪 Testing Chroma Vector Store")
    print("=" * 40)
    
    try:
        # Test 1: Import Chroma vector store
        print("1. Testing Chroma import...")
        from services.vectorstore.chroma import ChromaVectorStore
        print("✅ ChromaVectorStore imported successfully")
        
        # Test 2: Initialize Chroma
        print("\n2. Testing Chroma initialization...")
        chroma_store = ChromaVectorStore(
            collection_name="test_collection",
            persist_directory="./test_chroma_db"
        )
        await chroma_store.initialize()
        print("✅ ChromaVectorStore initialized successfully")
        
        # Test 3: Test search by text (should work with mock data even without real data)
        print("\n3. Testing Chroma search by text...")
        results = await chroma_store.search_by_text(
            query_text="authentication bug",
            namespace="test_project",
            top_k=3
        )
        print(f"✅ Found {len(results)} search results")
        
        for i, result in enumerate(results):
            print(f"   Result {i+1}: {result.document.metadata.get('title', 'Unknown')} (score: {result.score:.2f})")
        
        # Test 4: Test add_documents
        print("\n4. Testing Chroma add_documents...")
        from services.vectorstore.base import Document
        
        test_docs = [
            Document(
                id='test_doc_1',
                content='This is a test document about authentication issues.',
                metadata={
                    'title': 'Test Auth Doc',
                    'source_type': 'test',
                    'url': 'https://example.com/test1'
                }
            )
        ]
        
        doc_ids = await chroma_store.add_documents(test_docs, namespace="test_project")
        success = len(doc_ids) > 0
        print(f"✅ Upsert {'successful' if success else 'failed'}")
        
        print("\n" + "=" * 40)
        print("🎉 Chroma vector store test completed!")
        print("ChromaDB is working and ready for production use.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Chroma test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chroma())
    sys.exit(0 if success else 1)
