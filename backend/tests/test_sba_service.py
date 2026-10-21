"""Unit tests for SBAContentAPI.

The service now layers sources: legacy JSON content API -> live sba.gov HTML
pages -> curated static catalog. These tests inject a fake requests session so
they never touch the network, and assert the current, documented behavior.
"""
import pytest
import requests
from unittest.mock import MagicMock

from backend.services import SBA_Content
from backend.services.SBA_Content import SBAContentAPI, SBA_CONTENT_BASE


def _json_response(payload, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture(autouse=True)
def _clear_cache():
    SBA_Content.clear_sba_cache()
    yield
    SBA_Content.clear_sba_cache()


@pytest.fixture
def session():
    s = MagicMock(spec=requests.Session)
    s.headers = {}
    return s


@pytest.fixture
def sba_api(session):
    return SBAContentAPI(session=session)


class TestSBAContentAPI:
    def test_search_articles_success(self, sba_api, session):
        session.get.return_value = _json_response(
            {'results': [{'id': 1, 'title': 'Test Article'}], 'total_pages': 1}
        )

        result = sba_api.search_articles(query='test', page=1)

        assert result['source'] == 'legacy_json'
        assert len(result['results']) == 1
        assert result['results'][0]['title'] == 'Test Article'
        assert result['items'] == result['results']
        session.get.assert_called_once_with(
            f'{SBA_CONTENT_BASE.rstrip("/")}/articles.json',
            params={'query': 'test', 'page': 1},
            timeout=12,
        )

    def test_search_articles_request_error_falls_back_to_static(self, sba_api, session):
        session.get.side_effect = requests.RequestException('Connection error')

        result = sba_api.search_articles(query='')

        # Network down: still returns display-ready cards, flagged as not current
        assert result['source'] == 'static'
        assert result['degraded'] is True
        assert result['is_current'] is False
        assert result['count'] > 0

    def test_get_article_success(self, sba_api, session):
        session.get.return_value = _json_response(
            {'id': 1, 'title': 'Test Article', 'body': 'Article content'}
        )

        result = sba_api.get_article(1)

        assert result['success'] is True
        assert result['title'] == 'Test Article'
        session.get.assert_called_once_with(
            f'{SBA_CONTENT_BASE.rstrip("/")}/articles/1.json',
            params=None,
            timeout=12,
        )

    def test_search_courses_success(self, sba_api, session):
        session.get.return_value = _json_response(
            {'results': [{'id': 1, 'title': 'Test Course'}], 'total_pages': 1}
        )

        result = sba_api.search_courses(query='test')

        assert len(result['results']) == 1
        assert result['results'][0]['title'] == 'Test Course'

    def test_search_offices_success(self, sba_api, session):
        session.get.return_value = _json_response(
            {'results': [{'id': 1, 'title': 'Test Office'}], 'total_pages': 1}
        )

        result = sba_api.search_offices()

        assert len(result['results']) == 1
        assert result['results'][0]['title'] == 'Test Office'

    def test_get_node_success(self, sba_api, session):
        session.get.return_value = _json_response(
            {'id': 1, 'title': 'Test Node', 'type': 'article'}
        )

        result = sba_api.get_node(1)

        assert result['id'] == 1
        assert result['title'] == 'Test Node'

    def test_get_json_timeout_returns_error(self, sba_api, session):
        session.get.side_effect = requests.Timeout('Request timed out')

        result = sba_api.get_node(1)

        assert result['success'] is False
        assert 'Request timed out' in result['error']

    def test_get_json_http_error_returns_error(self, sba_api, session):
        resp = _json_response({})
        resp.raise_for_status.side_effect = requests.HTTPError('404 Not Found')
        session.get.return_value = resp

        result = sba_api.get_node(1)

        assert result['success'] is False
        assert '404 Not Found' in result['error']

    def test_rate_limited(self, sba_api, session):
        session.get.return_value = _json_response({}, status=429)

        result = sba_api.get_node(1)

        assert result == {'error': 'rate_limited', 'status_code': 429, 'success': False}
