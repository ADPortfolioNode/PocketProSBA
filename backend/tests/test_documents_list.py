"""Docs tab: GET /api/documents/list lists the files the upload routes saved.

Uploads are written by routes/files.process_upload() to files.UPLOAD_FOLDER
(the UPLOAD_FOLDER env var, default "uploads"). The list endpoint used a
hard-coded relative "uploads", so with UPLOAD_FOLDER set the Docs tab stayed
empty after a successful upload.
"""
import io

import pytest

from backend.app import create_app
from backend.routes import files as files_routes


@pytest.fixture
def client(tmp_path, monkeypatch):
    upload_dir = tmp_path / 'custom-uploads'
    monkeypatch.setattr(files_routes, 'UPLOAD_FOLDER', str(upload_dir))
    # Never let the soft RAG ingest touch Chroma or the network in this test.
    monkeypatch.setattr('backend.services.rag.get_rag_manager', lambda: None, raising=False)
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as c:
        c.upload_dir = upload_dir
        yield c


def test_list_is_empty_before_any_upload(client):
    res = client.get('/api/documents/list')
    assert res.status_code == 200
    assert res.get_json() == {'files': []}


def test_uploaded_file_shows_up_in_list(client):
    res = client.post(
        '/api/documents/upload',
        data={'file': (io.BytesIO(b'hello sba'), 'plan.txt')},
        content_type='multipart/form-data',
    )
    assert res.status_code == 200, res.get_data(as_text=True)
    assert (client.upload_dir / 'plan.txt').exists()

    listed = client.get('/api/documents/list').get_json()['files']
    assert [f['filename'] for f in listed] == ['plan.txt']
    assert listed[0]['size'] == len(b'hello sba')


def test_list_ignores_subdirectories_and_sorts_by_name(client):
    client.upload_dir.mkdir(parents=True)
    (client.upload_dir / 'b.md').write_text('b')
    (client.upload_dir / 'a.txt').write_text('a')
    (client.upload_dir / 'nested').mkdir()
    listed = client.get('/api/documents/list').get_json()['files']
    assert [f['filename'] for f in listed] == ['a.txt', 'b.md']
