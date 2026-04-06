import unittest
from models import User, Session

class TestModels(unittest.TestCase):
    def setUp(self):
        self.session = Session()

    def test_user_creation(self):
        user = User(name='Test', email='test@example.com')
        self.session.add(user)
        self.session.commit()
        self.assertIsNotNone(user.id)

    def tearDown(self):
        self.session.rollback()
        self.session.close()
