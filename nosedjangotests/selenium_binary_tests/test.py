from django.test import TransactionTestCase
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import os


class SeleniumTestCase(TransactionTestCase):
    def test_simple(self):
        driver = self.driver

        self.assertIn(driver.binary._start_cmd, 'ff-link')
