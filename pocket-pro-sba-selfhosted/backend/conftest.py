import os

import pytest

from backend.app import create_app
from backend.models.chat import db


@pytest.fixture
def app():
    """Create application for testing with in-memory database."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if db_path and db_path != ':memory:' and os.path.exists(db_path):
                os.remove(db_path)


@pytest.fixture
def client(app):
    return app.test_client()