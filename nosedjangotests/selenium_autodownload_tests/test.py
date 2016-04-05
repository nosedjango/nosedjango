from django.test import TransactionTestCase

import tempfile


class SeleniumTestCase(TransactionTestCase):

    def test_simple(self):
        driver = self.driver
        driver.get('http://www.google.com')
        firefox_profile = self.driver.firefox_profile
        self.assertEqual(
            firefox_profile.default_preference['browser.download.dir'],
            tempfile.gettmpdir()
        )


