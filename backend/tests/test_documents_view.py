"""Docs tab viewer: GET /api/documents/view/<filename> returns an uploaded
file for in-app inspection, using the same extraction path as upload.

Auth, upload folder, and RAG stubbing follow test_documents_list.py.
"""
import io

import pytest

from backend.app import create_app
from backend.routes import files as files_routes
from backend.tests.auth_helpers import authenticate


@pytest.fixture
def client(tmp_path, monkeypatch):
    upload_dir = tmp_path / 'custom-uploads'
    monkeypatch.setattr(files_routes, 'UPLOAD_FOLDER', str(upload_dir))
    # Never let the soft RAG ingest touch Chroma or the network in this test.
    monkeypatch.setattr('backend.services.rag.get_rag_manager', lambda: None, raising=False)
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as c:
        # Upload and view are auth_required.
        authenticate(c, app)
        c.upload_dir = upload_dir
        yield c


def _upload(client, name, data):
    res = client.post(
        '/api/documents/upload',
        data={'file': (io.BytesIO(data), name)},
        content_type='multipart/form-data',
    )
    assert res.status_code == 200, res.get_data(as_text=True)


def test_view_returns_uploaded_text_content(client):
    _upload(client, 'plan.txt', b'hello sba viewer')
    res = client.get('/api/documents/view/plan.txt')
    assert res.status_code == 200
    body = res.get_json()
    assert body['filename'] == 'plan.txt'
    assert body['text'] == 'hello sba viewer'
    assert body['extractable'] is True
    assert body['truncated'] is False
    assert body['size'] == len(b'hello sba viewer')


def test_view_missing_file_is_404_not_an_error_dump(client):
    res = client.get('/api/documents/view/nope.txt')
    assert res.status_code == 404
    assert res.get_json() == {'error': 'File not found'}


def test_view_rejects_path_traversal(client):
    _upload(client, 'plan.txt', b'hello sba viewer')
    res = client.get('/api/documents/view/..%2Fplan.txt')
    assert res.status_code == 404
    res = client.get('/api/documents/view/%2E%2E%2Fplan.txt')
    assert res.status_code == 404


def test_view_binary_without_extractable_text_is_honest(client):
    # Legacy .doc binaries cannot be extracted with the installed libraries:
    # the endpoint must say so, not invent content.
    client.upload_dir.mkdir(parents=True)
    (client.upload_dir / 'old.doc').write_bytes(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1garbage')
    res = client.get('/api/documents/view/old.doc')
    assert res.status_code == 200
    body = res.get_json()
    assert body['extractable'] is False
    assert body['text'] == ''
