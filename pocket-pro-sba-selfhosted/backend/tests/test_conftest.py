"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from backend.app import create_app


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    # Use a temporary database for tests
    db_fd, db_path = tempfile.mkstemp()

    # Set test configuration
    test_config = {
        'TESTING': True,
        'DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key',
        'CHROMA_HOST': 'localhost',
        'CHROMA_PORT': '8000',
        'OPENAI_API_KEY': 'test-key'
    }

    app = create_app(test_config)

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def mock_chromadb():
    """Mock ChromaDB connections for all tests."""
    with patch('backend.services.chroma_fixed.ChromaService') as mock_chroma:
        mock_instance = MagicMock()
        mock_instance.initialize.return_value = None
        mock_instance.client = MagicMock()
        mock_instance.collection = MagicMock()
        mock_instance.add_documents.return_value = None
        mock_instance.query.return_value = {'documents': [], 'metadatas': []}
        mock_chroma.return_value = mock_instance

        with patch('backend.services.rag.get_rag_manager') as mock_rag:
            mock_rag_instance = MagicMock()
            mock_rag_instance.query.return_value = {'results': []}
            mock_rag_instance.add_documents.return_value = None
            mock_rag.return_value = mock_rag_instance

            yield


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch('openai.ChatCompletion.create') as mock_chat:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Mocked response"
        mock_chat.return_value = mock_response
        yield mock_chat
