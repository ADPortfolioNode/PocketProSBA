import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class FrontendLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.get("http://localhost:5000/")  # Adjust port if needed

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_main_elements_present(self):
        driver = self.driver
        # Check header title
        header = driver.find_element(By.CSS_SELECTOR, "header h1")
        self.assertEqual(header.text, "WhiteLabelRAG")

        # Check navigation links
        nav_links = driver.find_elements(By.CSS_SELECTOR, "nav ul.nav li.nav-item a.nav-link")
        nav_texts = [link.text for link in nav_links]
        self.assertIn("Home", nav_texts)
        self.assertIn("Chat", nav_texts)
        self.assertIn("Assistants", nav_texts)

        # Check main content title
        main_title = driver.find_element(By.CSS_SELECTOR, "main h2.card-title")
        self.assertEqual(main_title.text, "Main Content")

        # Check sidebar status badges
        badges = driver.find_elements(By.CSS_SELECTOR, "ul.list-group li.list-group-item span.badge")
        badge_texts = [badge.text for badge in badges]
        self.assertIn("Stable", badge_texts)
        self.assertIn("Online", badge_texts)
        self.assertIn("Ready", badge_texts)

    def test_responsive_layout(self):
        driver = self.driver
        # Set window size to mobile width and check if nav is hidden (d-none d-md-block)
        driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        nav = driver.find_element(By.CSS_SELECTOR, "nav")
        self.assertTrue("d-none" in nav.get_attribute("class"))

        # Set window size to desktop width and check if nav is visible
        driver.set_window_size(1024, 768)
        nav = driver.find_element(By.CSS_SELECTOR, "nav")
        self.assertFalse("d-none" in nav.get_attribute("class"))

if __name__ == "__main__":
    unittest.main()
