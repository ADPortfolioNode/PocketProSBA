import pytest
import os
from app import create_app
from config import TestConfig
from models.chat import db

@pytest.fixture
def app():
    """Create application for testing with test database configuration"""
    app = create_app(config_class=TestConfig)
    
    # Create test database tables
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Clean up test database after tests
    with app.app_context():
        db.drop_all()
        # Remove test database file if using SQLite
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                os.remove(db_path)

@pytest.fixture
def client(app):
    return app.test_client()
