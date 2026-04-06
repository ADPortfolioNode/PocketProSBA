"""
Basic RAG functionality test
Test ChromaDB and embedding functions independently
"""
import os
import sys
import shutil
from pathlib import Path

def test_chromadb_rag():
    """Test basic RAG functionality"""
    print("🧪 Testing RAG Functionality")
    print("=" * 40)
    
    # Clean up test directories
    test_dirs = ['./test_rag_basic', './.chroma', './pocketpro_vector_db']
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    
    test_db_path = Path('./test_rag_basic')
    test_db_path.mkdir(exist_ok=True)
    
    try:
        # Import app components
        sys.path.insert(0, '.')
        from app import SimpleEmbeddingFunction
        import chromadb
        from chromadb.config import Settings
        
        print("✅ Imports successful")
        
        # Initialize ChromaDB
        try:
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(test_db_path.absolute()),
                anonymized_telemetry=False
            )
            client = chromadb.Client(settings)
        except Exception:
            client = chromadb.Client()
        
        print("✅ ChromaDB client initialized")
        
        # Test embedding function
        embedding_func = SimpleEmbeddingFunction()
        test_embeddings = embedding_func(["Small Business Administration provides loans"])
        print(f"✅ Embedding function works - dimension: {len(test_embeddings[0])}")
        
        # Create collection
        collection = client.create_collection(
            name="test_rag_collection",
            embedding_function=embedding_func,
            metadata={"hnsw:space": "cosine"}
        )
        print("✅ Collection created")
        
        # Test RAG workflow
        print("\n📝 Testing RAG Workflow:")
        
        # 1. Add SBA documents
        sba_docs = [
            {
                'text': 'SBA provides small business loans to help entrepreneurs start and grow their businesses.',
                'id': 'sba_loans_1',
                'metadata': {'source': 'sba_guide', 'type': 'loans'}
            },
            {
                'text': 'Business plan writing is essential for securing SBA funding and setting clear business goals.',
                'id': 'business_plan_1', 
                'metadata': {'source': 'business_guide', 'type': 'planning'}
            },
            {
                'text': 'SBA 504 loans are specifically designed for purchasing real estate and equipment.',
                'id': 'sba_504_1',
                'metadata': {'source': 'loan_types', 'type': 'real_estate'}
            }
        ]
        
        for doc in sba_docs:
            collection.add(
                documents=[doc['text']],
                ids=[doc['id']],
                metadatas=[doc['metadata']]
            )
        
        print(f"   ✅ Added {len(sba_docs)} documents")
        
        # 2. Test search functionality
        queries = [
            'How can I get SBA loans?',
            'What is business plan writing?',
            'Tell me about SBA 504 loans'
        ]
        
        for query in queries:
            results = collection.query(
                query_texts=[query],
                n_results=2
            )
            
            print(f"\n   🔍 Query: '{query}'")
            if results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    print(f"      📄 Result {i+1}: {doc[:60]}...")
                    if results['metadatas'][0][i]:
                        print(f"         📊 Metadata: {results['metadatas'][0][i]}")
            else:
                print("      ❌ No results found")
        
        # 3. Test document count
        count = collection.count()
        print(f"\n   📊 Total documents in collection: {count}")
        
        # 4. Test RAG chat simulation
        print("\n💬 Testing RAG Chat Simulation:")
        user_query = "How do I start a small business with SBA help?"
        
        # Retrieve relevant documents
        search_results = collection.query(
            query_texts=[user_query],
            n_results=2
        )
        
        if search_results['documents'][0]:
            context = " ".join(search_results['documents'][0])
            response = f"Based on SBA resources: {context[:200]}..."
            print(f"   🤖 RAG Response: {response}")
        else:
            print("   ❌ No context found for RAG response")
        
        print("\n🎉 RAG functionality test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if test_db_path.exists():
            shutil.rmtree(test_db_path)

if __name__ == "__main__":
    success = test_chromadb_rag()
    if success:
        print("\n✅ RAG system is working correctly!")
        print("You can now test the Flask app endpoints.")
    else:
        print("\n❌ RAG system has issues that need to be resolved.")
    
    sys.exit(0 if success else 1)
