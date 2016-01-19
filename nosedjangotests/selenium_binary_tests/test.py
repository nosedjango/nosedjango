from django.test import TransactionTestCase

class SeleniumTestCase(TransactionTestCase):
    def test_simple(self):
        driver = self.driver
        self.assertEqual(driver.binary._start_cmd, '/Applications/FirefoxDeveloperEdition.app/Contents/MacOS/firefox')
