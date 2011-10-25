from django.test import TransactionTestCase

class SeleniumTestCase(TransactionTestCase):

    def test_simple(self):
        driver = self.driver
        driver.get('http://www.google.com')
        self.assertEqual(driver.title, 'Google')
