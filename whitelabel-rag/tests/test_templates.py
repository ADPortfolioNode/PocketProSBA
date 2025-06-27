"""
Tests for template rendering and frontend functionality
"""

import pytest
import os

def test_index_template_exists():
    """Test that the index.html template exists."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'app', 'templates', 'index.html'
    )
    assert os.path.exists(template_path), "index.html template should exist"

def test_index_route_renders_template(client):
    """Test that the index route renders the template successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'WhiteLabelRAG' in response.data
    assert b'AI Assistant' in response.data

def test_static_css_exists():
    """Test that the CSS file exists."""
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'app', 'static', 'css', 'style.css'
    )
    assert os.path.exists(css_path), "style.css should exist"

def test_static_js_exists():
    """Test that the JavaScript file exists."""
    js_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'app', 'static', 'js', 'app.js'
    )
    assert os.path.exists(js_path), "app.js should exist"

def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'WhiteLabelRAG'