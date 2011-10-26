from django.test import TransactionTestCase

class SeleniumTestCase(TransactionTestCase):

    def test_simple(self):
        driver = self.driver
        driver.get('http://www.google.com')
        self.assertEqual(driver.title, 'Google')

    def test_simple_with_ctrl_c(self):
        driver = self.driver
        driver.get('http://www.google.com')
        #raise KeyboardInterrupt('test')
