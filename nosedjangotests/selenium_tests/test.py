from django.test import TransactionTestCase

class SeleniumTestCase(TransactionTestCase):

    def test_simple(self):
        driver = self.driver
        driver.get('http://localhost:8000')
        self.assertEqual(driver.title, 'Welcome to Django')
