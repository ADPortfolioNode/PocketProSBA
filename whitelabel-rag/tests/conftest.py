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
    """Setup test environment with vector database configuration"""
    # Set test environment variables
    os.environ.update({
        'TESTING': 'true',
        'FLASK_DEBUG': 'false',
        'LOG_LEVEL': 'WARNING',
        'PINECONE_ENVIRONMENT': 'test',
        'USE_PINECONE': 'false'  # Use fallback for tests
    })
    
    yield

@pytest.fixture
def test_app():
    """Create test Flask app with vector store setup"""
    # Import after environment is set up
    from app import app
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def fresh_vector_store():
    """Initialize a fresh vector store for testing"""
    try:
        from app import SimpleVectorStore
        vector_store = SimpleVectorStore()
        yield vector_store
    except Exception as e:
        print(f"Failed to create fresh vector store: {e}")
        yield None

@pytest.fixture
def mock_chromadb_available():
    """Mock vector store availability for testing"""
    try:
        from app import vector_store, rag_system_available
        return vector_store is not None and rag_system_available
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
