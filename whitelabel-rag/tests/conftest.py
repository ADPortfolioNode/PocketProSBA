import os
import sys
import pytest
import shutil
from pathlib import Path

# Add the root directory to sys.path for imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Setup test environment with ChromaDB configuration"""
    # Create unique test data directory to avoid conflicts
    test_data_dir = Path('./test_pocketpro_chromadb')
    
    # Clean up any existing test directory
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    test_data_dir.mkdir(exist_ok=True)
    
    # Set test environment variables to avoid ChromaDB conflicts
    os.environ.update({
        'TESTING': 'true',
        'CHROMA_DB_PATH': str(test_data_dir.absolute()),
        'FLASK_DEBUG': 'false',
        'LOG_LEVEL': 'WARNING',
        'CHROMA_DB_IMPL': 'duckdb+parquet'
    })
    
    # Clean up any .chroma directories that might cause conflicts
    current_dir = Path.cwd()
    chroma_dirs = [
        current_dir / '.chroma',
        current_dir / 'chroma_db',
        current_dir / '.chromadb',
        current_dir / 'pocketpro_vector_db'
    ]
    
    for chroma_dir in chroma_dirs:
        if chroma_dir.exists():
            try:
                shutil.rmtree(chroma_dir)
                print(f"Cleaned up {chroma_dir}")
            except Exception as e:
                print(f"Could not clean {chroma_dir}: {e}")
    
    yield
    
    # Cleanup after tests
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)

@pytest.fixture
def test_app():
    """Create test Flask app with fresh ChromaDB setup"""
    # Import after environment is set up
    from app import app
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def fresh_chromadb():
    """Initialize a fresh ChromaDB instance for testing using ChromaDB 0.3.29 API"""
    import chromadb
    from chromadb.config import Settings
    
    # Create test-specific directory
    test_db_path = Path('./test_fresh_chromadb')
    if test_db_path.exists():
        shutil.rmtree(test_db_path)
    test_db_path.mkdir()
    
    try:
        # Initialize fresh ChromaDB client using 0.3.29 compatible method
        try:
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(test_db_path.absolute()),
                anonymized_telemetry=False
            )
            client = chromadb.Client(settings)
        except Exception:
            # Fallback to default client
            client = chromadb.Client()
        
        # Create simple embedding function for testing
        class TestEmbeddingFunction:
            def __call__(self, texts):
                import hashlib
                embeddings = []
                for text in texts:
                    # Create simple hash-based embedding
                    text_hash = hashlib.sha256(str(text).encode()).hexdigest()
                    embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, min(len(text_hash), 768), 2)]
                    while len(embedding) < 384:
                        embedding.append(0.0)
                    embeddings.append(embedding[:384])
                return embeddings
        
        embedding_function = TestEmbeddingFunction()
        
        # Create test collection
        collection = client.create_collection(
            name="test_collection",
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        
        yield client, collection
        
    except Exception as e:
        print(f"Failed to create fresh ChromaDB: {e}")
        yield None, None
    finally:
        if test_db_path.exists():
            shutil.rmtree(test_db_path)

@pytest.fixture
def mock_chromadb_available():
    """Mock ChromaDB availability for testing"""
    try:
        from app import collection, chroma_client
        return collection is not None and chroma_client is not None
    except ImportError:
        return False

@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        {
            'id': 'doc1',
            'text': 'Small Business Administration provides loans and grants to help entrepreneurs start and grow their businesses.',
            'metadata': {'source': 'sba_guide', 'type': 'business_info'}
        },
        {
            'id': 'doc2', 
            'text': 'SBA 504 loans are designed for purchasing real estate or equipment for small businesses.',
            'metadata': {'source': 'sba_loans', 'type': 'loan_info'}
        },
        {
            'id': 'doc3',
            'text': 'Business plan writing is essential for securing funding and setting clear goals for your startup.',
            'metadata': {'source': 'business_planning', 'type': 'planning_guide'}
        }
    ]

@pytest.fixture
def sample_queries():
    """Sample queries for testing RAG functionality"""
    return [
        'How can I get SBA loans?',
        'What is business plan writing?',
        'Tell me about small business grants',
        'How do I start a business?'
    ]

import io
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_llm(monkeypatch):
    mock = MagicMock()
    mock.generate_text.return_value = '{"steps": [{"step_number": 1, "instruction": "Search for information about climate change", "suggested_agent_type": "SearchAgent"}]}'
    monkeypatch.setattr('app.services.llm_factory.LLMFactory.get_llm', lambda: mock)
    return mock

@pytest.fixture
def mock_chroma_service(monkeypatch):
    mock = MagicMock()
    mock.query_documents.return_value = {
        'documents': [['Document content']],
        'metadatas': [[{'source': 'test_source'}]],
        'distances': [[0.1]]
    }
    monkeypatch.setattr('app.services.chroma_service.get_chroma_service_instance', lambda: mock)
    monkeypatch.setattr('app.services.chroma_service.ChromaService', lambda: mock)
    # Patch document processor methods to avoid real PDF parsing errors
    monkeypatch.setattr('app.services.document_processor.DocumentProcessor._extract_text', lambda self, file_path: "Extracted text")
    monkeypatch.setattr('app.services.document_processor.DocumentProcessor._create_chunks', lambda self, text: ["chunk1", "chunk2"])
    monkeypatch.setattr('app.services.document_processor.DocumentProcessor.process_document', lambda self, file_path: {"success": True, "chunks": ["chunk1", "chunk2"]})
    # Patch ChromaService._setup_chroma to no-op to avoid real ChromaDB calls
    monkeypatch.setattr('app.services.chroma_service.ChromaService._setup_chroma', lambda self: None)
    return mock

@pytest.fixture
def temp_pdf(tmp_path):
    # Minimal valid PDF file content
    pdf_content = (
        b'%PDF-1.4\n'
        b'1 0 obj\n'
        b'<< /Type /Catalog /Pages 2 0 R >>\n'
        b'endobj\n'
        b'2 0 obj\n'
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n'
        b'endobj\n'
        b'3 0 obj\n'
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\n'
        b'endobj\n'
        b'4 0 obj\n'
        b'<< /Length 44 >>\n'
        b'stream\n'
        b'BT\n'
        b'/F1 24 Tf\n'
        b'100 700 Td\n'
        b'(Hello, PDF!) Tj\n'
        b'ET\n'
        b'endstream\n'
        b'endobj\n'
        b'xref\n'
        b'0 5\n'
        b'0000000000 65535 f \n'
        b'0000000010 00000 n \n'
        b'0000000060 00000 n \n'
        b'0000000117 00000 n \n'
        b'0000000211 00000 n \n'
        b'trailer\n'
        b'<< /Size 5 /Root 1 0 R >>\n'
        b'startxref\n'
        b'308\n'
        b'%%EOF\n'
    )
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(pdf_content)
    return pdf_file

@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()
