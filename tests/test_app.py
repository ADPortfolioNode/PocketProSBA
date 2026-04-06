import pytest
from app import app
from models import Session, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello, World!' in response.data

class TestApp:
    def setup_method(self):
        self.app = app.test_client()
        self.session = Session()
        # Add test user
        user = User(name='Test User', email='test@example.com')
        self.session.add(user)
        self.session.commit()
        self.user_id = user.id

    def test_get_user(self):
        response = self.app.get(f'/user/{self.user_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data

    def teardown_method(self):
        self.session.rollback()
        self.session.close()
