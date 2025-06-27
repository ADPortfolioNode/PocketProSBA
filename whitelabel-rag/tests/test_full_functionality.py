import pytest
import io

@pytest.fixture
def client():
    from app import create_app
    app = create_app()
    # FastAPI app does not have 'config' attribute or 'test_client' method
    # Use TestClient from starlette.testclient for testing FastAPI apps
    from starlette.testclient import TestClient
    client = TestClient(app)
    yield client

def test_document_upload_search_and_chat(client):
    # Upload a document
    data = {
        'file': (io.BytesIO(b'This is a test document content for full functionality'), 'full_test_doc.txt')
    }
    upload_resp = client.post('/api/files', data=data, content_type='multipart/form-data')
    assert upload_resp.status_code == 200
    upload_json = upload_resp.json()
    assert 'message' in upload_json
    assert 'filename' in upload_json

    # Query the document
    query_resp = client.post('/api/query', json={'query': 'test document'})
    assert query_resp.status_code == 200
    query_json = query_resp.json()
    assert query_json.get('success') is True
    assert 'rag_response' in query_json

    # Chat interaction
    chat_resp = client.post('/api/chat', json={'message': 'Tell me about the test document'})
    assert chat_resp.status_code == 200
    chat_json = chat_resp.json()
    assert 'response' in chat_json
    assert isinstance(chat_json['response'], str)
