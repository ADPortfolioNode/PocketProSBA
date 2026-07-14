import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from routes.sba import sba_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(sba_bp, url_prefix='/api/sba')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

class TestSBARoutes:
    @patch('routes.sba.sba_api')
    def test_search_articles_success(self, mock_sba_api, client):
        mock_sba_api.search_articles.return_value = {
            'results': [{'id': 1, 'title': 'Test Article'}],
            'total_pages': 1
        }

        response = client.get('/api/sba/content/articles?query=test&page=1')

        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert 'totalPages' in data
        assert 'currentPage' in data
        assert len(data['items']) == 1
        assert data['items'][0]['title'] == 'Test Article'

    @patch('routes.sba.sba_api')
    def test_search_articles_error(self, mock_sba_api, client):
        mock_sba_api.search_articles.return_value = {'error': 'API Error'}

        response = client.get('/api/sba/content/articles?query=test&page=1')

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'API Error'

    @patch('routes.sba.sba_api')
    def test_get_article_details_success(self, mock_sba_api, client):
        mock_sba_api.get_article.return_value = {
            'id': 1,
            'title': 'Test Article',
            'body': 'Article content'
        }

        response = client.get('/api/sba/content/articles/1')

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == 1
        assert data['title'] == 'Test Article'

    @patch('routes.sba.sba_api')
    def test_get_article_details_not_found(self, mock_sba_api, client):
        mock_sba_api.get_article.return_value = {'error': 'Article not found'}

        response = client.get('/api/sba/content/articles/999')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    @patch('routes.sba.sba_api')
    def test_search_courses_success(self, mock_sba_api, client):
        mock_sba_api.search_courses.return_value = {
            'results': [{'id': 1, 'title': 'Test Course'}],
            'total_pages': 1
        }

        response = client.get('/api/sba/content/courses?query=test&page=1')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['items']) == 1
        assert data['items'][0]['title'] == 'Test Course'

    @patch('routes.sba.sba_api')
    def test_search_offices_without_query(self, mock_sba_api, client):
        mock_sba_api.search_offices.return_value = {
            'results': [{'id': 1, 'title': 'Test Office'}],
            'total_pages': 1
        }

        response = client.get('/api/sba/content/offices?page=1')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['items']) == 1

    @patch('routes.sba.sba_api')
    def test_get_node_details_success(self, mock_sba_api, client):
        mock_sba_api.get_node.return_value = {
            'id': 1,
            'title': 'Test Node',
            'type': 'article'
        }

        response = client.get('/api/sba/content/node/1')

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == 1
        assert data['title'] == 'Test Node'

    def test_invalid_route(self, client):
        response = client.get('/api/sba/content/invalid')
        assert response.status_code == 404
