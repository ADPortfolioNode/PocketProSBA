"""
Script to fix ChromaDB configuration and test functionality
"""
import os
import shutil
import sys
from pathlib import Path

def cleanup_chromadb_directories():
    """Clean up all potential ChromaDB conflict directories"""
    current_dir = Path.cwd()
    
    # List of directories that might cause conflicts
    conflict_dirs = [
        current_dir / '.chroma',
        current_dir / 'chroma_db', 
        current_dir / '.chromadb',
        current_dir / 'pocketpro_chromadb',
        current_dir / 'pocketpro_vector_db',
        current_dir / 'test_pocketpro_chromadb',
        current_dir / 'test_chromadb_data'
    ]
    
    print("🧹 Cleaning up ChromaDB directories...")
    
    for dir_path in conflict_dirs:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"   ✅ Removed: {dir_path}")
            except Exception as e:
                print(f"   ⚠️ Could not remove {dir_path}: {e}")
        else:
            print(f"   ℹ️ Not found: {dir_path}")

def test_chromadb_installation():
    """Test if ChromaDB is properly installed"""
    try:
        import chromadb
        print(f"✅ ChromaDB version: {chromadb.__version__}")
        return True
    except ImportError as e:
        print(f"❌ ChromaDB not installed: {e}")
        return False

def test_chromadb_functionality():
    """Test ChromaDB with simple embedding function"""
    try:
        import chromadb
        from chromadb.config import Settings
        import numpy as np
        
        # Create test directory
        test_path = Path('./test_chromadb_fix')
        if test_path.exists():
            shutil.rmtree(test_path)
        test_path.mkdir()
        
        print("🔧 Testing ChromaDB functionality...")
        
        # Initialize client using ChromaDB 0.3.29 API
        try:
            # Method 1: Use Settings for ChromaDB 0.3.29
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(test_path.absolute()),
                anonymized_telemetry=False
            )
            client = chromadb.Client(settings)
            print("   ✅ Client initialized with Settings")
        except Exception as settings_error:
            print(f"   ⚠️ Settings method failed: {settings_error}")
            try:
                # Method 2: Simple client for 0.3.29
                client = chromadb.Client()
                print("   ✅ Client initialized with default method")
            except Exception as default_error:
                print(f"   ❌ All client methods failed: {default_error}")
                return False
        
        # Simple embedding function compatible with ChromaDB 0.3.29
        class TestEmbedding:
            def __call__(self, texts):
                import re
                import hashlib
                from collections import Counter
                
                embeddings = []
                for text in texts:
                    # Simple text processing
                    words = re.findall(r'\w+', str(text).lower())
                    
                    # Create hash-based embedding
                    text_str = ' '.join(words)
                    text_hash = hashlib.sha256(text_str.encode()).hexdigest()
                    
                    # Convert hash to embedding
                    embedding = []
                    for i in range(0, min(len(text_hash), 768), 2):
                        try:
                            val = int(text_hash[i:i+2], 16) / 255.0
                            embedding.append(float(val))
                        except:
                            embedding.append(0.0)
                    
                    # Pad to 384 dimensions
                    while len(embedding) < 384:
                        embedding.append(0.0)
                    
                    embeddings.append(embedding[:384])
                
                return embeddings
        
        embedding_func = TestEmbedding()
        
        # Test embedding
        test_emb = embedding_func(["test document"])
        print(f"   ✅ Embedding created: {len(test_emb[0])} dimensions")
        
        # Create collection with embedding function for ChromaDB 0.3.29
        try:
            collection = client.create_collection(
                name="test_fix_collection",
                embedding_function=embedding_func,
                metadata={"hnsw:space": "cosine"}
            )
            print("   ✅ Collection created with embedding function")
        except Exception as collection_error:
            print(f"   ❌ Collection creation failed: {collection_error}")
            return False
        
        # Add and query
        collection.add(
            documents=["Test document for ChromaDB fix"],
            ids=["fix_test_1"],
            metadatas=[{"test": "fix"}]
        )
        print("   ✅ Document added")
        
        results = collection.query(
            query_texts=["test document"],
            n_results=1
        )
        print(f"   ✅ Query successful: {len(results['documents'][0])} results")
        
        # Test deletion
        collection.delete(ids=["fix_test_1"])
        print("   ✅ Document deletion successful")
        
        # Cleanup
        shutil.rmtree(test_path)
        print("🎉 ChromaDB is working properly!")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB functionality test failed: {e}")
        if 'test_path' in locals() and test_path.exists():
            shutil.rmtree(test_path)
        return False

def check_app_configuration():
    """Check app.py ChromaDB configuration"""
    app_file = Path('./app.py')
    
    if not app_file.exists():
        print("❌ app.py not found")
        return False
    
    print("🔧 Checking app.py ChromaDB configuration...")
    
    try:
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key components
        checks = {
            'SimpleEmbeddingFunction': 'SimpleEmbeddingFunction' in content,
            'PersistentClient': 'PersistentClient' in content,
            'cleanup_chroma_directories': 'cleanup_chroma_directories' in content,
            'pocketpro_vector_db': 'pocketpro_vector_db' in content
        }
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "⚠️"
            print(f"   {status} {check_name}: {'Found' if passed else 'Missing'}")
        
        if all(checks.values()):
            print("   ✅ App configuration appears correct")
            return True
        else:
            print("   ⚠️ Some ChromaDB components may be missing")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading app.py: {e}")
        return False

def set_environment_variables():
    """Set up environment variables for ChromaDB"""
    print("🔧 Setting up environment variables...")
    
    env_vars = {
        'CHROMA_DB_IMPL': 'duckdb+parquet',
        'CHROMA_DB_PATH': './pocketpro_vector_db'
    }
    
    for var, value in env_vars.items():
        os.environ[var] = value
        print(f"   ✅ {var} = {value}")

def main():
    """Main fix procedure"""
    print("🚀 ChromaDB Fix Tool for PocketPro SBA")
    print("=" * 50)
    
    # Step 1: Clean up directories
    cleanup_chromadb_directories()
    print()
    
    # Step 2: Test installation
    if not test_chromadb_installation():
        print("\n❌ ChromaDB is not installed. Please install with:")
        print("   pip install chromadb==0.3.29")
        return False
    print()
    
    # Step 3: Set environment variables
    set_environment_variables()
    print()
    
    # Step 4: Test functionality
    if not test_chromadb_functionality():
        print("\n❌ ChromaDB functionality test failed")
        return False
    print()
    
    # Step 5: Check app configuration
    check_app_configuration()
    print()
    
    print("🎉 ChromaDB fix completed successfully!")
    print("\nNext steps:")
    print("1. Run: python test_chromadb_simple.py")
    print("2. Run: python app.py")
    print("3. Check startup logs for ChromaDB initialization")
    print("4. Test endpoints: /health, /api/info")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
