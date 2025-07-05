"""
Simple ChromaDB test to verify functionality
Run this to check if ChromaDB is working properly
"""
import os
import shutil
import sys
from pathlib import Path

def test_chromadb_basic():
    """Test basic ChromaDB functionality"""
    
    print("🧪 Testing ChromaDB Basic Functionality")
    print("=" * 40)
    
    # Clean up any existing directories
    test_dirs = ['./test_simple_chromadb', './.chroma', './chroma_db']
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"   🧹 Cleaned up: {dir_path}")
    
    # Create test directory
    test_db_path = Path('./test_simple_chromadb')
    test_db_path.mkdir(exist_ok=True)
    
    try:
        import chromadb
        from chromadb.config import Settings
        print("✅ ChromaDB imported successfully")
        
        # Initialize client using ChromaDB 0.3.29 compatible method
        try:
            # Method 1: Use Settings
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(test_db_path.absolute()),
                anonymized_telemetry=False
            )
            client = chromadb.Client(settings)
            print("✅ ChromaDB client created with Settings")
        except Exception as settings_error:
            print(f"⚠️ Settings method failed: {settings_error}")
            try:
                # Method 2: Default client
                client = chromadb.Client()
                print("✅ ChromaDB client created with default method")
            except Exception as default_error:
                print(f"❌ All client methods failed: {default_error}")
                return False
        
        # Create simple embedding function
        class SimpleEmbedding:
            def __call__(self, texts):
                import hashlib
                import re
                
                embeddings = []
                for text in texts:
                    # Clean and process text
                    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', str(text).lower())
                    
                    # Create hash-based embedding
                    text_hash = hashlib.sha256(clean_text.encode()).hexdigest()
                    
                    # Convert to numerical embedding
                    embedding = []
                    for i in range(0, min(len(text_hash), 768), 2):
                        try:
                            val = int(text_hash[i:i+2], 16) / 255.0
                            embedding.append(float(val))
                        except:
                            embedding.append(0.0)
                    
                    # Ensure 384 dimensions
                    while len(embedding) < 384:
                        embedding.append(0.0)
                    
                    embeddings.append(embedding[:384])
                
                return embeddings
        
        embedding_function = SimpleEmbedding()
        print("✅ Embedding function created")
        
        # Test embedding function
        test_embeddings = embedding_function(["test document"])
        print(f"✅ Embedding test successful - dimension: {len(test_embeddings[0])}")
        
        # Create collection - REQUIRED for ChromaDB 0.3.29
        collection = client.create_collection(
            name="test_collection",
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        print("✅ Collection created successfully")
        
        # Add document
        test_doc = "This is a test document for ChromaDB verification"
        collection.add(
            documents=[test_doc],
            ids=["test_doc_1"],
            metadatas=[{"source": "test", "type": "verification"}]
        )
        print("✅ Document added successfully")
        
        # Query document
        results = collection.query(
            query_texts=["test document verification"],
            n_results=1
        )
        print("✅ Query executed successfully")
        print(f"   Found {len(results['documents'][0])} documents")
        
        if results['documents'][0]:
            print(f"   Document content: {results['documents'][0][0][:50]}...")
            print(f"   Document metadata: {results['metadatas'][0][0]}")
        
        # Test document count
        count = collection.count()
        print(f"✅ Collection count: {count} documents")
        
        # Clean up
        collection.delete(ids=["test_doc_1"])
        print("✅ Document deleted successfully")
        
        final_count = collection.count()
        print(f"✅ Final count after deletion: {final_count} documents")
        
        print("\n🎉 ChromaDB is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB test failed: {str(e)}")
        import traceback
        print("📋 Full error traceback:")
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test directory
        if test_db_path.exists():
            try:
                shutil.rmtree(test_db_path)
                print("🧹 Test directory cleaned up")
            except Exception as e:
                print(f"⚠️ Could not clean up test directory: {e}")

def test_app_import():
    """Test if app.py can be imported without errors"""
    print("\n🧪 Testing app.py import...")
    
    try:
        # Add current directory to path
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        
        # Try to import key components
        from app import SimpleEmbeddingFunction
        print("✅ SimpleEmbeddingFunction imported successfully")
        
        # Test the embedding function
        embedding_func = SimpleEmbeddingFunction()
        test_embeddings = embedding_func(["test"])
        print(f"✅ App embedding function works - dimension: {len(test_embeddings[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ App import test failed: {e}")
        return False

def main():
    """Main test procedure"""
    success_basic = test_chromadb_basic()
    success_app = test_app_import()
    
    print("\n" + "=" * 50)
    
    if success_basic and success_app:
        print("🎉 All tests passed! ChromaDB is ready to use.")
        print("\nYou can now run:")
        print("   python app.py")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        if not success_basic:
            print("   - Basic ChromaDB functionality issue")
        if not success_app:
            print("   - App integration issue")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
