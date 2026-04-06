import unittest
from config import Config

class TestConfig(unittest.TestCase):
    def test_debug_default(self):
        self.assertFalse(Config.DEBUG)

    def test_database_url(self):
        self.assertIn('sqlite', Config.DATABASE_URL)

if __name__ == '__main__':
    unittest.main()
