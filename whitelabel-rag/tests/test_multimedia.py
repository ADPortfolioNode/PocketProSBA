import io
import pytest

@pytest.fixture
def client():
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.mark.parametrize("filename, content_type", [
    ("test_image.jpg", "image/jpeg"),
    ("test_video.mp4", "video/mp4"),
    ("test_audio.mp3", "audio/mpeg"),
])
def test_multimedia_upload_and_info(client, filename, content_type):
    # Prepare a dummy file content
    data = {
        'file': (io.BytesIO(b"dummy data for testing"), filename)
    }
    
    # Test upload endpoint
    response = client.post('/api/multimedia/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'message' in json_data
    assert 'filename' in json_data
    assert json_data['filename'] == filename
    
    # Test info endpoint
    response_info = client.get(f"/api/multimedia/info/{filename}")
    assert response_info.status_code == 200
    info_data = response_info.get_json()
    assert 'file_info' in info_data
    assert info_data['file_info']['filename'] == filename
    assert 'size' in info_data['file_info']
    assert 'modified' in info_data['file_info']

@pytest.mark.parametrize("filename", [
    "unsupported_file.txt",
    "malicious.exe",
])
def test_multimedia_upload_unsupported_file(client, filename):
    data = {
        'file': (io.BytesIO(b"dummy data"), filename)
    }
    response = client.post('/api/multimedia/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
