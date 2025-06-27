import os
import io
import pytest
from app import create_app
from starlette.testclient import TestClient

def test_file_upload(tmp_path):
    app = create_app()
    client = TestClient(app)

    data = {
        'file': (io.BytesIO(b"Hello world!"), 'test.txt')
    }
    response = client.post('/api/files', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert 'File uploaded successfully' in response.json().get('message', '')
    uploaded_file = tmp_path / 'test.txt'
    assert uploaded_file.exists()
