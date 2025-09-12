import pytest
from unittest.mock import patch, MagicMock
from services.SBA_Content import SBAContentAPI

class TestSBAContentAPI:
    @pytest.fixture
    def sba_api(self):
        return SBAContentAPI()

    @patch('services.SBA_Content.requests.get')
    def test_search_articles_success(self, mock_get, sba_api):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{'id': 1, 'title': 'Test Article'}],
            'total_pages': 1
        }
        mock_get.return_value = mock_response

        result = sba_api.search_articles(query='test', page=1)

        assert 'results' in result
        assert len(result['results']) == 1
        assert result['results'][0]['title'] == 'Test Article'
        mock_get.assert_called_once_with(
            'https://www.sba.gov/api/content/search/articles.json',
            params={'query': 'test', 'page': 1},
            timeout=10
        )

    @patch('services.SBA_Content.requests.get')
    def test_search_articles_request_error(self, mock_get, sba_api):
        mock_get.side_effect = Exception('Connection error')

        result = sba_api.search_articles(query='test')

        assert 'error' in result
        assert 'Connection error' in result['error']

    @patch('services.SBA_Content.requests.get')
    def test_get_article_success(self, mock_get, sba_api):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 1,
            'title': 'Test Article',
            'body': 'Article content'
        }
        mock_get.return_value = mock_response

        result = sba_api.get_article(1)

        assert result['id'] == 1
        assert result['title'] == 'Test Article'
        mock_get.assert_called_once_with(
            'https://www.sba.gov/api/content/search/articles/1.json',
            timeout=10
        )

    @patch('services.SBA_Content.requests.get')
    def test_search_courses_success(self, mock_get, sba_api):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{'id': 1, 'title': 'Test Course'}],
            'total_pages': 1
        }
        mock_get.return_value = mock_response

        result = sba_api.search_courses(query='test')

        assert len(result['results']) == 1
        assert result['results'][0]['title'] == 'Test Course'

    @patch('services.SBA_Content.requests.get')
    def test_search_offices_success(self, mock_get, sba_api):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{'id': 1, 'title': 'Test Office'}],
            'total_pages': 1
        }
        mock_get.return_value = mock_response

        result = sba_api.search_offices()

        assert len(result['results']) == 1
        assert result['results'][0]['title'] == 'Test Office'

    @patch('services.SBA_Content.requests.get')
    def test_get_node_success(self, mock_get, sba_api):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 1,
            'title': 'Test Node',
            'type': 'article'
        }
        mock_get.return_value = mock_response

        result = sba_api.get_node(1)

        assert result['id'] == 1
        assert result['title'] == 'Test Node'

    @patch('services.SBA_Content.requests.get')
    def test_request_timeout(self, mock_get, sba_api):
        import requests
        mock_get.side_effect = requests.Timeout('Request timed out')

        result = sba_api.search_articles()

        assert 'error' in result
        assert 'Request timed out' in result['error']

    @patch('services.SBA_Content.requests.get')
    def test_http_error(self, mock_get, sba_api):
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError('404 Not Found')
        mock_get.return_value = mock_response

        result = sba_api.search_articles()

        assert 'error' in result
        assert '404 Not Found' in result['error']
